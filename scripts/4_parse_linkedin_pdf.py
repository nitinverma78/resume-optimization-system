#!/usr/bin/env python3
"""
Parse LinkedIn profile PDF and extract structured data.
"""

import sys, json, os
from pathlib import Path
import pymupdf


def parse_linkedin_pdf(pdf_path: Path) -> dict:
    """
    Extract text from LinkedIn profile PDF.
    
    Args:
        pdf_path: Path to the LinkedIn profile PDF
        
    Returns:
        Dictionary containing extracted profile data
    """
    doc = pymupdf.open(pdf_path)
    
    # Extract all text from all pages
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    
    # Get page count before closing
    page_count = doc.page_count
    doc.close()
    
    # Return raw text with metadata
    return {"raw_text": full_text, "metadata": {"source": str(pdf_path), "pages": page_count}}


def main(
    pdf_path: Path = Path(__file__).parent.parent / "data" / "supply" / "profile_data" / "MyLinkedInProfile.pdf",
    output_json: Path = Path(__file__).parent.parent / "data" / "supply" / "profile_data" / "linkedin-profile-parsed.json"
):
    """Main execution."""
    # Allow environment variables to override defaults
    pdf_path = Path(os.getenv('LINKEDIN_PDF', str(pdf_path)))
    if output_json is None:
        output_json = pdf_path.parent / "linkedin-profile-parsed.json"
    
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Parsing {pdf_path}...")
    data = parse_linkedin_pdf(pdf_path)
    
    # Save to JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Parsed successfully!")
    print(f"✓ Saved to: {output_json}")
    print(f"\nExtracted {len(data['raw_text'])} characters")
    
    # Preview first 500 characters
    print("\n--- Preview ---")
    print(data['raw_text'][:500])


if __name__ == "__main__":
    main()
