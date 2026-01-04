#!/usr/bin/env python3
"""[Demand Discovery] Step 10: Ingest JDs from Files, Links, and Batches."""
import os
import json
import sys
import argparse
import requests
import re
import time
from pathlib import Path
from scripts.lib_extract import extract
from scripts.lib_demand import fetch_url, parse_html, parse_jd_text, process_batch_file

def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")

# Manual .env loading
env_path = Path(__file__).parent.parent / ".env"
_env_loaded = False
if env_path.exists():
    for l in env_path.read_text().splitlines():
        if '=' in l and not l.strip().startswith('#'):
            k, v = l.strip().split('=', 1)
            # Only set if not already set (respect existing env)
            if not os.getenv(k): os.environ[k] = v.strip('"').strip("'"); _env_loaded = True

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
    if not content: 
        # Only skip if it's a "failed" fetch (network error) AND we want to retry later? 
        # Actually user wants to SEE expired jobs. So we save them.
        pass

    # Basic Extraction (only if content exists)
    sections = {}
    if content:
        raw_text = parse_html(content)
        sections = parse_jd_text(raw_text)
    else:
        raw_text = ""

    return {
        "id": f"{type.upper()}-{re.sub(r'[^a-zA-Z0-9]', '_', name)}",
        "title": name,
        "company": "Unknown", # Todo: extract from text
        "url": url,
        "type": type,
        "source_file": source,
        "status": status,          # New Field
        "processing_note": note,   # New Field
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), # New Field
        "raw_text": raw_text,
        "sections": sections
    }

def main():
    parser = argparse.ArgumentParser(description="Ingest JDs from various sources.")
    parser.add_argument("--url", help="Ingest a single ad-hoc URL")
    parser.add_argument("--scope", choices=['small', 'medium', 'large'], default='large', help="Ingestion scope: small (fast), medium, or large (all)")
    parser.add_argument("--login", action="store_true", help="Launch browser to login and save session state")
    parser.add_argument("--force", action="store_true", help="Force re-ingest existing URLs")
    args = parser.parse_args()

    # Login Flow
    if args.login:
        print("🔐 Launching browser for Login...")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.linkedin.com/login")
            print("👉 Please log in to LinkedIn in the browser window.")
            print("👉 Once you see your Feed, press Enter here.")
            input()
            
            # Save State
            state_path = get_data_dir()/"linkedin_state.json"
            context.storage_state(path=state_path)
            print(f"✅ Session saved to {state_path}")
            browser.close()
        return

    # Setup
    r_folder = os.getenv('RESUME_FOLDER')
    if not r_folder: print("Error: RESUME_FOLDER not set."); return
    
    dd = get_data_dir()
    inv_p = dd/"supply"/"2_file_inventory.json"
    out = dd/"demand"/"1_jd_database.json"

    raw_dir = dd/"demand"/"raw_jds"
    
    # Load Existing DB (Incremental)
    db = []
    if out.exists():
        try:
            db = json.loads(out.read_text()).get('roles', [])
            print(f"  📚 Loaded {len(db)} existing JDs from database.")
        except:
            print("  ⚠️  Could not load existing database. Starting fresh.")
    
    existing_urls = {i.get('url') for i in db if i.get('url')}

    print("🚀 Ingesting JDs...")
    raw_dir.mkdir(parents=True, exist_ok=True) # Ensure raw drop zone exists

    # Define Scopes (Hoist to top)
    scope_small = ['Job Applications.csv', 'Work Search Logs copy.xlsx']
    scope_medium = scope_small + ['Saved Jobs.csv']
    
    # Calculate Expected Batches
    expected_batches = []
    if inv_p.exists():
        inv_data = json.loads(inv_p.read_text())
        for f in inv_data.get('jds', []):
            fname = Path(f['path']).name
            if Path(f['path']).suffix.lower() in ['.csv', '.xlsx']:
                if args.scope == 'small' and not any(s in fname for s in scope_small): continue
                if args.scope == 'medium' and not any(s in fname for s in scope_medium): continue
                expected_batches.append(fname)

    # Helper Functions (Scoped to Main)
    def save_summary(batch_name="N/A", status_label="RUNNING", start_time=None, batch_total=0, batch_processed=0, expected_batches=[]):
        processed = len(db)
        # ... (rest of save_summary logic is fine, no changes needed inside)
        
        # Calculate Progress Stats
        progress_bar = ""
        eta_str = "Calculating..."
        pct_str = "0%"
        
        if status_label == "RUNNING" and start_time and batch_total > 0:
             elapsed = time.time() - start_time
             if batch_processed > 0:
                 rate = batch_processed / elapsed # items per second
                 remaining = batch_total - batch_processed
                 eta_seconds = remaining / rate if rate > 0 else 0
                 eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                 
                 pct = (batch_processed / batch_total)
                 pct_str = f"{int(pct * 100)}%"
                 bar_len = 20
                 filled = int(bar_len * pct)
                 progress_bar = "▓" * filled + "░" * (bar_len - filled)

        # Aggregate by Batch
        batches = {}
        for item in db:
            src = item.get('source_file', 'unknown')
            if src not in batches:
                batches[src] = {'total': 0, 'active': 0, 'expired': 0, 'failed': 0}
            
            batches[src]['total'] += 1
            st = item.get('status')
            if st == 'expired': batches[src]['expired'] += 1
            elif st == 'failed': batches[src]['failed'] += 1
            elif st in ['success', 'active']: batches[src]['active'] += 1
            else: pass # Unknown status

        summary_path = dd / "demand" / "ingestion_summary.md"
        with open(summary_path, 'w') as f:
            f.write(f"# 📊 Ingestion Status Report\n")
            f.write(f"**Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Status**: `{status_label}`\n\n")
            
            if status_label == "RUNNING" and progress_bar:
                f.write(f"## ⏳ Current Batch Progress\n")
                f.write(f"**Batch**: `{batch_name}`\n")
                f.write(f"**Progress**: `{progress_bar}` {pct_str} ({batch_processed}/{batch_total})\n")
                f.write(f"**ETA**: {eta_str}\n\n")

            f.write(f"## 📦 Batch Breakdown\n")
            f.write(f"| Status | Batch Name | Total | 🟢 Active | 🔴 Expired | ⚠️ Failed |\n")
            f.write(f"|---|---|---|---|---|---|\n")
            
            # Combine expected and actual for display
            all_batch_names = sorted(list(set(expected_batches + list(batches.keys()))))
            
            total_active = 0
            total_expired = 0
            total_failed = 0
            
            for name in all_batch_names:
                stats = batches.get(name, {'total': 0, 'active': 0, 'expired': 0, 'failed': 0})
                
                # Determine Symbol
                symbol = "⏳" # Pending/Unknown
                if name in batches: symbol = "✅" # Processed or Processing
                if name == batch_name and status_label == "RUNNING": symbol = "🔄" # Currently Processing
                
                # Special case: unknown/classified aren't in expected list, just mark as done if present
                if name not in expected_batches and name in batches: symbol = "✅"

                # Colorize Counts (Text-Friendly Emojis)
                if name not in batches:
                    c_total = "-"
                    c_active = "-"
                    c_expired = "-"
                    c_failed = "-"
                else:
                    c_total = f"{stats['total']} 🔵"
                    c_active = f"{stats['active']} 🟢" if stats['active'] > 0 else f"{stats['active']}"
                    c_expired = f"{stats['expired']} 🔴" if stats['expired'] > 0 else f"{stats['expired']}"
                    c_failed = f"{stats['failed']} 🟠" if stats['failed'] > 0 else f"{stats['failed']}"

                f.write(f"| {symbol} | {name} | {c_total} | {c_active} | {c_expired} | {c_failed} |\n")
                total_active += stats['active']
                total_expired += stats['expired']
                total_failed += stats['failed']

            f.write(f"\n## 📈 Global Totals\n")
            f.write(f"- **Total Processed**: {processed}\n")
            f.write(f"- **Total Active**: {total_active}\n")
            f.write(f"- **Total Expired**: {total_expired}\n")
            
            if (dd/"demand"/"missing_jds.md").exists():
                 f.write(f"- ⚪️ **Missing (No URL)**: {(dd/'demand'/'missing_jds.md').read_text().count('- [ ]')}\n")

    def save_db(batch_name="N/A", start_time=None, batch_total=0, batch_processed=0):
        with open(out, 'w') as f: json.dump({"roles": db}, f, indent=2)
        save_summary(batch_name, "RUNNING", start_time, batch_total, batch_processed, expected_batches)

    # A. Ad-hoc Link
    if args.url:
        if jd := ingest_item("cli", "Ad-hoc URL", url=args.url, type="link"):
            db.append(jd)
            print(f"  ✅ Ingested URL: {args.url}")
            # Immediate Save
            with open(out, 'w') as f: json.dump({"roles": db}, f, indent=2)
        return

    # B. Classified Inventory (Files & Batches)
    if inv_p.exists():
        inv = json.loads(inv_p.read_text())
        # 1. Process Classified JDs (Files)
        for f in inv.get('jds', []):
            fp = Path(f['path'])
            if not fp.exists(): continue
            
            # Scope Filtering (Already handled via expected calculation, but needed for flow control)
            if fp.suffix.lower() in ['.csv', '.xlsx']:
                if fp.name not in expected_batches: continue
            
            # Check if this is actually a batch file (CSV/XLSX)
            if fp.suffix.lower() in ['.csv', '.xlsx']:
                print(f"  📦 Processing Batch: {fp.name}")
                items = process_batch_file(fp)
                
                # Separate links (parallel) and desc (serial)
                links = [i for i in items if i.get('url')]
                descs = [i for i in items if not i.get('url')]
                
                # Filter Links (Incremental Check)
                if not args.force:
                    original_len = len(links)
                    links = [i for i in links if i.get('url') not in existing_urls]
                    skipped = original_len - len(links)
                    if skipped > 0:
                        print(f"     ⏭️  Skipping {skipped} existing URLs (Use --force to re-ingest)")
                
                # Parallel Batch Link Processing
                if links:
                    print(f"     ⚡️ Fetching {len(links)} URLs in parallel...")
                    import concurrent.futures
                    start_time = time.time()
                    
                    # Reduced workers for Playwright stability
                    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                        # Submit all
                        futures = {executor.submit(ingest_item, fp.name, i['title'], url=i['url'], type="batch_link"): i for i in links}
                        
                        completed_count = 0
                        for future in concurrent.futures.as_completed(futures):
                            i = futures[future]
                            completed_count += 1
                            try:
                                if jd := future.result():
                                    jd['company'] = i['company']
                                    db.append(jd)
                                    # Incremental Save every 5 items
                                    if len(db) % 5 == 0:
                                        save_db(fp.name, start_time, len(links), completed_count)
                                        print(f"     💾 Saved {len(db)} items... ({completed_count}/{len(links)} fetched)")
                            except Exception as e:
                                print(f"     ❌ Failed {i['url']}: {e}")
                    
                    # Final save after batch
                    save_db(fp.name, start_time, len(links), len(links))

                # Serial Batch Desc Processing
                for item in descs:
                    print(f"  ⚠️  Search Required: {item['title']} at {item['company']} (No URL)")
                    db.append({
                        "id": item['id'],
                        "title": item['title'],
                        "company": item['company'],
                        "source": fp.name,
                        "type": "batch_desc_stub",
                        "raw_text": f"Job Title: {item['title']}\nCompany: {item['company']}", 
                        "sections": {} 
                    })
            # Mode A: Standard File
            elif txt := extract(fp):
                if jd := ingest_item("classified", f['name'], content=txt, type="file"):
                    db.append(jd)

    # C. Raw Drop Zone
    if raw_dir.exists():
        for fp in [x for x in raw_dir.glob("*.*") if not x.name.startswith('.')]:
             if txt := extract(fp):
                 if jd := ingest_item("manual", fp.name, content=txt, type="file"):
                     db.append(jd)

    # Generate Reports
    if db:
        out.parent.mkdir(parents=True, exist_ok=True)
        # Final Save with Completed Status
        with open(out, 'w') as f: json.dump({"roles": db}, f, indent=2)
        save_summary(batch_name="ALL_DONE", status_label="COMPLETED", expected_batches=expected_batches)
        print(f"✅ Ingested {len(db)} JDs to {out}")
    else:
        print("❌ No JDs found.")

    # Missing JDs Report
    missing_jds = [j for j in db if j.get('type') == 'batch_desc_stub']
    if missing_jds:
        m_out = dd/"demand"/"missing_jds.md"
        with open(m_out, 'w') as f:
            f.write("# 🕵️‍♀️ Missing JDs Report\n\n")
            f.write(f"Found **{len(missing_jds)}** items needing manual search.\n")
            f.write("Click the **[Search]** link, find the Job URL, and verify functionality.\n\n")
            f.write("| Company | Title | Source | Action |\n")
            f.write("|---|---|---|---|\n")
            for m in missing_jds:
                q = f"{m['company']} {m['title']} careers job description".replace(' ', '+')
                link = f"https://www.google.com/search?q={q}"
                f.write(f"| {m['company']} | {m['title']} | {m['source']} | [🔎 Search]({link}) |\n")
        print(f"⚠️  Detailed Report: {m_out}")

if __name__ == "__main__": main()
