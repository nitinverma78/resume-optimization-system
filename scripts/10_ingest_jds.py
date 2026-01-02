#!/usr/bin/env python3
"""[Demand Discovery] Step 10: Ingest job descriptions into database."""
import json,os,re,subprocess,pymupdf
from pathlib import Path
from typing import List,Dict,Any

def extract_txt(fp: Path) -> str:
    """Read text from supported file types."""
    txt = ""
    try:
        if fp.suffix.lower() == '.pdf':
            doc = pymupdf.open(fp)
            txt = "".join(p.get_text()+"\n" for p in doc)
        elif fp.suffix.lower() in ['.txt', '.md']:
            txt = fp.read_text(encoding='utf-8', errors='ignore')
        elif fp.suffix.lower() in ['.docx', '.doc']:
            r = subprocess.run(['textutil','-convert','txt','-stdout',str(fp)],
                              capture_output=True, text=True)
            if r.returncode == 0: txt = r.stdout
            else: print(f"  [Error] textutil failed for {fp.name}")
    except Exception as e:
        print(f"  Error reading {fp.name}: {e}")
    return txt

def parse_jd(txt: str, fname: str) -> Dict[str,Any]:
    """Parse JD text to extract metadata and rubric."""
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    title = lines[0] if lines else "Unknown Role"
    
    secs = {'Responsibilities': [], 'Requirements': [], 'Summary': []}
    cur = 'Summary'
    
    for line in lines:
        if   re.search(r'(?i)(responsibilit|duties|what you will do)', line): cur = 'Responsibilities'
        elif re.search(r'(?i)(requirement|qualification|skills|who you are)', line): cur = 'Requirements'
        else: secs[cur].append(line)
    
    return {"id": fname, "title": title, "company": "Unknown Company",
            "raw_text": txt, "structured_sections": secs}

def main(
    inp_dir: Path = Path(__file__).parent.parent/"data"/"demand"/"raw_jds",
    out_db: Path = Path(__file__).parent.parent/"data"/"demand"/"1_jd_database.json"
):
    """Main ingestion loop."""
    if not inp_dir.exists():
        print(f"Error: {inp_dir} not found.")
        return

    print("Ingesting Job Descriptions...")
    
    db = []
    for fp in inp_dir.glob("*.*"):
        if fp.name.startswith('.'): continue
        print(f"  Processing {fp.name}...")
        txt = extract_txt(fp)
        if txt and len(txt) > 100:
            db.append(parse_jd(txt, fp.name))
        else:
            print(f"    Skipping (Empty or unreadable)")
            
    if not db:
        print("No valid JDs found. Please add files to data/demand/raw_jds/")
        return
        
    with open(out_db, 'w', encoding='utf-8') as f:
        json.dump({"roles": db}, f, indent=2, ensure_ascii=False)
        
    print(f"\n✓ Ingested {len(db)} JDs.")
    print(f"  Database saved to: {out_db}")

if __name__ == "__main__": main()
