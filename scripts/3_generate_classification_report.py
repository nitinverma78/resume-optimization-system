#!/usr/bin/env python3
"""Generate a readable classification report for user review."""
import json,os
from pathlib import Path

def gen_report(cls_path: Path, out_md: Path):
    """Generate markdown report of classifications."""
    with open(cls_path, 'r', encoding='utf-8') as f: cls = json.load(f)
    
    # Handle both old and new field names
    user_cls  = cls.get('user_cls') or cls.get('user_cover_letters', [])
    tracking  = cls.get('tracking') or cls.get('tracking_files', [])
    
    rpt = []
    rpt.append("# File Classification Report\n")
    rpt.append(f"Total files analyzed: {sum(len(v) for v in cls.values())}\n")
    rpt.append("---\n\n")
    
    def add_section(title, desc, items, show_ext=False):
        rpt.append(f"## {title} ({len(items)} files)\n")
        rpt.append(f"*{desc}*\n\n")
        for i, f in enumerate(sorted(items, key=lambda x: x['name']), 1):
            ext = f.get('ext') or f.get('extension', '')
            if show_ext: rpt.append(f"{i}. `{f['name']}` {ext or '(no ext)'}\n")
            else:        rpt.append(f"{i}. `{f['name']}`\n")
        rpt.append("\n---\n\n")
    
    add_section("User Resumes", "Files identified as your resume variations", cls['user_resumes'])
    add_section("User Cover Letters", "Files identified as your cover letters", user_cls)
    add_section("User Combined Documents", "Files containing BOTH resume and cover letter", cls['user_combined'])
    add_section("Other Resumes", "Resumes that don't appear to be yours", cls['other_resumes'])
    add_section("Tracking Files", "Spreadsheets for tracking applications", tracking)
    add_section("Other Files", "JDs, templates, presentations, misc", cls['other'], show_ext=True)
    
    with open(out_md, 'w', encoding='utf-8') as f: f.writelines(rpt)

def main(
    cls_file: Path = Path(__file__).parent.parent/"data"/"supply"/"2_file_inventory.json",
    out: Path = Path(__file__).parent.parent/"data"/"supply"/"2_classification_report.md"
):
    """Main execution."""
    cls_file = Path(os.getenv('CLASSIFIED_FILE', str(cls_file)))
    out      = Path(os.getenv('REPORT_FILE', str(out)))
    
    if not cls_file.exists():
        print(f"Error: Classified files not found at {cls_file}")
        print("Please run 2_classify_files.py first.")
        return
    
    print("Generating classification report...")
    gen_report(cls_file, out)
    
    print(f"✓ Report generated: {out}")
    print(f"\nYou can review the classifications in: {out}")

if __name__ == "__main__": main()
