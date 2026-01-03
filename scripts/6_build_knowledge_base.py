#!/usr/bin/env python3
"""[Supply Knowledge Extraction] Step 6: Build master knowledge base."""
import json,re,difflib,os,sys,argparse
from pathlib import Path
from collections import defaultdict

# Defaults (Generic)
DEF_TAGS = {"Leadership":["led","managed"],"Tech":["cloud","api"],"Impact":["saved","growth"]}
DEF_MAP = {}

def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")
def norm(txt): return re.sub(r'\W+', ' ', txt.lower()).strip()

def load_cfg(p):
    try:
        if p and Path(p).exists(): return json.loads(Path(p).read_text())
        if (d:=Path(__file__).parent.parent/"config"/"knowledge_base.json").exists(): return json.loads(d.read_text())
    except Exception as e: print(f"⚠️ Config error: {e}")
    print("⚠️ Using default config."); return {"company_map":DEF_MAP, "tag_taxonomy":DEF_TAGS}

def get_tags(txt, tax):
    t=txt.lower(); tags={cat for cat,kws in tax.items() if any(k in t for k in kws)}
    if re.search(r'(\$\d|\d%|\d\+)', txt): tags.add("Quantifiable")
    return list(tags)

def merge(bullets, tax):
    uniq=[]
    for b in bullets:
        b_n=norm(b['text']); m=None
        for u in uniq:
            if difflib.SequenceMatcher(None, b_n, norm(u['text'])).ratio() > 0.85:
                m=u; m['sources'].append(b['source']); m['text']=max(b['text'],u['text'],key=len); break
        if not m: uniq.append({'text':b['text'], 'sources':[b['source']], 'tags':get_tags(b['text'], tax)})
    return uniq

def main():
    p = argparse.ArgumentParser(); p.add_argument("--config"); args = p.parse_args()
    cfg = load_cfg(args.config); cm, tt = cfg.get("company_map", DEF_MAP), cfg.get("tag_taxonomy", DEF_TAGS)
    
    dd=get_data_dir(); inp,out = dd/"supply"/"5_extracted_content.json", dd/"supply"/"6_knowledge_base.json"
    if not inp.exists(): sys.exit(f"Missing {inp}")
    
    db=json.loads(inp.read_text()); kb={"meta":{"files":len(db)},"companies":defaultdict(lambda:{"roles":set(),"bullets":[]})}
    temp=defaultdict(list); canon = lambda n: next((v for k,v in cm.items() if k in n.lower()), n.strip())

    for e in db:
        for stage in ['recent','earlier']:
            for blk in e.get('experience',{}).get(stage,[]):
                co=canon(blk['company']); kb['companies'][co]['roles'].add(blk.get('role','Unknown'))
                [temp[co].append({'text':b['text'], 'source':e.get('source_file','')}) for b in blk.get('bullets',[])]
    
    print(f"Consolidating {len(temp)} companies...")
    kb['companies'] = {co: {"name":co, "roles":list(kb['companies'][co]['roles']), "bullet_pool":merge(temp[co], tt), "bullet_count":len(merge(temp[co], tt))} for co in temp}
    
    with open(out, 'w') as f: json.dump(kb, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved to {out}")

if __name__=="__main__": main()
