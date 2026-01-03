#!/usr/bin/env python3
"""[Supply Discovery] Step 3: Generate report."""
import json,os,sys
from pathlib import Path
from collections import defaultdict

CATS=[('user_resumes',"User Resumes","Your resumes"), ('user_cls',"User CLs","Your cover letters"), ('user_combined',"Combined","Both"), ('jds',"JDs","Job Descriptions")]
def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")
def folder(p): return Path(p).parent.name

def main():
    dd=get_data_dir(); inp,out = dd/"supply"/"2_file_inventory.json", dd/"supply"/"2_classification_report.md"
    if not inp.exists(): return
    
    cls=json.loads(inp.read_text()); rpt=[f"# Classification Report\nTotal cats: {len(cls)}\n"]
    for k,t,d in CATS:
        if items:=cls.get(k,[]):
            rpt+=[f"## {t} ({len(items)})\n*{d}*\n"]
            grps=defaultdict(list); [grps[folder(x['path'])].append(x) for x in items]
            for f,files in sorted(grps.items()): rpt+=[f"### {f}/ ({len(files)})"] + [f"- `{x['name']}`" for x in sorted(files,key=lambda x:x['name'])] + [""]
    
    with open(out,'w') as f: f.write("\n".join(rpt))
    print(f"✓ Report: {out}")

if __name__=="__main__": main()
