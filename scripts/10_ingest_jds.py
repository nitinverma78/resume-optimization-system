
import os
import sys
import re
import json
import time
import argparse
import requests
from pathlib import Path
import dataclasses
from playwright.sync_api import sync_playwright

def get_data_dir(): 
    return Path(os.getenv('DATA_DIR')) if os.getenv('DATA_DIR') else Path(__file__).parent.parent/"data"

@dataclasses.dataclass
class ScraperState:
    last_offset: int = 0
    processed_urls: set = dataclasses.field(default_factory=set)
    poison_urls: set = dataclasses.field(default_factory=set)
    
    @classmethod
    def load(cls, path: Path):
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return cls(
                    last_offset=data.get('last_offset', 0),
                    processed_urls=set(data.get('processed_urls', [])),
                    poison_urls=set(data.get('poison_urls', []))
                )
            except:
                pass
        return cls()

    def save(self, path: Path):
        path.write_text(json.dumps({
            'last_offset': self.last_offset,
            'processed_urls': list(self.processed_urls),
            'poison_urls': list(self.poison_urls)
        }, indent=2))

class ScraperSession:
    def __init__(self, auth_file: Path):
        self.auth_file = auth_file
        self.p = None
        self.browser = None
        self.context = None
        self.page = None
        
    def start(self):
        from playwright.sync_api import sync_playwright
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=False)
        self.context = self.browser.new_context(storage_state=str(self.auth_file))
        self.page = self.context.new_page()
        # Set default timeout to avoid infinite hangs
        self.page.set_default_timeout(30000)
        
    def restart(self):
        print("     ♻️  Restarting Browser Session...")
        try: self.browser.close()
        except: pass
        try: self.p.stop()
        except: pass
        time.sleep(2)
        self.start()
        
    def safe_goto(self, url, retries=3):
        for i in range(retries):
            try:
                self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
                return True
            except Exception as e:
                print(f"     ⚠️  Goto failed ({i+1}/{retries}): {e}")
                if i == retries - 1: return False
                self.restart() # Active recovery
                
    def close(self):
        if self.browser: self.browser.close()
        if self.p: self.p.stop()

def extract_job_content(session, url):
    """Robust content extraction logic shared by regular and retry modes."""
    try:
        # Robust "See More" - Try multiple strategies
        clicked_more = False
        for sel in [
            'button.jobs-description__footer-button', 
            '.show-more-less-html__button',
            '[aria-label="Click to see more description"]',
            'button[class*="show-more"]',
            '[aria-label="Show more, visually expands previously read content above"]'
        ]:
            try: 
                if session.page.is_visible(sel):
                    session.page.click(sel, timeout=1000)
                    clicked_more = True
                    time.sleep(0.5)
            except: pass
        
        # Wait for meaningful content
        try:
            session.page.wait_for_selector('#job-details, .jobs-description__content', state='visible', timeout=5000)
        except: pass
        
        # Extract Data with Fallbacks
        job_data = session.page.evaluate("""() => {
            const title = document.querySelector('h1')?.innerText?.trim() 
                       || document.querySelector('.job-details-jobs-unified-top-card__job-title')?.innerText?.trim() 
                       || "Unknown";
                       
            const company = document.querySelector('.job-details-jobs-unified-top-card__company-name a')?.innerText?.trim() 
                          || document.querySelector('.job-details-jobs-unified-top-card__company-name')?.innerText?.trim() 
                          || "Unknown";
                          
            // Try multiple containers for the description
            const descContainer = document.querySelector('.jobs-description__content') 
                                || document.querySelector('#job-details') 
                                || document.querySelector('.jobs-box__html-content');
                                
            const text = descContainer?.innerText || "";
            const html = descContainer?.innerHTML || "";
            
            // Check if text is hidden or behind a "Show more" that we missed?
            
            return {title, company, text, html};
        }""")
        
        return job_data
    except Exception as e:
        print(f"     ❌ Extraction error: {e}")
        return None

def parse_html(html_content):
    """Strip HTML to raw text (simple version)."""
    clean = re.sub('<[^<]+?>', '', html_content)
    return clean.strip()

def parse_jd_text(text):
    """Heuristic section parsing."""
    sections = {}
    current_section = "Summary"
    lines = text.split('\n')
    sections[current_section] = []
    
    # Common headers
    headers = {
        'Responsibilities': ['responsibilities', 'what you will do', 'duties', 'role'],
        'Requirements': ['requirements', 'qualifications', 'what you bring', 'skills', 'experience'],
        'Benefits': ['benefits', 'perks', 'compensation', 'offer']
    }
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check if line is a header
        is_header = False
        lower = line.lower()
        for head, keywords in headers.items():
            if any(k in lower for k in keywords) and len(line) < 50:
                current_section = head
                sections[current_section] = []
                is_header = True
                break
        
        if not is_header:
            sections.setdefault(current_section, []).append(line)
            
    return sections

def fetch_url(url):
    """Fetch URL content using requests as a simple fallback or helper."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        return {
            'content': resp.text,
            'status': 'active' if resp.status_code == 200 else 'failed',
            'note': f"HTTP {resp.status_code}"
        }
    except Exception as e:
        return {'content': None, 'status': 'failed', 'note': str(e)}

def scrape_saved_jobs_direct(db, out_path, start_offset=0, retry_stubs=False):
    """Directly scrape saved jobs with robust state management and self-healing."""
    
    auth_file = get_data_dir().parent / "data" / ".linkedin_auth.json"
    if not auth_file.exists():
        print("❌ No auth file found! Run scripts/setup_linkedin_auth.py first.")
        return

    state_file = get_data_dir().parent / "data" / ".scraper_state.json"
    state = ScraperState.load(state_file)
    
    session = ScraperSession(auth_file)
    session.start()
    
    # RETRY STUBS MODE
    if retry_stubs:
        print(f"🚀 Starting Stub Retry Mode (Refetching jobs with <500 chars)...")
        # Identify stubs: jobs from scraping that have short text
        targets = [j for j in db if j.get('source_file') == "Direct_Saved_Jobs_Scrape" and len(j.get('raw_text', '')) < 500]
        print(f"   🎯 Found {len(targets)} stubs to retry.")
        
        count = 0
        for job in targets:
            url = job.get('url')
            if not url: continue
            
            print(f"   ☁️  Refetching Stub: {job.get('title')} ({url})")
            if not session.safe_goto(url):
                print(f"     ❌ Failed to load. Skipping.")
                continue
                
            job_data = extract_job_content(session, url)
            
            if job_data and len(job_data['text']) > len(job.get('raw_text', '')):
                 print(f"     ✅ Improved content! ({len(job_data['text'])} chars vs {len(job.get('raw_text', ''))})")
                 job['raw_text'] = job_data['text']
                 job['sections'] = parse_jd_text(job_data['text'])
                 job['fetched_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
                 
                 # Save continuously
                 with open(out_path, 'w') as f: json.dump({"roles": db}, f, indent=2)
                 count += 1
            else:
                 print(f"     ⚠️  No improvement ({len(job_data['text']) if job_data else 0} chars).")
        
        print(f"✅ Stub retry complete. Improved {count} jobs.")
        session.close()
        return

    # NORMAL MODE
    current_offset = start_offset if start_offset > 0 else state.last_offset
    print(f"🚀 Starting Robust Scraper (Resume: {current_offset})")
    
    try:
        # Loop through pages (up to 200 jobs)
        for offset in range(current_offset, 200, 10):
            print(f"📖 Text: processing page offset {offset}")
            state.last_offset = offset
            state.save(state_file)
            
            list_url = f"https://www.linkedin.com/my-items/saved-jobs/?start={offset}"
            
            if not session.safe_goto(list_url):
                print(f"❌ Failed to load list page {offset}. skipping...")
                continue
                
            try: session.page.wait_for_selector(".reusable-search__result-container", timeout=5000)
            except: time.sleep(2)
            
            links = session.page.evaluate("""
                Array.from(document.querySelectorAll('a'))
                     .map(a => a.href.split('?')[0])
                     .filter(h => h.includes('/jobs/view/'))
            """)
            unique_links = list(set(links))
            print(f"   🔍 Found {len(unique_links)} jobs.")
            
            for job_url in unique_links:
                if job_url in state.processed_urls: continue
                if job_url in state.poison_urls: 
                    print(f"   ☠️  Skipping Poison URL: {job_url}"); continue
                
                print(f"   ☁️  Fetching: {job_url}")
                if not session.safe_goto(job_url):
                    print("     ❌ Failed to load job page. Marking poison.")
                    state.poison_urls.add(job_url)
                    state.save(state_file)
                    continue

                job_data = extract_job_content(session, job_url)

                if not job_data or not job_data['text']:
                    print("     ⚠️  Empty text. Skipping.")
                    continue
                
                if len(job_data['text']) < 200:
                    print(f"     ⚠️  Text too short ({len(job_data['text'])} chars). Possible stub.")
                        
                item = {
                    "id": f"SAVED-{len(db) + 1}",
                    "title": job_data['title'],
                    "company": job_data['company'],
                    "url": job_url,
                    "type": "linkedin_saved",
                    "source_file": "Direct_Saved_Jobs_Scrape",
                    "status": "active",
                    "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "raw_text": job_data['text'],
                    "sections": parse_jd_text(job_data['text'])
                }
                
                # Update/Upsert
                existing_idx = next((i for i, d in enumerate(db) if d.get('url') == job_url), -1)
                if existing_idx >= 0:
                    item['id'] = db[existing_idx]['id']
                    db[existing_idx] = item
                else:
                    db.append(item)
                    
                with open(out_path, 'w') as f: json.dump({"roles": db}, f, indent=2)
                state.processed_urls.add(job_url)
                state.save(state_file)
                print("     ✅ Saved.")
            
    except KeyboardInterrupt:
        print("\n🛑 Scraper stopped by user. State saved.")
    except Exception as e:
        print(f"\n💥 Critical Scraper Error: {e}")
    finally:
        session.close()
        state.save(state_file)
        print("💾 Final state saved.")

def ingest_item(source, name, url=None, content=None, type="file"):
    """Ingest a single JD item, handling both file content and URLs."""
    status = "active"
    note = "Ingested from file"
    
    if url: 
        print(f"  ☁️  Fetching: {url}")
        res = fetch_url(url)
        content = res['content']
        status = res['status']
        note = res['note']
    
    # Even if content is empty (expired/failed), we verify/save the entry
    if not content: content = ""

    # Basic Extraction
    sections = {}
    if content:
        raw_text = parse_html(content)
        sections = parse_jd_text(raw_text)
    else:
        raw_text = ""

    return {
        "id": f"{type.upper()}-{re.sub(r'[^a-zA-Z0-9]', '_', name)}",
        "title": name,
        "company": "Unknown", 
        "url": url,
        "type": type,
        "source_file": source,
        "status": status,
        "processing_note": note,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "raw_text": raw_text,
        "sections": sections
    }

def main():
    parser = argparse.ArgumentParser(description="Ingest JDs from various sources.")
    parser.add_argument("--url", help="Ingest a single ad-hoc URL")
    parser.add_argument("--scope", choices=['small', 'medium', 'large'], default='large', help="Ingestion scope: small (fast), medium, or large (all)")
    parser.add_argument("--login", action="store_true", help="Launch browser to login and save session state")
    parser.add_argument("--scrape-saved", action="store_true", help="Directly scrape saved jobs from LinkedIn profile")
    parser.add_argument("--resume-from", type=int, default=0, help="Resume direct scraping from this offset")
    parser.add_argument("--retry-stubs", action="store_true", help="Retry scraping for potential stubs (<500 chars)")
    parser.add_argument("--force", action="store_true", help="Force re-ingest existing URLs")
    args = parser.parse_args()

    # Login Flow
    if args.login:
        print("🔐 Launching browser for Login...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.linkedin.com/login")
            print("👉 Please log in to LinkedIn in the browser window.")
            print("👉 Once you see your Feed, press Enter here.")
            input()
            
            # Save State
            state_path = get_data_dir().parent / "data" / ".linkedin_auth.json"
            context.storage_state(path=state_path)
            print(f"✅ Session saved to {state_path}")
            browser.close()
        return

    dd = get_data_dir()
    out = dd/"demand"/"1_jd_database.json"
    
    # Load Existing DB
    db = []
    if out.exists():
        try:
             db = json.loads(out.read_text()).get('roles', [])
             print(f"  📚 Loaded {len(db)} existing JDs from database.")
        except:
             print("  ⚠️  Could not load existing database. Starting fresh.")

    # DIRECT SCRAPE MODE
    if args.scrape_saved:
        scrape_saved_jobs_direct(db, out, start_offset=args.resume_from, retry_stubs=args.retry_stubs)
        return
    
    print("ℹ️  No scrape mode selected. Use --scrape-saved to scrape LinkedIn Saved Jobs.")

if __name__ == "__main__":
    main()
