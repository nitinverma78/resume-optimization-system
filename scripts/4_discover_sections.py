#!/usr/bin/env python3
"""[Supply Knowledge Extraction] Step 4: Discover unique section headers."""
import json,re,os,sys
from pathlib import Path
from collections import Counter
from scripts.lib_extract import extract

STD_HEADERS = {'EXPERIENCE','WORK HISTORY','EDUCATION','SKILLS','PROJECTS','SUMMARY','OBJECTIVE','PUBLICATIONS','CERTIFICATIONS','AWARDS','PROFESSIONAL EXPERIENCE','TECHNICAL SKILLS','CORE COMPETENCIES'}
def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")

def extract_headers(txt):
    h = []
    for l in txt.split('\n'):
        l=l.strip(); is_upper=l.isupper(); not_b=not re.match(r'^[•\-\*\d\.]',l); is_std=l.upper() in STD_HEADERS
        if (len(l)<40 and is_upper and not_b) or is_std:
            cl = re.sub(r'[:\.]+$','',l).strip()
            if len(cl)>3: h.append(cl)
    return h

def main():
    dd = get_data_dir()
    cls_P, out_J, out_R = dd/"supply"/"2_file_inventory.json", dd/"supply"/"4_section_headers.json", dd/"supply"/"4_section_headers_report.md"
    if not cls_P.exists(): print(f"Missing {cls_P}"); sys.exit(1)
    
    inv = json.loads(cls_P.read_text()); counts = Counter()
    files = [Path(f['path']) for k in ['user_resumes','user_combined'] if k in inv for f in inv[k] if Path(f['path']).exists()]
    
    print(f"Scanning {len(files)} files...")
    for f in files: counts.update(extract_headers(extract(f))); print(".",end="",flush=True)
    
    with open(out_J, 'w') as f: json.dump(dict(counts), f, indent=2, ensure_ascii=False)
    
    rpt = "# Resume Section Header Analysis\n\n| Header | Count | Recommendation |\n|---|---|---|\n"
    for h,c in sorted(counts.items(), key=lambda x:x[1], reverse=True):
        if c>1: rpt += f"| **{h}** | {c} | {'Identify' if c>=5 else 'Check'} |\n"
    out_R.write_text(rpt)
    print(f"\n✓ Saved to {out_J} and {out_R}")

if __name__=="__main__": main()
