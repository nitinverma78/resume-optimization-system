#!/usr/bin/env python3
"""
Step 8: Extract Resume Content (Content-Aware)

Parses all classified resumes to build a structured Knowledge Base.
Implements "Content-Aware" logic:
1. Captures Summary Header as "Target Role" (metadata).
2. Segments lists into Hard/Soft skills based on keywords.
3. Separates IP (Patents/Talks) from general text.
4. Aggregates extraction into `data/resume_content_db.json`.
"""

import json, os, re
import pymupdf
from pathlib import Path
from typing import List, Dict, Any

# --- Configuration ---

# Regex patterns for section detection
# We use flexible patterns to catch variations found in Step 7
SECTION_PATTERNS = {
    "Summary": r"(?i)^(SUMMARY|PROFILE|PROFESSIONAL SUMMARY|EXECUTIVE SUMMARY|.*LEADER|.*OFFICER|.*CONTACT)$",
    "Experience": r"(?i)^(PROFESSIONAL EXPERIENCE|EXPERIENCE|WORK HISTORY|CAREER HIGHLIGHTS|RECENT EXPERIENCES|PRIOR EXPERIENCES|ENGAGEMENT)$",
    "Skills": r"(?i)^(SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|AREAS OF EXPERTISE|TECHNICAL ARSENAL|CAPABILITIES|TECHNOLOGIES)$",
    "Education": r"(?i)^(EDUCATION|ACADEMIC BACKGROUND)$",
    "Patents": r"(?i)^(PATENTS|INVENTIONS)$",
    "Publications": r"(?i)^(PUBLICATIONS|SELECTED PUBLICATIONS)$",
    "Talks": r"(?i)^(TALKS|PRESENTATIONS|INVITED TALKS|SPEAKING ENGAGEMENTS)$",
    "Awards": r"(?i)^(AWARDS|HONORS|RECOGNITION)$"
}

# Keywords to distinguish Hard vs Soft skills if they are in the same block
HARD_SKILL_KEYWORDS = {
    'python', 'java', 'c++', 'sql', 'aws', 'cloud', 'pytorch', 'tensorflow', 'machine learning', 
    'ai', 'nlp', 'robotics', 'algorithms', 'architecture', 'distributed systems', 'api', 'backend',
    'frontend', 'react', 'node', 'docker', 'kubernetes', 'linux', 'git', 'ci/cd'
}

SOFT_SKILL_KEYWORDS = {
    'leadership', 'strategy', 'management', 'mentoring', 'communication', 'negotiation', 
    'stakeholder', 'vision', 'roadmap', 'agile', 'scrum', 'budget', 'hiring', 'team building',
    'cross-functional', 'collaboration', 'business development', 'transformation'
}

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Read text from PDF."""
    try:
        doc = pymupdf.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading {pdf_path.name}: {e}")
        return ""

def identify_sections(lines: List[str]) -> Dict[str, Dict]:
    """
    Segment text into sections.
    Returns: { 'SectionName': {'header': 'Original Header', 'content': ['line1', 'line2']} }
    """
    sections = {}
    current_section = "Uncategorized"
    current_header = "Start"
    sections[current_section] = {'header': current_header, 'content': []}
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check if line is a header
        matched_category = None
        for category, pattern in SECTION_PATTERNS.items():
            # Heuristic: Headers are usually short and match the pattern
            if len(line) < 60 and re.match(pattern, line):
                matched_category = category
                break
        
        if matched_category:
            current_section = matched_category
            current_header = line # Capture the exact text (e.g. "AI TECHNOLOGY LEADER")
            if current_section not in sections:
                sections[current_section] = {'header': current_header, 'content': []}
        else:
            sections[current_section]['content'].append(line)
            
    return sections

def classify_skills(skill_lines: List[str]) -> Dict[str, List[str]]:
    """
    Split skill lines into Hard/Soft buckets based on content.
    Refined logic: Sentences describing outcomes are usually 'Soft/Strategic', 
    even if they mention tech. 'Hard' is reserved for lists of tools.
    """
    hard = []
    soft = []
    uncategorized = []
    
    for line in skill_lines:
        line = line.strip()
        if not line: continue
        line_lower = line.lower()
        
        # Check for keywords
        has_hard_keyword = any(k in line_lower for k in HARD_SKILL_KEYWORDS)
        has_soft_keyword = any(k in line_lower for k in SOFT_SKILL_KEYWORDS)
        
        # Heuristic: Lists of tools are Hard. Sentences are Soft/Strategic.
        # If it contains "Leadership", "Management", "Strategy", it's Soft dominant.
        is_sentence = len(line.split()) > 5 or ":" in line
        
        if has_soft_keyword:
            soft.append(line)
        elif has_hard_keyword:
            if is_sentence:
                # E.g. "MLOps: Accelerate lifecycle..." -> Soft/Strategic (Process)
                soft.append(line)
            else:
                # E.g. "Python, Java, C++" -> Hard
                hard.append(line)
        else:
            uncategorized.append(line)
            
    return {'hard': hard, 'soft': soft, 'other': uncategorized}

def tag_bullet_theme(text: str) -> List[str]:
    """Tag a bullet point with themes."""
    tags = []
    text_lower = text.lower()
    
    # Theme map
    THEMES = {
        "Leadership": ['led', 'managed', 'hired', 'mentored', 'strategy', 'vision', 'budget', 'team', 'stakeholder'],
        "Technical Delivery": ['built', 'developed', 'architected', 'deployed', 'engineered', 'platform', 'system'],
        "Optimization": ['reduced', 'saved', 'improved', 'efficiency', 'optimized', 'cost', 'profit'],
        "Innovation": ['patent', 'research', 'paper', 'novel', 'state-of-the-art', 'cutting-edge'],
        "Product": ['roadmap', 'customer', 'launch', 'user', 'market', 'revenue']
    }
    
    for theme, keywords in THEMES.items():
        if any(k in text_lower for k in keywords):
            tags.append(theme)
            
    return tags

def parse_experience_blocks(exp_lines: List[str]) -> Dict[str, List[Dict]]:
    """
    Segment experience into Recent vs Earlier.
    Recent: Manifold, TAG (Aspen), Staples
    Earlier: Zulily, Amazon, FICO (and others)
    """
    recent = []
    earlier = []
    
    current_block = {'company': 'Unknown', 'role': '', 'bullets': [], 'tags': set(), 'raw_text': []}
    
    # Specific company detection
    RECENT_COMPANIES = ['manifold', 'aspen', 'tag', 'staples', 'investor']
    
    for line in exp_lines:
        line = line.strip()
        if not line: continue
        
        # Detect start of a new company block (Heuristic: Date + Name, or known name)
        # We look for the company name in the line
        line_lower = line.lower()
        is_company_header = False
        detected_company = ""
        
        if len(line) < 100:
            # Check for known companies
            all_companies = RECENT_COMPANIES + ['zulily', 'amazon', 'fico', 'dash', 'fair isaac']
            for co in all_companies:
                if co in line_lower:
                    is_company_header = True
                    detected_company = co.capitalize() 
                    break
        
        if is_company_header and detected_company:
            # Save previous block
            if current_block['raw_text']:
                # Decide where to put it
                is_recent_block = any(r in current_block['company'].lower() for r in RECENT_COMPANIES)
                if is_recent_block:
                    recent.append(current_block)
                else:
                    earlier.append(current_block)
            
            # Start new block
            current_block = {'company': detected_company, 'role': '', 'bullets': [], 'tags': set(), 'raw_text': [line]}
        else:
            # Add to current block
            current_block['raw_text'].append(line)
            # Check if it's a bullet
            if line.startswith(('•', '-', '*')) or len(line) > 60:
                clean_bullet = re.sub(r'^[•\-\*]\s*', '', line).strip()
                tags = tag_bullet_theme(clean_bullet)
                current_block['bullets'].append({'text': clean_bullet, 'tags': tags})
                current_block['tags'].update(tags)
            elif len(line) < 60 and not current_block['role']:
                # Likely role title
                current_block['role'] = line

    # Save last block
    if current_block['raw_text']:
        is_recent_block = any(r in current_block['company'].lower() for r in RECENT_COMPANIES)
        if is_recent_block:
            recent.append(current_block)
        else:
            earlier.append(current_block)
            
    # Serialize sets
    for block in recent + earlier:
        block['tags'] = list(block['tags'])

    return {'recent': recent, 'earlier': earlier}

def process_resume(file_path: Path) -> Dict[str, Any]:
    """Process a single resume file."""
    text = extract_text_from_pdf(file_path)
    lines = text.split('\n')
    
    # 1. Segment text
    raw_sections = identify_sections(lines)
    
    parsed_data = {
        "source_file": file_path.name,
        "role_intent": "General", # Default
        "summary": "",
        "skills": {},
        "experience": {'recent': [], 'earlier': []},
        "patents": [],
        "publications": [],
        "talks": []
    }
    
    # 2. Process Summary & Intent
    if "Summary" in raw_sections:
        sec = raw_sections["Summary"]
        parsed_data["role_intent"] = sec['header'] # "AI TECHNOLOGY LEADER"
        parsed_data["summary"] = "\n".join(sec['content'])
        
    # 3. Process Skills
    if "Skills" in raw_sections:
        sec = raw_sections["Skills"]
        parsed_data["skills"] = classify_skills(sec['content'])
        
    # 4. Process IP
    if "Patents" in raw_sections:
        parsed_data["patents"] = raw_sections["Patents"]['content']
    if "Publications" in raw_sections:
        parsed_data["publications"] = raw_sections["Publications"]['content']
    if "Talks" in raw_sections:
        parsed_data["talks"] = raw_sections["Talks"]['content']
        
    # 5. Process Experience - Content Aware Segmentation
    if "Experience" in raw_sections:
        parsed_data["experience"] = parse_experience_blocks(raw_sections["Experience"]['content'])

    return parsed_data

def main(
    classified_file: Path = Path(__file__).parent.parent / "data" / "supply" / "2_file_inventory.json",
    output_db: Path = Path(__file__).parent.parent / "data" / "supply" / "4_raw_extracted_content.json"
):
    """Main extraction loop."""
    # Env override
    classified_file = Path(os.getenv('CLASSIFIED_FILE', str(classified_file)))
    
    if not classified_file.exists():
        print(f"Error: {classified_file} not found.")
        return
        
    with open(classified_file, 'r') as f:
        inventory = json.load(f)
        
    print("Extracting content from resumes...")
    
    db = []
    processed_count = 0
    
    categories = ['user_resumes', 'user_combined']
    for cat in categories:
        if cat not in inventory: continue
        
        for file_info in inventory[cat]:
            path = Path(file_info['path'])
            if not path.exists(): continue
            
            data = process_resume(path)
            db.append(data)
            processed_count += 1
            print(".", end="", flush=True)
            
    print(f"\n\n✓ Content extraction complete! Processed {processed_count} documents.")
    
    with open(output_db, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
        
    print(f"  Database saved to: {output_db}")

if __name__ == "__main__":
    main()
