#!/usr/bin/env python3
"""[Demand Discovery] Step 10: Ingest job descriptions."""
import json,os,re,csv
from pathlib import Path
from scripts.lib_extract import extract

def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")

def parse_jd(txt, fname, src):
    lines=[l.strip() for l in txt.split('\n') if l.strip()]; cur='Summary'; secs={'Responsibilities':[],'Requirements':[],'Summary':[]}
    for l in lines:
        if re.search(r'(?i)(responsibilit|duties|what you will do)',l): cur='Responsibilities'
        elif re.search(r'(?i)(requirement|qualification|skills|who you are)',l): cur='Requirements'
        else: secs[cur].append(l)
    return {"id":fname, "title":lines[0] if lines else "Role", "company":"Unknown", "source":src, "raw_text":txt, "sections":secs, "type":"jd"}

def parse_csv(fp):
    try: return [{"id":f"LI-{r.get('Application Date')}-{r.get('Company Name')}", "title":r.get('Job Title',''), "company":r.get('Company Name',''), "url":r.get('Job Url',''), "date":r.get('Application Date',''), "type":"app_record"} for r in csv.DictReader(open(fp,encoding='utf-8'))]
    except: return []

def main():
    dd=get_data_dir(); inv_p=dd/"supply"/"2_file_inventory.json"; out=dd/"demand"/"1_jd_database.json"; db=[]
    print("🚀 Ingesting JDs...")
    
    # 1. Classified
    if inv_p.exists():
        inv=json.loads(inv_p.read_text())
        for f in inv.get('jds',[]) + inv.get('job_descriptions',[]):
            fp=Path(f['path'])
            if fp.name=='Job Applications.csv': db.extend(parse_csv(fp)); print(f"  Parsed CSV: {fp.name}")
            elif fp.exists() and fp.suffix.lower() not in ['.xlsx','.csv'] and (txt:=extract(fp)): db.append(parse_jd(txt, f['name'], "classified"))
    
    # 2. Raw
    raw=dd/"demand"/"raw_jds"
    if raw.exists():
        for fp in [x for x in raw.glob("*.*") if not x.name.startswith('.')]:
             if txt:=extract(fp): db.append(parse_jd(txt, fp.name, "manual"))

    if db: 
        out.parent.mkdir(parents=True, exist_ok=True); 
        with open(out,'w') as f: json.dump({"roles":db}, f, indent=2)
        print(f"✅ Ingested {len(db)} JDs to {out}")
    else: print("❌ No JDs found.")

if __name__ == "__main__": main()
