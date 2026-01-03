#!/usr/bin/env python3
"""[Supply Knowledge Extraction] Step 4: Discover unique section headers in resumes."""
import json,os,re,pymupdf
from pathlib import Path
from collections import Counter
from typing import List,Dict,Set

# Standard headers to always catch
STD_HEADERS = {
    'EXPERIENCE', 'WORK HISTORY', 'EDUCATION', 'SKILLS', 'PROJECTS',
    'SUMMARY', 'OBJECTIVE', 'PUBLICATIONS', 'CERTIFICATIONS', 'AWARDS',
    'PROFESSIONAL EXPERIENCE', 'TECHNICAL SKILLS', 'CORE COMPETENCIES'
}

def extract_headers(txt: str) -> List[str]:
    """Identify lines that look like section headers."""
    headers = []
    for line in txt.split('\n'):
        line = line.strip()
        if not line: continue
        
        is_short  = len(line) < 40
        is_upper  = line.isupper()
        not_bullet = not re.match(r'^[•\-\*\d\.]', line)
        is_std    = line.upper() in STD_HEADERS
        
        if (is_short and is_upper and not_bullet) or is_std:
            clean = re.sub(r'[:\.]+$', '', line).strip()
            if len(clean) > 3: headers.append(clean)
            
    return headers

def get_pdf_headers(fp: Path) -> List[str]:
    """Extract headers from a single PDF."""
    try:
        doc = pymupdf.open(fp)
        txt = "".join(p.get_text() for p in doc)
        doc.close()
        return extract_headers(txt)
    except: return []

def get_data_dir():
    if d := os.getenv('DATA_DIR'): return Path(d)
    return Path(__file__).parent.parent/"data"

def main(
    cls_file: Path = None,
    out_json: Path = None,
    out_rpt: Path = None
):
    """Main discovery loop."""
    data_dir = get_data_dir()
    if not cls_file: cls_file = data_dir/"supply"/"2_file_inventory.json"
    if not out_json: out_json = data_dir/"supply"/"4_section_headers.json"
    if not out_rpt:  out_rpt  = data_dir/"supply"/"4_section_headers_report.md"
    
    if not cls_file.exists():
        print(f"Error: {cls_file} not found. Run Step 2 first.")
        return

    with open(cls_file, 'r') as f: inv = json.load(f)
        
    print("Discovering section headers in resumes...")
    
    counts = Counter()
    n = 0
    
    # Scan resumes and combined docs - handle both old and new field names
    cats = ['user_resumes', 'user_combined']
    for cat in cats:
        if cat not in inv: continue
        files = inv[cat]
        print(f"\nScanning {cat} ({len(files)} files)...")
        
        for finfo in files:
            p = Path(finfo['path'])
            if not p.exists(): continue
            counts.update(get_pdf_headers(p))
            n += 1
            print(".", end="", flush=True)

    print(f"\n\n✓ Discovery complete! Scanned {n} files.")
    
    # Save JSON
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(dict(counts), f, indent=2, ensure_ascii=False)
        
    # Generate Report
    with open(out_rpt, 'w', encoding='utf-8') as f:
        f.write("# Resume Section Header Analysis\n\n")
        f.write("Unique potential section headers found. Map to canonical sections.\n\n")
        f.write("## Most Common Headers (Found in > 5 files)\n")
        f.write("| Header | Occurrences | Recommended Mapping |\n")
        f.write("| :--- | :--- | :--- |\n")
        
        sorted_h = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        for h, c in sorted_h:
            if c >= 5: f.write(f"| **{h}** | {c} | _(Assign)_ |\n")
                
        f.write("\n## Less Common Headers\n")
        for h, c in sorted_h:
            if 1 < c < 5: f.write(f"- {h} ({c})\n")

    print(f"  Saved raw counts to: {out_json}")
    print(f"  Saved report to: {out_rpt}")

if __name__ == "__main__": main()
