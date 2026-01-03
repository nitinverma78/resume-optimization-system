#!/usr/bin/env python3
"""[Supply Knowledge Extraction] Step 6: Build master knowledge base."""
import json,re,difflib,os,sys
from pathlib import Path
from collections import defaultdict

TAG_TAX = {"Leadership":["led","managed","strategy"],"AI": ["ai","ml","nlp","model"],"Tech":["cloud","aws","api","docker"],"Impact":["revenue","saved","growth"]} 
CO_MAP = {"amazon":"Amazon", "staples":"Staples", "aspen":"Aspen Dental", "tag":"Aspen Dental", "fico":"FICO"}
def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")
def norm(txt): return re.sub(r'\W+', ' ', txt.lower()).strip()
def canon(n): return next((v for k,v in CO_MAP.items() if k in n.lower()), n.strip())

def get_tags(txt):
    tags=set(); t=txt.lower()
    for cat,kws in TAG_TAX.items(): 
        if any(k in t for k in kws): tags.add(cat)
    if re.search(r'(\$\d|\d%|\d\+)', txt): tags.add("Quantifiable")
    return list(tags)

def merge(bullets):
    uniq=[]
    for b in bullets:
        b_n = norm(b['text']); match=None
        for u in uniq:
            if difflib.SequenceMatcher(None, b_n, norm(u['text'])).ratio() > 0.85:
                match=u; match['sources'].append(b['source']); match['text']=max(b['text'],u['text'],key=len); break
        if not match: uniq.append({'text':b['text'], 'sources':[b['source']], 'tags':get_tags(b['text'])})
    return uniq

def main():
    dd=get_data_dir(); inp,out = dd/"supply"/"5_extracted_content.json", dd/"supply"/"6_knowledge_base.json"
    if not inp.exists(): print(f"Missing {inp}"); sys.exit(1)
    
    db=json.loads(inp.read_text()); kb={"meta":{"files":len(db)},"companies":defaultdict(lambda:{"roles":set(),"bullets":[]})}
    temp=defaultdict(list)
    
    for e in db:
        src=e.get('source_file','')
        for stage in ['recent','earlier']:
            for blk in e.get('experience',{}).get(stage,[]):
                co=canon(blk['company'])
                kb['companies'][co]['roles'].add(blk.get('role','Unknown'))
                for b in blk.get('bullets',[]): temp[co].append({'text':b['text'], 'source':src})
    
    print(f"Consolidating {len(temp)} companies...")
    kb['companies'] = {co: {"name":co, "roles":list(kb['companies'][co]['roles']), "bullet_pool":merge(temp[co]), "bullet_count":len(merge(temp[co]))} 
                       for co in temp}
    
    with open(out, 'w') as f: json.dump(kb, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved to {out}")

if __name__=="__main__": main()
