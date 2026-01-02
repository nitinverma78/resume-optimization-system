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

def main(
    pdf: Path = Path(__file__).parent.parent/"data"/"supply"/"profile_data"/"MyLinkedInProfile.pdf",
    out: Path = Path(__file__).parent.parent/"data"/"supply"/"profile_data"/"linkedin-profile-parsed.json"
):
    """Main execution."""
    pdf = Path(os.getenv('LINKEDIN_PDF', str(pdf)))
    out = out or pdf.parent/"linkedin-profile-parsed.json"
    
    if not pdf.exists():
        print(f"Error: PDF not found at {pdf}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Parsing {pdf}...")
    data = parse_pdf(pdf)
    
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Parsed successfully!")
    print(f"✓ Saved to: {out}")
    print(f"\nExtracted {len(data['raw_text'])} characters")
    print("\n--- Preview ---")
    print(data['raw_text'][:500])

if __name__ == "__main__": main()
