#!/usr/bin/env python3
"""
Phase 1.2: Content-Based File Classifier (FINAL VERSION)
Fixed based on user feedback:
- Ownership: Checks for user's name via USER_NAME environment variable
- Support: PPTX and old .doc files
- Detection: Better distinguish presentations vs resumes
"""

import json, re, subprocess, os
from pathlib import Path
from typing import List, Dict, Tuple, NewType
from pydantic import BaseModel
import pymupdf
from docx import Document
from pptx import Presentation

# Type aliases for clarity
FilePath = NewType('FilePath', Path)
Category = NewType('Category', str)
Reason = NewType('Reason', str)
TextContent = NewType('TextContent', str)


class ClassifiedFiles(BaseModel):
    """Model for classified file categories."""    
    class Config:
        frozen = True  # Make immutable
    
    user_resumes: List[Dict]
    user_cover_letters: List[Dict]
    user_combined: List[Dict]
    other_resumes: List[Dict]
    tracking_files: List[Dict]
    other: List[Dict]


def extract_text_from_pdf(
    file_path: FilePath  # Path to PDF file
) -> TextContent:  # Extracted text in lowercase
    """Extract text from PDF."""
    try:
        doc = pymupdf.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.lower()
    except Exception as e:
        print(f"  Warning: Could not read PDF {file_path.name}: {e}")
        return ""


def extract_text_from_docx(
    file_path: FilePath  # Path to DOCX file
) -> TextContent:  # Extracted text in lowercase
    """Extract text from DOCX file."""
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.lower()
    except Exception as e:
        print(f"  Warning: Could not read DOCX {file_path.name}: {e}")
        return ""


def extract_text_from_old_doc(file_path: Path) -> str:
    """Extract text from old .doc file using textutil (Mac) or antiword."""
    try:
        # Try textutil first (Mac built-in)
        result = subprocess.run(
            ['textutil', '-convert', 'txt', '-stdout', str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.lower()
        
        # Fallback: try reading as plain text (sometimes works)
        with open(file_path, 'rb') as f:
            raw = f.read()
            # Extract readable ASCII text
            text = ''.join(chr(b) if 32 <= b < 127 else ' ' for b in raw)
            return text.lower()
    except Exception as e:
        print(f"  Warning: Could not read old .doc {file_path.name}: {e}")
        return ""


def extract_text_from_pptx(file_path: Path) -> str:
    """Extract text from PPTX file."""
    try:
        prs = Presentation(file_path)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text.lower()
    except Exception as e:
        print(f"  Warning: Could not read PPTX {file_path.name}: {e}")
        return ""


def is_user_document(
    text: str,       # Document text content (lowercase)
    filename: str,   # Document filename  
    user_name: str = None  # User's full name (default: USER_NAME env var)
) -> bool:  # True if document belongs to user
    """Check if document belongs to user (name in content OR filename)."""
    # Get user name from env or parameter
    if user_name is None:
        user_name = os.getenv('USER_NAME', 'YOUR_NAME')  # Generic placeholder
    
    # Normalize for search
    user_lower = user_name.lower()
    user_compact = user_lower.replace(' ', '')
    
    # Check filename
    filename_lower = filename.lower()
    has_name_in_filename = user_compact in filename_lower.replace(' ', '')
    
    # Check content
    has_name_in_content = user_lower in text
    
    return has_name_in_filename or has_name_in_content


def is_cover_letter(
    text: str  # Document text content (lowercase)
) -> bool:  # True if document contains cover letter indicators
    """Determine if document contains a cover letter."""
    cl_indicators = [
        r'dear\s+(?:hiring|recruiter|manager|team)',
        r'i\s+am\s+writing\s+to\s+express',
        r'i\s+am\s+(?:excited|pleased|thrilled)\s+to\s+apply',
        r'sincerely',
        r'best\s+regards',
        r'thank\s+you\s+for\s+(?:considering|your\s+time)',
        r'i\s+would\s+welcome\s+the\s+opportunity',
        r'i\s+look\s+forward\s+to',
        r'cover\s+letter',
        r'enthusiastic\s+about.*opportunity',
        r'interest\s+in.*position'
    ]
    
    matches = sum(1 for pattern in cl_indicators if re.search(pattern, text))
    return matches >= 1


def is_resume(
    text: str  # Document text content (lowercase)
) -> bool:  # True if document has resume structure
    """Determine if document contains a resume using STRICT pattern matching."""
    # Check for resume section keywords
    resume_sections = [
        r'\bexperience\b',
        r'\beducation\b',
        r'\bskills\b',
        r'professional\s+summary',
        r'accomplishments',
        r'\bwork\s+history\b',
        r'\bemployment\b',
        r'technical\s+(?:skills|arsenal|expertise)',
        r'core\s+capabilities'
    ]
    section_count = sum(1 for pattern in resume_sections if re.search(pattern, text))
    
    # Check for actual resume PATTERNS (not just keywords)
    resume_patterns = {
        # Date ranges (2020-2023, 2020 - Present, etc.)
        'has_date_ranges': bool(re.search(r'(?:19|20)\d{2}\s*[-–—]\s*(?:(?:19|20)\d{2}|present|current)', text)),
        
        # Job titles with common patterns
        'has_job_titles': bool(re.search(r'\b(?:vp|vice president|director|manager|chief|lead|senior|sr|engineer|scientist|analyst|specialist)\b', text)),
        
        # Bullet points (multiple)
        'has_bullets': text.count('•') + text.count('- ') + text.count('* ') > 5,
        
        # Company indicators (worked at, at company)
        'has_companies': bool(re.search(r'\b(?:at\s+\w+|worked\s+at|employed\s+by)\b', text)),
        
        # Achievement metrics (%, $, numbers with context)
        'has_metrics': bool(re.search(r'(?:\$[\d,]+[kmb]?|\d+%|\d+\+\s+(?:years|people|projects))', text)),
    }
    
    pattern_count = sum(resume_patterns.values())
    
    # Need BOTH: 3+ section keywords AND 2+ resume patterns
    # This filters out presentations and cover letters that just mention "experience"
    return section_count >= 3 and pattern_count >= 2


def is_presentation(
    text: str,      # Document text content (lowercase)
    filename: str   # Document filename
) -> bool:  # True if document is a presentation
    """Determine if document is a presentation (not a resume)."""
    # For PPTX files specifically
    if filename.lower().endswith(('.ppt', '.pptx')):
        # If it has strong resume patterns, it's a resume in PPTX format
        if is_resume(text):
            return False
        # Otherwise, it's likely a presentation
        return True
    
    # For other file types (PDF, DOCX), only classify as presentation
    # if it has strong presentation indicators AND lacks resume structure
    # NOTE: We're very conservative here to avoid misclassifying resumes
    presentation_keywords = [
        r'\bslide\s*\d+',  # "Slide 1", "Slide 2"
        r'\bpresentation\b',
        r'\bagenda\b',
        r'\bconference\b',
        r'\bsummit\b',
        r'\bworkshop\b',
    ]
    
    has_presentation_kw = sum(1 for pattern in presentation_keywords if re.search(pattern, text))
    
    # Only classify as presentation if has 3+ strong indicators AND not a resume
    # This is very conservative to avoid false positives
    if has_presentation_kw >= 3 and not is_resume(text):
        return True
    
    return False


def is_other_persons_resume(text: str) -> bool:
    """Check if it's someone else's resume."""
    other_names = [
        r'patrick\s+moseley',
        r'russ\s+kasymov',
    ]
    
    for pattern in other_names:
        if re.search(pattern, text):
            return True
    
    return False


def classify_file_by_content(file_info: Dict) -> Tuple[str, str]:
    """Classify a file by analyzing its content."""
    if file_info['is_directory']:
        return 'other', 'directory'
    
    file_path = Path(file_info['path'])
    name = file_info['name']
    ext = file_info['extension']
    
    # Handle tracking files (by extension and name)
    if ext in ['.xlsx', '.csv']:
        tracking_keywords = ['search', 'log', 'track', 'companies', 'contacts', 'firms']
        if any(kw in name.lower() for kw in tracking_keywords):
            return 'tracking_file', 'spreadsheet with tracking keywords'
        return 'other', f'spreadsheet without clear purpose'
    
    # Skip unsupported file types
    if ext not in ['.pdf', '.docx', '.doc', '.pptx', '.txt']:
        return 'other', f'unsupported file type {ext}'
    
    # Extract text content - aligned for clarity
    text = ""
    if   ext == '.pdf':  text = extract_text_from_pdf(file_path)
    elif ext == '.docx': text = extract_text_from_docx(file_path)
    elif ext == '.doc':  text = extract_text_from_old_doc(file_path)
    elif ext == '.pptx': text = extract_text_from_pptx(file_path)
    elif ext == '.txt':
        try: text = file_path.read_text(encoding='utf-8').lower()
        except: pass
    
    if not text:
        return 'other', 'could not extract text'
    
    # Check if it's someone else's resume first
    if is_other_persons_resume(text):
        return 'other_resume', 'identified as another person\'s resume'
    
    # Check if it belongs to user (SIMPLIFIED: just need name)
    is_users = is_user_document(text, name)
    
    if not is_users:
        # Not user's document - check if it's a generic resume/CV
        if is_resume(text):
            return 'other_resume', 'resume structure but not user\'s'
        return 'other', 'not identified as user\'s document'
    
    # It's user's document - check if it's a presentation first
    if is_presentation(text, name):
        return 'other', 'user\'s presentation (not resume/CV)'
    
    # Determine type: resume, cover letter, or both
    has_cl = is_cover_letter(text)
    has_resume = is_resume(text)
    word_count = len(text.split())
    
    if has_cl and has_resume:
        # Cover letters can trigger resume detection because they mention
        # "experience", "skills", job titles, etc.
        # Use word count to distinguish:
        # - Cover letters: typically < 600 words
        # - Combined docs: typically > 600 words
        if word_count < 600:
            return 'user_cover_letter', 'user\'s cover letter (too short to be combined)'
        else:
            return 'user_combined', 'user\'s document with both resume and cover letter'
    elif has_cl:
        return 'user_cover_letter', 'user\'s cover letter only'
    elif has_resume:
        return 'user_resume', 'user\'s resume only'
    else:
        # If we're confident it's user's but unclear structure, default to resume
        return 'user_resume', 'user\'s document (structure unclear, defaulting to resume)'


def classify_files_from_inventory(
    inventory_path: Path  # Path to file_inventory.json
) -> ClassifiedFiles:  # ClassifiedFiles object with categorized files
    """Classify all files from inventory using content analysis."""
    with open(inventory_path, 'r', encoding='utf-8') as f:
        inventory = json.load(f)
    
    classified = {
        'user_resumes': [],
        'user_cover_letters': [],
        'user_combined': [],
        'other_resumes': [],
        'tracking_files': [],
        'other': []
    }
    
    print(f"Analyzing {len(inventory['files'])} files...\n")
    
    for idx, file_info in enumerate(inventory['files'], 1):
        if idx % 20 == 0:
            print(f"  Processed {idx}/{len(inventory['files'])} files...")
        
        category, reason = classify_file_by_content(file_info)
        
        # Add reason to file info for debugging
        file_info['classification_reason'] = reason
        
        # Aligned categorization for clarity
        if   category == 'user_resume':       classified['user_resumes'].append(file_info)
        elif category == 'user_cover_letter': classified['user_cover_letters'].append(file_info)
        elif category == 'user_combined':     classified['user_combined'].append(file_info)
        elif category == 'other_resume':      classified['other_resumes'].append(file_info)
        elif category == 'tracking_file':     classified['tracking_files'].append(file_info)
        else:                                 classified['other'].append(file_info)
    
    return ClassifiedFiles(**classified)


def main(
    inventory_file: Path = Path(__file__).parent.parent / "data" / "file_inventory.json",  # Input inventory
    output_file: Path = Path(__file__).parent.parent / "data" / "classified_files.json",  # Output classified
    user_name: str = None  # User's full name for ownership detection (default: USER_NAME env var)
):
    """Main execution."""
    # Allow environment variables to override defaults
    inventory_file = Path(os.getenv('INVENTORY_FILE', str(inventory_file)))
    output_file = Path(os.getenv('CLASSIFIED_FILE', str(output_file)))
    user_name = os.getenv('USER_NAME', user_name)  # Get from env if not provided
    
    if not inventory_file.exists():
        print(f"Error: File inventory not found at {inventory_file}")
        print("Please run 1_scan_resume_folder.py first.")
        return
    
    print("Classifying files using FINAL IMPROVED CONTENT ANALYSIS...")
    print("Now with: PPTX support, old .doc support, better ownership detection\n")
    
    classified = classify_files_from_inventory(inventory_file)
    
    # Save classification results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(classified.model_dump(), f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n✓ Classification complete!")
    print(f"✓ Saved to: {output_file}\n")
    
    print("Classification Summary:")
    print(f"  User Resumes (resume only): {len(classified.user_resumes)} files")
    print(f"  User Cover Letters (CL only): {len(classified.user_cover_letters)} files")
    print(f"  User Combined (Resume + CL): {len(classified.user_combined)} files")
    print(f"  Other Resumes: {len(classified.other_resumes)} files")
    print(f"  Tracking Files: {len(classified.tracking_files)} files")
    print(f"  Other Files: {len(classified.other)} files")
    
    print(f"\n📊 Total User Documents: {len(classified.user_resumes) + len(classified.user_cover_letters) + len(classified.user_combined)}")


if __name__ == "__main__":
    main()
