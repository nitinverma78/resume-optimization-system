#!/usr/bin/env python3
"""[Supply Discovery] Step 3: Generate report."""
import json,os,sys
from pathlib import Path
from collections import defaultdict

CATS=[
    ('user_resumes',"User Resumes","Your resumes"), 
    ('user_cls',"User CLs","Your cover letters"), 
    ('user_combined',"Combined","Both"), 
    ('jds',"JDs","Job Descriptions"),
    ('companies',"Companies","Target lists"),
    ('recruiters',"Recruiters","Recruiter info"),
    ('presentations',"Presentations","Slides"),
    ('other',"Other","Uncategorized/Exception")
]

# Manual .env loading
env_path = Path(__file__).parent.parent / ".env"
_env_loaded = False
if env_path.exists():
    for l in env_path.read_text().splitlines():
        if '=' in l and not l.strip().startswith('#'):
            k, v = l.strip().split('=', 1)
            # Only set if not already set (respect existing env)
            if not os.getenv(k): os.environ[k] = v.strip('"').strip("'"); _env_loaded = True

def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")

def folder(p): 
    # Try to show path relative to RESUME_FOLDER for better context
    if rf := os.getenv('RESUME_FOLDER'):
        try: return str(Path(p).parent.relative_to(rf))
        except ValueError: pass
    return Path(p).parent.name

def main():
    dd=get_data_dir(); inp,out = dd/"supply"/"2_file_inventory.json", dd/"supply"/"2_classification_report.md"
    if not inp.exists(): return
    
    cls=json.loads(inp.read_text()); rpt=[f"# Classification Report\nTotal files: {sum(len(v) for k,v in cls.items() if isinstance(v,list))}\n"]
    
    # Process main categories
    for k,t,d in CATS:
        if items:=cls.get(k,[]):
            rpt+=[f"## {t} ({len(items)})\n*{d}*\n"]
            grps=defaultdict(list); [grps[folder(x['path'])].append(x) for x in items]
            
            # Sort folders, putting root '.' first
            sorted_folders = sorted(grps.items(), key=lambda x: (x[0]!='.', x[0]))
            
            for f,files in sorted_folders: 
                display_folder = f if f != '.' else 'Root'
                rpt+=[f"### {display_folder}/ ({len(files)})"] + [f"- `{x['name']}`" for x in sorted(files,key=lambda x:x['name'])] + [""]

    with open(out,'w') as f: f.write("\n".join(rpt))
    print(f"✓ Report: {out}")

if __name__=="__main__": main()
