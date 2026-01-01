#!/usr/bin/env python3
"""Check why specific files are misclassified."""

import pymupdf
import json
from pathlib import Path
from docx import Document

def check_file_content(file_path: Path):
    """Show brief content summary."""
    ext = file_path.suffix.lower()
    
    print(f"\n{'='*70}")
    print(f"File: {file_path.name}")
    print(f"{'='*70}")
    
    if not file_path.exists():
        print(f"❌ FILE DOES NOT EXIST")
        print(f"Reason classified as 'other': File not found during scan")
        return
    
    try:
        if ext == '.pdf':
            doc = pymupdf.open(file_path)
            text = ""
            for page in doc[:2]:  # First 2 pages
                text += page.get_text()
            doc.close()
        elif ext == '.docx':
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs[:50]])
        else:
            text = ""
        
        text_lower = text.lower()
        
        print(f"Content preview (first 500 chars):")
        print(text[:500])
        print("\n" + "="*70)
        
        # Check key indicators
        has_nitin = "nitin" in text_lower
        has_resume_sections = sum([
            'experience' in text_lower,
            'education' in text_lower,
            'skills' in text_lower
        ])
        
        print(f"Has 'Nitin': {has_nitin}")
        print(f"Resume section keywords: {has_resume_sections}/3")
        
    except Exception as e:
        print(f"Error reading file: {e}")


base_path = Path.home() / "Downloads" / "NitinResumes"

print("\n" + "="*70)
print("RECRUITER CONTACT FILES (classified as resumes)")
print("="*70)

recruiter_files = [
    "ExecFirmsDetailed31.pdf",
    "ExecSearchDetailed1972.pdf",
    "ExecSearchDetailed544.pdf",
    "ExecSearchDetailed926.pdf",
    "ExecSearchDetailed15.pdf",
]

for filename in recruiter_files:
    check_file_content(base_path / filename)

print("\n\n" + "="*70)
print("JOB DESCRIPTION FILES (classified as resumes)")
print("="*70)

jd_files = [
    "VP of IT, Artificial Intelligence & Innovation Job Description.docx",
    "Vice-President--Customer-Experience-Technology.pdf",
]

for filename in jd_files:
    check_file_content(base_path / filename)

print("\n\n" + "="*70)
print("FILES CLASSIFIED AS 'OTHER'")
print("="*70)

other_files = [
    "Nitin Verma CL.pdf",
    "Nitin Verma RMR.pdf",
    "Nitin Verma.pdf",
]

for filename in other_files:
    check_file_content(base_path / filename)
