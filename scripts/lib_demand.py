"""Library for demand discovery: URL fetching and batch processing."""
import os, time, random, re, csv
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from scripts.lib_extract import extract

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0'
]

def fetch_url(url):
    """Robust URL fetcher using Playwright to handle dynamic JS sites (LinkedIn)."""
    if not url or not url.startswith('http'): return None
    
    from playwright.sync_api import sync_playwright
    
    # Fixed User-Agent to match typical browser behavior (avoid HeadlessChrome)
    FIXED_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    for i in range(2): # 2 retries
        try:
            with sync_playwright() as p:
                # Stealth: Disable automation flags
                browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
                
                # Auth State
                state_path = os.path.expanduser("~/.gemini/antigravity/scratch/resume-optimization-system/data/linkedin_state.json")
                use_state = state_path if os.path.exists(state_path) else None
                
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent=FIXED_UA,
                    storage_state=use_state
                )
                
                # Stealth: Mask webdriver property
                page = context.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Navigate
                # Warmup: Visit homepage first to validate session if reusing state
                if use_state and 'linkedin.com' in url:
                    try:
                        page.goto("https://www.linkedin.com/feed/", timeout=15000)
                        time.sleep(2)
                    except: pass

                page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                # LinkedIn Specific Handling
                if 'linkedin.com' in url:
                    time.sleep(3) # Wait for potential redirects/lazyload
                    
                    # Check for Expiration/Redirect
                    if 'expired_jd_redirect' in page.url or 'jobs/search' in page.url:
                        print(f"    ⚠️  Job Expired: {url}")
                        browser.close()
                        return {'content': None, 'status': 'expired', 'note': 'Redirected to search/expired page'}

                    try:
                        # Scroll to trigger lazy loading
                        page.keyboard.press("End")
                        time.sleep(1)
                        page.keyboard.press("Home")
                        time.sleep(1)
                        
                        # Try to expand "See more"
                        selectors = [
                            "button.jobs-description__footer-button",
                            "button[aria-label='Click to see more description']",
                            ".show-more-less-html__button"
                        ]
                        for s in selectors:
                            if page.is_visible(s):
                                page.click(s)
                                time.sleep(0.5)
                                break
                    except Exception as e:
                        print(f"    (Non-fatal interaction error: {e})")
                
                content = page.content()
                browser.close()
                return {'content': content, 'status': 'success', 'note': 'Fetched via Playwright'}

        except Exception as e:
            print(f"  ⚠️ Playwright error {url}: {e}")
            time.sleep(2)
            
    return {'content': None, 'status': 'failed', 'note': f'Max retries exceeded'}

def parse_html(html):
    """Extract readable text from HTML."""
    if not html: return ""
    soup = BeautifulSoup(html, 'html.parser')
    # Remove script and style elements
    for s in soup(["script", "style", "nav", "footer", "header"]): s.decompose()
    return soup.get_text(separator='\n').strip()

def parse_jd_text(txt):
    """Heuristic section splitter."""
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    if not lines: return {}
    cur = 'Summary'
    secs = {'Responsibilities': [], 'Requirements': [], 'Summary': []}
    for l in lines:
        if re.search(r'(?i)(responsibilit|duties|what you will do)', l): cur = 'Responsibilities'
        elif re.search(r'(?i)(requirement|qualification|skills|who you are)', l): cur = 'Requirements'
        else: secs[cur].append(l)
    return secs

def process_batch_file(fp: Path):
    """Process a batch file (CSV/XLSX) and return list of potential JDs."""
    if not fp.exists(): return []
    
    rows = []
    try:
        if fp.suffix == '.csv':
            import csv
            with open(fp, encoding='utf-8', errors='ignore') as f:
                rows = list(csv.DictReader(f))
        elif fp.suffix == '.xlsx':
            import openpyxl
            wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
            ws = wb.active
            
            # Smart Header Detection (Scans first 5 rows)
            headers = None
            data_rows = []
            for r_idx, r in enumerate(ws.iter_rows(values_only=True)):
                # Heuristic: Valid header has >2 strings and 'company' or 'employer' or 'title' or 'position'
                row_vals = [str(x).strip() for x in r if x]
                row_str = " ".join(row_vals).lower()
                
                if not headers:
                    if len(row_vals) >= 2 and any(k in row_str for k in ['company','employer','title','position','url','link']):
                        headers = [str(c).strip() if c else f"col_{i}" for i,c in enumerate(r)]
                        continue
                if headers:
                    # Zip headers with values
                    row_dict = {h: (r[i] if i < len(r) else None) for i, h in enumerate(headers)}
                    rows.append(row_dict)
                    
    except Exception as e:
        print(f"  ❌ Error reading batch {fp.name}: {e}")
        return []

    # 2. Identify Mode (Links vs Description)
    results = []
    for r in rows:
        # Normalize keys
        r = {k.lower().strip(): v for k, v in r.items() if k}
        
        # Look for URL
        url = next((v for k, v in r.items() if any(x in k for x in ['url','link']) and v and str(v).startswith('http')), None)
        # Look for Company/Title (Extended Mappings) - ignore None values
        company = next((v for k, v in r.items() if any(x in k for x in ['company','employer']) and v), "Unknown")
        title = next((v for k, v in r.items() if any(x in k for x in ['title','position','role']) and v), "Role")
        
        # Cleanup values
        if isinstance(title, str): title = title.strip()
        if isinstance(company, str): company = company.strip()
        
        # Skip empty rows commonly found in excel
        if company == "Unknown" and title == "Role" and not url: continue

        entry = {
            "id": f"BATCH-{fp.name}-{len(results)}",
            "title": title,
            "company": company,
            "url": url,
            "source": fp.name,
            "type": "batch_link" if url else "batch_desc"
        }
        results.append(entry)
        
    return results
