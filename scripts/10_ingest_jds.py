#!/usr/bin/env python3
"""
[Demand Discovery] Step 10: Ingest job descriptions into database.

Current Capabilities:
1. Manual Drops: Ingests PDFs/DOCs from `data/demand/raw_jds/`.
2. Classified Inventory: Ingests "jds" category files identified in Step 2.
3. LinkedIn Data: Parses `Job Applications.csv` for historical application metadata.

Outputs: `data/demand/1_jd_database.json`
"""
import json,os,re,subprocess,pymupdf,csv
from pathlib import Path
from typing import List,Dict,Any

DATA = Path(__file__).parent.parent/"data"
RAW  = DATA/"demand"/"raw_jds"
INV  = DATA/"supply"/"2_file_inventory.json"
OUT  = DATA/"demand"/"1_jd_database.json"

def extract_txt(fp: Path) -> str:
    """Read text from supported file types."""
    try:
        if fp.suffix.lower() == '.pdf':
            doc = pymupdf.open(fp)
            txt = "".join(p.get_text()+"\n" for p in doc); doc.close()
            return txt
        elif fp.suffix.lower() in ['.txt', '.md']:
            return fp.read_text(encoding='utf-8', errors='ignore')
        elif fp.suffix.lower() in ['.docx', '.doc']:
            r = subprocess.run(['textutil','-convert','txt','-stdout',str(fp)], capture_output=True, text=True)
            return r.stdout if r.returncode==0 else ""
    except Exception as e: print(f"  Err {fp.name}: {e}")
    return ""

def parse_jd(txt: str, fname: str, src: str) -> Dict[str,Any]:
    """Parse JD text to extract metadata and rubric."""
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    title = lines[0] if lines else "Unknown Role"
    
    secs = {'Responsibilities': [], 'Requirements': [], 'Summary': []}
    cur = 'Summary'
    for line in lines:
        if   re.search(r'(?i)(responsibilit|duties|what you will do)', line): cur = 'Responsibilities'
        elif re.search(r'(?i)(requirement|qualification|skills|who you are)', line): cur = 'Requirements'
        else: secs[cur].append(line)
    
    return {"id": fname, "title": title, "company": "Unknown", "source": src,
            "raw_text": txt, "sections": secs, "type": "job_description"}

def parse_linkedin_csv(fp: Path) -> List[Dict[str,Any]]:
    """Parse Job Applications.csv from LinkedIn export."""
    jds = []
    try:
        with open(fp, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map fields
                jds.append({
                    "id": f"LI-APP-{row.get('Application Date','unknown')}-{row.get('Company Name','unknown')}",
                    "title": row.get('Job Title', 'Unknown Title'),
                    "company": row.get('Company Name', 'Unknown Company'),
                    "source": "linkedin_application",
                    "url": row.get('Job Url', ''),
                    "resume_used": row.get('Resume Name', ''),
                    "q_and_a": row.get('Question And Answers', ''),
                    "date": row.get('Application Date', ''),
                    "type": "application_record"
                })
    except Exception as e: print(f"  Err parsing CSV {fp.name}: {e}")
    return jds

def main():
    print("🚀 Ingesting Job Descriptions...")
    db = []
    
    # 1. Classified JDs (from Step 2 inventory)
    if INV.exists():
        with open(INV) as f: inv = json.load(f)
        items = inv.get('jds', []) + inv.get('job_descriptions', [])
        print(f"📦 Found {len(items)} classified items in inventory")
        
        for f in items:
            fp = Path(f['path'])
            if not fp.exists(): continue
            
            # Special handling for known CSVs
            if f['name'] == 'Job Applications.csv':
                print(f"  Parsing LinkedIn Applications: {f['name']}")
                apps = parse_linkedin_csv(fp)
                db.extend(apps)
                print(f"    -> Extracted {len(apps)} application records")
                continue
                
            if fp.suffix.lower() in ['.xlsx', '.csv']: 
                continue # Skip other logs/spreadsheets
            
            print(f"  Processing JD file: {f['name']}")
            if txt := extract_txt(fp):
                db.append(parse_jd(txt, f['name'], "classified_file"))
    else: print("⚠️  Inventory not found.")

    # 2. Raw JDs (Manual drops)
    if RAW.exists():
        for fp in RAW.glob("*.*"):
            if fp.name.startswith('.'): continue
            print(f"  Processing raw drop: {fp.name}")
            if txt := extract_txt(fp):
                db.append(parse_jd(txt, fp.name, "raw_manual"))
    
    if not db: print("❌ No JDs ingested."); return

    with open(OUT, 'w') as f: json.dump({"roles": db}, f, indent=2)
    print(f"\n✅ Ingested {len(db)} total records. Saved to {OUT}")

if __name__ == "__main__": main()
