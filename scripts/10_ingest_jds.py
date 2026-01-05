
from __future__ import annotations
import os
import json
import time
import argparse
import dataclasses
from pathlib import Path
from typing import List, Dict, Set, Optional, Callable, TypeVar, Any, Protocol
from playwright.sync_api import sync_playwright, Page, Browser, Playwright

# --- Types & Protocols ---
T = TypeVar("T")
PathLike = str | Path

class JobData(Protocol):
    url: str
    raw_text: str

class ContentExtractor(Protocol):
    def extract(self, page: Page) -> Optional[Dict[str, str]]: ...

# --- Configuration & State ---
@dataclasses.dataclass(frozen=True)
class Config:
    data_dir: Path
    auth_file: Path
    db_file: Path
    state_file: Path
    
    @classmethod
    def from_env(cls) -> Config:
        root = Path(os.getenv('DATA_DIR', Path(__file__).parent.parent/'data'))
        return cls(
            data_dir=root,
            auth_file=root.parent/"data"/".linkedin_auth.json",
            db_file=root/"demand"/"1_jd_database.json",
            state_file=root.parent/"data"/".scraper_state.json"
        )

@dataclasses.dataclass
class ScraperState:
    last_offset: int = 0
    processed_urls: Set[str] = dataclasses.field(default_factory=set)
    poison_urls: Set[str] = dataclasses.field(default_factory=set)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({
            'last_offset': self.last_offset,
            'processed_urls': list(self.processed_urls),
            'poison_urls': list(self.poison_urls)
        }, indent=2))

    @classmethod
    def load(cls, path: Path) -> ScraperState:
        if not path.exists(): return cls()
        try:
            d = json.loads(path.read_text())
            return cls(d.get('last_offset',0), set(d.get('processed_urls',[])), set(d.get('poison_urls',[])))
        except: return cls()

# --- Core Logic ---
class BrowserSession:
    def __init__(self, auth_path: Path):
        self._auth = auth_path
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def __enter__(self) -> BrowserSession:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=False)
        context = self._browser.new_context(storage_state=str(self._auth))
        self.page = context.new_page()
        self.page.set_default_timeout(30000)

    def close(self) -> None:
        if self._browser: self._browser.close()
        if self._playwright: self._playwright.stop()

    def restart(self) -> None:
        print("     ♻️  Restarting Browser...")
        self.close()
        time.sleep(2)
        self.start()

    def goto(self, url: str, retries: int = 3) -> bool:
        if not self.page: return False
        for i in range(retries):
            try:
                self.page.goto(url, wait_until='domcontentloaded')
                return True
            except:
                if i == retries - 1: return False
                self.restart()
        return False

class LinkedInExtractor:
    EXPANDERS = [
        'button.jobs-description__footer-button', 
        '.show-more-less-html__button', 
        '[aria-label*="Show more"]'
    ]

    def extract(self, page: Page) -> Optional[Dict[str, str]]:
        self._expand_description(page)
        return self._scrape_dom(page)

    def _expand_description(self, page: Page) -> None:
        for sel in self.EXPANDERS:
            try:
                if page.is_visible(sel): 
                    page.click(sel, timeout=500)
                    time.sleep(0.2)
            except: pass
        try: 
            page.wait_for_selector('#job-details, .jobs-description__content', timeout=3000)
        except: pass

    def _scrape_dom(self, page: Page) -> Dict[str, str]:
        return page.evaluate("""() => {
            const get = (s) => document.querySelector(s)?.innerText?.trim();
            const container = document.querySelector('.jobs-description__content') || document.querySelector('#job-details');
            return {
                title: get('h1') || get('.job-details-jobs-unified-top-card__job-title') || "Unknown",
                company: get('.job-details-jobs-unified-top-card__company-name a') || get('.job-details-jobs-unified-top-card__company-name') || "Unknown",
                text: container?.innerText || ""
            };
        }""")

class JobProcessor:
    def __init__(self, config: Config, session: BrowserSession):
        self.cfg = config
        self.session = session
        self.extractor = LinkedInExtractor()
        self.db: List[Dict] = self._load_db()

    def _load_db(self) -> List[Dict]:
        return json.loads(self.cfg.db_file.read_text()).get('roles', []) if self.cfg.db_file.exists() else []

    def _save_db(self) -> None:
        with open(self.cfg.db_file, 'w') as f: json.dump({"roles": self.db}, f, indent=2)

    def _upsert(self, data: Dict[str, str], url: str) -> None:
        item = {
            "id": f"SAVED-{len(self.db)+1}",
            "title": data['title'], "company": data['company'], "url": url,
            "type": "linkedin_saved", "source_file": "Direct_Saved_Jobs_Scrape",
            "status": "active", "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_text": data['text'], 
            "sections": self._parse_sections(data['text'])
        }
        idx = next((i for i, x in enumerate(self.db) if x.get('url') == url), -1)
        if idx >= 0: 
            item['id'] = self.db[idx].get('id', item['id'])
            self.db[idx] = item
        else: 
            self.db.append(item)
        self._save_db()

    def _parse_sections(self, text: str) -> Dict[str, List[str]]:
        sections, current = {}, "Summary"
        for line in text.split('\n'):
            if not line.strip(): continue
            lower = line.lower()
            if len(line) < 50:
                if any(x in lower for x in ['responsibilities', 'duties']): current = 'Responsibilities'
                elif any(x in lower for x in ['requirements', 'skills']): current = 'Requirements'
                elif any(x in lower for x in ['benefits', 'perks']): current = 'Benefits'
            sections.setdefault(current, []).append(line.strip())
        return sections

    def process_url(self, url: str, state: Optional[ScraperState] = None, force: bool = False) -> None:
        if state and not force:
            if url in state.processed_urls or url in state.poison_urls: return

        print(f"   ☁️  {url}")
        if not self.session.goto(url):
            print("     ❌ Failed to load.")
            if state: 
                state.poison_urls.add(url)
                state.save(self.cfg.state_file)
            return

        data = self.extractor.extract(self.session.page)
        if not data or not data.get('text'):
            print("     ⚠️  Empty content.")
            return

        print(f"     ✅ Saved ({len(data['text'])} chars).")
        if len(data['text']) < 200: print(f"     ⚠️  Stub detected.")
        
        self._upsert(data, url)
        
        if state:
            state.processed_urls.add(url)
            state.save(self.cfg.state_file)

# --- Workflows ---
def run_retry_stubs(proc: JobProcessor) -> None:
    stubs = [j for j in proc.db if j.get('source_file') == "Direct_Saved_Jobs_Scrape" and len(j.get('raw_text', '')) < 500]
    print(f"🚀 Retrying {len(stubs)} identified stubs...")
    for job in stubs:
        proc.process_url(job['url'], force=True)

def run_scraper(proc: JobProcessor, start_offset: int = 0) -> None:
    state = ScraperState.load(proc.cfg.state_file)
    offset = start_offset if start_offset > 0 else state.last_offset
    
    print(f"🚀 Scraping Saved Jobs starting at offset {offset}...")
    for off in range(offset, 200, 10):
        print(f"📖 Text: processing page offset {off}")
        state.last_offset = off
        state.save(proc.cfg.state_file)
        
        if not proc.session.goto(f"https://www.linkedin.com/my-items/saved-jobs/?start={off}"): continue
        
        try: proc.session.page.wait_for_selector(".reusable-search__result-container", timeout=4000)
        except: time.sleep(1)
        
        urls = proc.session.page.evaluate("""
            Array.from(document.querySelectorAll('a'))
                 .map(a => a.href.split('?')[0])
                 .filter(h => h.includes('/jobs/view/'))
        """)
        
        for url in set(urls):
            proc.process_url(url, state)

def login_flow(cfg: Config) -> None:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)
        page = b.new_context().new_page()
        page.goto("https://www.linkedin.com/login")
        input("👉 Log in and press Enter...")
        b.contexts[0].storage_state(path=cfg.auth_file)
        print(f"✅ Session saved to {cfg.auth_file}")

# --- Entry Point ---
def main():
    parser = argparse.ArgumentParser(description="Robust LinkedIn Job Scraper")
    parser.add_argument("--scrape-saved", action="store_true", help="Scrape 'Saved Jobs' list")
    parser.add_argument("--retry-stubs", action="store_true", help="Refetch partial jobs")
    parser.add_argument("--resume-from", type=int, default=0, help="Start offset")
    parser.add_argument("--url", help="Scrape single URL")
    parser.add_argument("--login", action="store_true", help="Update auth session")
    args = parser.parse_args()

    cfg = Config.from_env()

    if args.login:
        login_flow(cfg)
        return

    print(f"  � Database size: {len(json.loads(cfg.db_file.read_text()).get('roles', [])) if cfg.db_file.exists() else 0}")
    
    # Context Manager for automatic resource cleanup
    try:
        with BrowserSession(cfg.auth_file) as session:
            proc = JobProcessor(config=cfg, session=session)
            
            if args.url:
                proc.process_url(args.url, force=True)
            elif args.retry_stubs:
                run_retry_stubs(proc)
            elif args.scrape_saved:
                run_scraper(proc, args.resume_from)
            else:
                parser.print_help()
                
    except KeyboardInterrupt:
        print("\n🛑 Execution interrupted by user.")
    except Exception as e:
        print(f"\n💥 Fatal Error: {e}")

if __name__ == "__main__":
    main()
