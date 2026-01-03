#!/usr/bin/env python3
"""[Supply Public Profile] Step 7: Parse LinkedIn profile PDF."""
import sys,json,os
from pathlib import Path
import pymupdf

def parse_pdf(pdf: Path) -> dict:
    """Extract text from LinkedIn profile PDF."""
    doc = pymupdf.open(pdf)
    txt = "".join(p.get_text() for p in doc)
    n_pages = doc.page_count
    doc.close()
    return {"raw_text": txt, "metadata": {"source": str(pdf), "pages": n_pages}}

import argparse

def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Parse LinkedIn Profile PDF")
    parser.add_argument("pdf", nargs="?", help="Path to PDF")
    parser.add_argument("--out", help="Output JSON path")
    
    args = parser.parse_args()

    # Default output path
    default_out = Path(__file__).parent.parent/"data"/"supply"/"profile_data"/"linkedin-profile-parsed.json"
    
    # Resolve PDF path: Arg > Env > Search RESUME_FOLDER
    if args.pdf:
        pdf = Path(args.pdf)
    elif os.getenv('LINKEDIN_PDF'):
        pdf = Path(os.getenv('LINKEDIN_PDF'))
    else:
        # Search for MyLinkedInProfile.pdf in RESUME_FOLDER
        resume_folder = os.getenv('RESUME_FOLDER')
        if not resume_folder:
            print("Error: RESUME_FOLDER not set and no PDF path provided", file=sys.stderr)
            sys.exit(1)
        
        resume_folder = Path(resume_folder).expanduser()
        # Search in root and subdirectories for MyLinkedInProfile.pdf
        found = list(resume_folder.rglob("MyLinkedInProfile.pdf"))
        
        if not found:
            print(f"Error: MyLinkedInProfile.pdf not found in {resume_folder} (searched recursively)", file=sys.stderr)
            sys.exit(1)
        
        pdf = found[0]  # Use first match
        if len(found) > 1:
            print(f"Warning: Multiple MyLinkedInProfile.pdf found, using: {pdf}")
    
    out = Path(args.out) if args.out else default_out
    
    if not pdf.exists():
        print(f"Error: PDF not found at {pdf}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Parsing {pdf}...")
    data = parse_pdf(pdf)
    
    # Ensure output directory exists
    out.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Parsed successfully!")
    print(f"✓ Saved to: {out}")
    print(f"\nExtracted {len(data['raw_text'])} characters")
    print("\n--- Preview ---")
    print(data['raw_text'][:500])

if __name__ == "__main__": main()
