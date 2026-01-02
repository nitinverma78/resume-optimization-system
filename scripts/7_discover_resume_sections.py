#!/usr/bin/env python3
"""
Step 7: Discover Resume Sections

Scans all user resumes to discover unique section headers.
Outputs a report to help the user define a canonical mapping strategy.

Output: 
- data/section_headers.json (Raw counts)
- data/section_headers_report.md (Human readable)
"""

import json, os, re
import pymupdf
from pathlib import Path
from collections import Counter
from typing import List, Dict, Set

def extract_potential_headers(text: str) -> List[str]:
    """Identify lines that look like section headers."""
    headers = []
    lines = text.split('\n')
    
    # Common standard headers to always catch even if formatting is weird
    STANDARD_HEADERS = {
        'EXPERIENCE', 'WORK HISTORY', 'EDUCATION', 'SKILLS', 'PROJECTS', 
        'SUMMARY', 'OBJECTIVE', 'PUBLICATIONS', 'CERTIFICATIONS', 'AWARDS',
        'PROFESSIONAL EXPERIENCE', 'TECHNICAL SKILLS', 'CORE COMPETENCIES'
    }
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue
        
        # Heuristics for a header:
        # 1. Short length
        # 2. All CAPS or Title Case
        # 3. Not a bullet point
        # 4. Often followed by content
        
        is_short = len(line) < 40
        is_upper = line.isupper()
        is_title = line.istitle()
        not_bullet = not re.match(r'^[\•\-\*\d\.]', line)
        
        # Check against standard list (case insensitive)
        is_standard = line.upper() in STANDARD_HEADERS
        
        # Check formatting heuristic
        # (Uppercase AND short AND not bullet) OR (Standard Header)
        if (is_short and is_upper and not_bullet) or is_standard:
            # Clean it up
            clean_header = re.sub(r'[:\.]+$', '', line).strip()
            if len(clean_header) > 3: # Ignore tiny unrelated labels
                headers.append(clean_header)
            
    return headers

def process_file_headers(file_path: Path) -> List[str]:
    """Extract headers from a single file."""
    try:
        doc = pymupdf.open(file_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        
        return extract_potential_headers(full_text)
    except Exception as e:
        # print(f"  Error reading {file_path.name}: {e}") # specific errors can be noisy
        return []

def main(
    classified_file: Path = Path(__file__).parent.parent / "data" / "supply" / "2_file_inventory.json",
    output_json: Path = Path(__file__).parent.parent / "data" / "supply" / "3_section_headers.json",
    output_report: Path = Path(__file__).parent.parent / "data" / "supply" / "3_section_headers_report.md"
):
    """Main discovery loop."""
    # Env overrides
    classified_file = Path(os.getenv('CLASSIFIED_FILE', str(classified_file)))
    
    if not classified_file.exists():
        print(f"Error: {classified_file} not found. Run Step 2 first.")
        return

    with open(classified_file, 'r') as f:
        file_inventory = json.load(f)
        
    print("Discovering section headers in resumes...")
    
    header_counts = Counter()
    processed_files = 0
    
    # We scan resumes and combined docs
    categories_to_scan = ['user_resumes', 'user_combined']
    
    for category in categories_to_scan:
        if category not in file_inventory: continue
        
        files_list = file_inventory[category]
        print(f"\nScanning {category} ({len(files_list)} files)...")
        
        for file_info in files_list:
            path = Path(file_info['path'])
            if not path.exists(): continue
            
            headers = process_file_headers(path)
            header_counts.update(headers)
            processed_files += 1
            
            # Progress dot
            print(".", end="", flush=True)

    print(f"\n\n✓ Discovery complete! Scanned {processed_files} files.")
    
    # Save Raw JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(dict(header_counts), f, indent=2, ensure_ascii=False)
        
    # Generate Report
    with open(output_report, 'w', encoding='utf-8') as f:
        f.write("# Resume Section Header Analysis\n\n")
        f.write("This report lists all unique potential section headers found in your files.\n")
        f.write("Use this to decide how to map them to canonical sections (e.g., 'Work History' -> 'Experience').\n\n")
        
        f.write("## Most Common Headers (Found in > 5 files)\n")
        f.write("| Header | Occurrences | Recommended Mapping |\n")
        f.write("| :--- | :--- | :--- |\n")
        
        # Sort by frequency
        sorted_headers = sorted(header_counts.items(), key=lambda x: x[1], reverse=True)
        
        for header, count in sorted_headers:
            if count >= 5:
                f.write(f"| **{header}** | {count} | _(Assign Category)_ |\n")
                
        f.write("\n## Less Common Headers (Review to see if valid)\n")
        for header, count in sorted_headers:
            if 1 < count < 5:
                f.write(f"- {header} ({count})\n")

    print(f"  Saved raw counts to: {output_json}")
    print(f"  Saved report to: {output_report}")

if __name__ == "__main__":
    main()
