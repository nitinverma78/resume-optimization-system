#!/usr/bin/env python3
"""
Quick script to analyze specific files and determine their content type.
"""

import pymupdf
from pathlib import Path
from docx import Document
import re


def extract_pdf_text(file_path: Path, max_pages: int = None) -> str:
    """Extract text from PDF."""
    try:
        doc = pymupdf.open(file_path)
        text = ""
        pages_to_read = len(doc) if max_pages is None else min(max_pages, len(doc))
        for i in range(pages_to_read):
            text += doc[i].get_text()
        doc.close()
        return text.lower()
    except Exception as e:
        return f"ERROR: {e}"


def extract_docx_text(file_path: Path) -> str:
    """Extract text from DOCX."""
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.lower()
    except Exception as e:
        return f"ERROR: {e}"


def analyze_content(text: str) -> dict:
    """Analyze what the document contains."""
    
    # Check if it's Nitin's document
    nitin_indicators = [
        r'nitin\s+verma',
        r'nitinverma78@(?:gmail|yahoo)\.com',
        r'linkedin\.com/in/nvlead',
        r'manifold\s+systems',
        r'wharton.*mba',
        r'iit.*madras'
    ]
    
    is_nitins = sum(1 for p in nitin_indicators if re.search(p, text)) >= 2
    
    # Check for cover letter indicators
    cl_indicators = [
        r'dear\s+(?:hiring|recruiter|manager)',
        r'i\s+am\s+writing\s+to\s+express',
        r'i\s+am\s+excited\s+to\s+apply',
        r'sincerely',
        r'thank\s+you\s+for\s+considering',
    ]
    
    has_cover_letter = sum(1 for p in cl_indicators if re.search(p, text)) >= 2
    
    # Check for resume indicators
    resume_sections = [
        r'\bexperience\b',
        r'\beducation\b',
        r'\bskills\b',
        r'professional\s+summary',
        r'accomplishments',
        r'employment'
    ]
    
    has_resume = sum(1 for p in resume_sections if re.search(p, text)) >= 3
    
    # Estimate page count by text length
    approx_pages = len(text) / 3000  # rough estimate
    
    return {
        'is_nitins': is_nitins,
        'has_cover_letter': has_cover_letter,
        'has_resume': has_resume,
        'approx_pages': round(approx_pages, 1),
        'word_count': len(text.split())
    }


def main():
    """Analyze specific files."""
    base_path = Path.home() / "Downloads" / "NitinResumes"
    
    files_to_check = [
        "Nitin Verma CL Kayak.pdf",
        "Nitin Verma Cover Letter Repligen.pdf",
        "Nitin Verma Cover Letter VelvetJobs.docx",
        "AiOfficerCofounderCLnCV.pdf",
        "CLandCV Liberty.pdf",
        "HexagonCLnCV.pdf",
        "Nitin Verma Daley And Associates.pdf",
        "Nitin Verma Resume Andiamo VP of Engineering.pdf",
        "Nitin Verma Resume D33P CTO.pdf",
        "Nitin Verma Resume SVP Toptal.pdf",
        "Nitin Verma.pdf",
        "NitinAlnylamCLandCV.pdf",
        "NitinMetaCLandCV.pdf",
        "NitinValtechCLandCV.pdf",
        "NitinVermaAndiamo.pdf",
        "NitinVermaMetricBio.pdf",
        "NitinWorkzoneCLandCV.pdf",
        "Resume202502061106.pdf",
        "AndiamoCTOCoverLetter.pdf",
        "AthenahealthVPCoverLetter.pdf",
        "CengageCoverLetter.pdf",
        "CompScienceCoverLetter.pdf",
        "EpamChiefTechAICoverLetter.pdf",
        "FormlabsCoverLetter.pdf",
        "IntuitAICoverLetter.pdf",
        "IronwoodCoverLetter.pdf",
        "MetricBioCoverLetter.pdf",
        "NitinResumeColumbiaUniv.doc",
        "RuralKingCoverLetter.pdf",
        "WaymoCoverLetter.pdf"
    ]
    
    print("Analyzing specific files by CONTENT:\n")
    print("=" * 80)
    
    for filename in files_to_check:
        file_path = base_path / filename
        
        if not file_path.exists():
            print(f"\n{filename}")
            print("  STATUS: FILE NOT FOUND")
            continue
        
        # Extract text
        if filename.endswith('.pdf'):
            text = extract_pdf_text(file_path)
        elif filename.endswith('.docx') or filename.endswith('.doc'):
            text = extract_docx_text(file_path)
        else:
            print(f"\n{filename}")
            print("  STATUS: UNSUPPORTED FORMAT")
            continue
        
        if text.startswith("ERROR"):
            print(f"\n{filename}")
            print(f"  STATUS: {text}")
            continue
        
        # Analyze content
        analysis = analyze_content(text)
        
        # Determine classification
        owner = "Nitin's" if analysis['is_nitins'] else "Other Person's"
        
        if analysis['has_cover_letter'] and analysis['has_resume']:
            doc_type = "BOTH (Cover Letter + Resume)"
        elif analysis['has_cover_letter']:
            doc_type = "Cover Letter Only"
        elif analysis['has_resume']:
            doc_type = "Resume Only"
        else:
            doc_type = "Other/Unclear"
        
        print(f"\n{filename}")
        print(f"  Owner: {owner}")
        print(f"  Type: {doc_type}")
        print(f"  Pages: ~{analysis['approx_pages']}, Words: {analysis['word_count']}")
        print("=" * 80)


if __name__ == "__main__":
    main()
