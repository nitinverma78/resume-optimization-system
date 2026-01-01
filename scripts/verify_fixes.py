#!/usr/bin/env python3
"""
Quick check to verify specific files are classified correctly.
"""

import json, os
from pathlib import Path

def check_specific_files(
    classified_file: Path = Path(__file__).parent.parent / "data" / "classified_files.json"  # Classified files JSON
):
    """Check classification of specific problematic files."""
    # Allow environment variable override
    classified_file = Path(os.getenv('CLASSIFIED_FILE', str(classified_file)))
    
    with open(classified_file, 'r') as f:
        data = json.load(f)
    
    files_to_check = {
        'EnterpriseAgenticAI.pdf': None,
        'AspenDentalCoverLetter.pdf': 'user_cover_letter',
        'TheRealRealCoverLetter.pdf': 'user_cover_letter',
        'Response Siena.docx': 'user_resume',
    }
    
    print("Checking specific file classifications:\n")
    
    for category_name, files in data.items():
        for file_info in files:
            filename = file_info['name']
            if filename in files_to_check:
                files_to_check[filename] = category_name
    
    for filename, category in files_to_check.items():
        status = "✅" if category else "❌ NOT FOUND"
        print(f"{status} {filename}: {category}")
    
    print("\n" + "="*60)
    print("Expected results:")
    print("  EnterpriseAgenticAI.pdf: 'other' (presentation)")
    print("  AspenDentalCoverLetter.pdf: 'user_cover_letters'")
    print("  TheRealRealCoverLetter.pdf: 'user_cover_letters'")
    print("  Response Siena.docx: 'user_resumes'")

if __name__ == "__main__":
    check_specific_files()
