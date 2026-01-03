#!/usr/bin/env python3
"""[Supply Discovery] Step 3: Generate readable classification report."""
import json,os
from pathlib import Path
from collections import defaultdict

# If env var not set, default to None (relative paths might fail, defaulting to full)
ROOT = Path(os.path.expanduser(os.getenv('RESUME_FOLDER', '/tmp')))

# Category definitions: key -> (title, description)
CATS = [
    ('user_resumes',  "User Resumes",           "Files identified as your resume variations"),
    ('user_cls',      "User Cover Letters",     "Files identified as your cover letters"),
    ('user_combined', "User Combined Documents","Files containing BOTH resume and cover letter"),
    ('presentations', "Presentations",          "Your presentations and slide decks"),
    ('jds',           "Job Descriptions",       "JDs for roles you've applied to"),
    ('other_resumes', "Other Resumes",          "Resumes that don't appear to be yours"),
    ('recruiters',    "Recruiters",             "Recruiter and exec search firm info"),
    ('companies',     "Companies",              "Company research and lists"),
    ('tracking',      "Tracking Files",         "Spreadsheets for tracking applications"),
    ('other',         "Other Files",            "Miscellaneous files"),
]

def rel_folder(p: str) -> str:
    """Get relative folder path from root."""
    try:    return str(Path(p).parent.relative_to(ROOT)) or '.'
    except: return Path(p).parent.name

def group_by_folder(items: list) -> dict:
    """Group items by folder path."""
    d = defaultdict(list)
    for f in items: d[rel_folder(f['path'])].append(f)
    return dict(sorted(d.items()))

def gen_report(cls_path: Path, out_md: Path):
    """Generate markdown report grouped by category and folder."""
    with open(cls_path) as f: cls = json.load(f)
    
    # Aliases for backward compat
    cls['user_cls'] = cls.get('user_cls') or cls.get('user_cover_letters', [])
    cls['tracking'] = cls.get('tracking') or cls.get('tracking_files', [])
    
    rpt = [
        "# File Classification Report\n",
        f"**Root folder:** `{ROOT}`\n\n",
        f"Total files: {sum(len(cls.get(k,'')) for k,_,_ in CATS)}\n",
        "---\n\n"
    ]
    
    for key, title, desc in CATS:
        items = cls.get(key, [])
        rpt.append(f"## {title} ({len(items)} files)\n*{desc}*\n\n")
        for folder, files in group_by_folder(items).items():
            rpt.append(f"### {folder or '(root)'}/ ({len(files)} files)\n")
            rpt.extend(f"- `{f['name']}`\n" for f in sorted(files, key=lambda x: x['name']))
            rpt.append("\n")
        rpt.append("---\n\n")
    
    with open(out_md, 'w') as f: f.writelines(rpt)

def get_data_dir():
    if d := os.getenv('DATA_DIR'): return Path(d)
    return Path(__file__).parent.parent/"data"

def main(
    cls_file: Path = None,
    out: Path = None
):
    data_dir = get_data_dir()
    if not cls_file: cls_file = data_dir/"supply"/"2_file_inventory.json"
    if not out: out = data_dir/"supply"/"2_classification_report.md"
    if not cls_file.exists():
        print(f"Error: {cls_file} not found. Run 2_classify_files.py first."); return
    print("Generating classification report...")
    gen_report(cls_file, out)
    print(f"✓ Report generated: {out}")

if __name__ == "__main__": main()
