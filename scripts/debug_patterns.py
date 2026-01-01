#!/usr/bin/env python3
"""Debug why specific files are misclassified."""

import pymupdf, re, os
from pathlib import Path

def analyze_resume_patterns(file_path: Path):
    """Show exactly what patterns are detected."""
    
    doc = pymupdf.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    text = text.lower()
    
    print(f"\n{'='*70}")
    print(f"File: {file_path.name}")
    print(f"{'='*70}")
    print(f"Word count: {len(text.split())}")
    
    # Section keywords
    resume_sections = {
        'experience': bool(re.search(r'\bexperience\b', text)),
        'education': bool(re.search(r'\beducation\b', text)),
        'skills': bool(re.search(r'\bskills\b', text)),
        'professional_summary': bool(re.search(r'professional\s+summary', text)),
        'accomplishments': bool(re.search(r'accomplishments', text)),
        'work_history': bool(re.search(r'\bwork\s+history\b', text)),
        'employment': bool(re.search(r'\bemployment\b', text)),
        'technical': bool(re.search(r'technical\s+(?:skills|arsenal|expertise)', text)),
        'core_capabilities': bool(re.search(r'core\s+capabilities', text)),
    }
    section_count = sum(resume_sections.values())
    
    # Resume patterns
    resume_patterns = {
        'has_date_ranges': bool(re.search(r'(?:19|20)\d{2}\s*[-–—]\s*(?:(?:19|20)\d{2}|present|current)', text)),
        'has_job_titles': bool(re.search(r'\b(?:vp|vice president|director|manager|chief|lead|senior|sr|engineer|scientist|analyst|specialist)\b', text)),
        'has_bullets': text.count('•') + text.count('- ') + text.count('* ') > 5,
        'has_companies': bool(re.search(r'\b(?:at\s+\w+|worked\s+at|employed\s+by)\b', text)),
        'has_metrics': bool(re.search(r'(?:\$[\d,]+[kmb]?|\d+%|\d+\+\s+(?:years|people|projects))', text)),
    }
    pattern_count = sum(resume_patterns.values())
    
    # Cover letter indicators
    cl_indicators = {
        'dear': bool(re.search(r'dear\s+(?:hiring|recruiter|manager|team)', text)),
        'i_am_writing': bool(re.search(r'i\s+am\s+writing\s+to\s+express', text)),
        'excited_to_apply': bool(re.search(r'i\s+am\s+(?:excited|pleased|thrilled)\s+to\s+apply', text)),
        'sincerely': bool(re.search(r'sincerely', text)),
        'best_regards': bool(re.search(r'best\s+regards', text)),
        'thank_you': bool(re.search(r'thank\s+you\s+for\s+(?:considering|your\s+time)', text)),
        'look_forward': bool(re.search(r'i\s+look\s+forward\s+to', text)),
    }
    cl_count = sum(cl_indicators.values())
    
    # Presentation indicators
    pres_indicators = {
        'slide': bool(re.search(r'\bslide\s*\d+', text)),
        'presentation': bool(re.search(r'\bpresentation\b', text)),
        'agenda': bool(re.search(r'\bagenda\b', text)),
        'conference': bool(re.search(r'\bconference\b', text)),
        'talk': bool(re.search(r'\btalk\b', text)),
        'overview': bool(re.search(r'overview', text)),
    }
    pres_count = sum(pres_indicators.values())
    
    print(f"\nSECTION KEYWORDS ({section_count}/9):")
    for k, v in resume_sections.items():
        if v:
            print(f"  ✓ {k}")
    
    print(f"\nRESUME PATTERNS ({pattern_count}/5):")
    for k, v in resume_patterns.items():
        print(f"  {'✓' if v else '✗'} {k}")
    
    print(f"\nCOVER LETTER INDICATORS ({cl_count}/7):")
    for k, v in cl_indicators.items():
        if v:
            print(f"  ✓ {k}")
    
    print(f"\nPRESENTATION INDICATORS ({pres_count}/6):")
    for k, v in pres_indicators.items():
        if v:
            print(f"  ✓ {k}")
    
    print(f"\nCLASSIFICATION LOGIC:")
    is_resume_strict = section_count >= 3 and pattern_count >= 2
    has_cl = cl_count >= 1
    is_pres = pres_count >= 2 and not is_resume_strict
    
    print(f"  - is_resume (strict): {is_resume_strict} (needs 3+ sections AND 2+ patterns)")
    print(f"  - has_cover_letter: {has_cl} (needs 1+ indicator)")
    print(f"  - is_presentation: {is_pres} (needs 2+ indicators AND not resume)")
    
    if has_cl and is_resume_strict:
        print(f"  → RESULT: user_combined")
    elif has_cl:
        print(f"  → RESULT: user_cover_letter")
    elif is_resume_strict:
        print(f"  → RESULT: user_resume")
    elif is_pres:
        print(f"  → RESULT: other (presentation)")
    else:
        print(f"  → RESULT: user_resume (default)")


def main(
    base_path: Path = Path.home() / "Downloads" / "NitinResumes"  # Resume folder
):
    """Debug pattern detection."""
    # Allow environment variable override
    base_path = Path(os.getenv('RESUME_FOLDER', str(base_path)))
    
    files_to_debug = [
        "EnterpriseAgenticAI.pdf",
        "AspenDentalCoverLetter.pdf",
        "TheRealRealCoverLetter.pdf",
    ]
    
    for filename in files_to_debug:
        file_path = base_path / filename
        if file_path.exists():
            analyze_resume_patterns(file_path)
        else:
            print(f"\n❌ {filename}: FILE NOT FOUND")

if __name__ == "__main__":
    main()
