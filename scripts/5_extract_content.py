#!/usr/bin/env python3
"""[Supply Knowledge Extraction] Step 5: Extract structured content."""
import json,re,os,sys
from pathlib import Path
from scripts.lib_extract import extract

SEC_PATS = {
    "Summary": r"(?i)^(SUMMARY|PROFILE|PROFESSIONAL SUMMARY|EXECUTIVE SUMMARY)$",
    "Experience": r"(?i)^(PROFESSIONAL EXPERIENCE|EXPERIENCE|WORK HISTORY)$",
    "Skills": r"(?i)^(SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|AREAS OF EXPERTISE)$",
    "Education": r"(?i)^(EDUCATION)$",
    "Patents": r"(?i)^(PATENTS|INVENTIONS)$",
    "Publications": r"(?i)^(PUBLICATIONS)$",
    "Talks": r"(?i)^(TALKS)$",
    "Awards": r"(?i)^(AWARDS)$"
}

def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")

def identify_sections(lines):
    secs = {"Uncategorized": {'header': 'Start', 'content': []}}; cur = "Uncategorized"
    for line in [l.strip() for l in lines if l.strip()]:
        matched = next((cat for cat, pat in SEC_PATS.items() if len(line)<60 and re.match(pat, line)), None)
        if matched: cur=matched; secs[cur]={'header':line, 'content':[]}
        else: secs[cur]['content'].append(line)
    return secs

HARD_KW = {'python','java','c++','sql','aws','pytorch','tensorflow','docker','kubernetes','linux','git'} 
SOFT_KW = {'leadership','strategy','management','agile','communication','stakeholder'}
THEMES = {"Leadership":['led','managed','strategy'], "Technical":['built','deployed','system'], "Optimization":['improved','saved']}
RECENT_COS = ['manifold','aspen','tag','staples','investor']

def classify_skills(lines):
    hard, soft, other = [], [], []
    for line in lines:
        lo = line.lower()
        if any(k in lo for k in HARD_KW) and len(line.split())<10: hard.append(line)
        elif any(k in lo for k in SOFT_KW): soft.append(line)
        else: other.append(line)
    return {'hard':hard,'soft':soft,'other':other}

def parse_exp(lines):
    recs, earls = [], []; blk = None; ALL = RECENT_COS + ['zulily','amazon']
    def save(b): (recs if any(r in b['company'].lower() for r in RECENT_COS) else earls).append(b)
    
    for line in lines:
        is_co = any(c in line.lower() for c in ALL) and len(line)<100
        if is_co:
            if blk: save(blk)
            blk={'company':line,'role':'','bullets':[],'tags':set()}
        elif blk:
            if line.startswith(('•','-')): 
                t=re.sub(r'^[•\-\*]\s*','',line)
                tags = [k for k,kw in THEMES.items() if any(x in t.lower() for x in kw)]
                blk['bullets'].append({'text':t,'tags':tags}); blk['tags'].update(tags)
            elif not blk['role']: blk['role']=line
    if blk: save(blk)
    for b in recs+earls: b['tags']=list(b.get('tags',[]))
    return {'recent':recs, 'earlier':earls}

def process(fp):
    txt = extract(fp).lower(); secs = identify_sections(txt.split('\n'))
    data = {"source_file":fp.name, "role_intent":secs.get("Summary",{}).get("header","General"), "summary":"\n".join(secs.get("Summary",{}).get("content",[])), "skills":{}, "experience":{'recent':[],'earlier':[]} }
    if "Skills" in secs: data["skills"] = classify_skills(secs["Skills"]['content'])
    if "Experience" in secs: data["experience"] = parse_exp(secs["Experience"]['content'])
    for k in ["Patents","Publications","Talks"]: 
        if k in secs: data[k.lower()] = secs[k]['content']
    return data

def main():
    dd = get_data_dir()
    cls_P, out_P = dd/"supply"/"2_file_inventory.json", dd/"supply"/"5_extracted_content.json"
    if not cls_P.exists(): print (f"Missing {cls_P}"); sys.exit(1)
    
    inv = json.loads(cls_P.read_text()); db = []
    files = [Path(f['path']) for k in ['user_resumes','user_combined'] if k in inv for f in inv[k] if Path(f['path']).exists()]
    
    print(f"Extracting {len(files)} files...")
    for f in files: db.append(process(f)); print(".", end="", flush=True)
    
    with open(out_P, 'w') as f: json.dump(db, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved {len(db)} to {out_P}")

if __name__=="__main__": main()
