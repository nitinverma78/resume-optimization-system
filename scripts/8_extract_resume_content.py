#!/usr/bin/env python3
"""Step 8: Extract Resume Content - Parse resumes into structured Knowledge Base."""
import json,os,re,pymupdf
from pathlib import Path
from dataclasses import dataclass
from typing import List,Dict,Any,NewType,Set

# Domain Types (RL-book pattern)
SectionName = NewType('SectionName', str)
BulletText  = NewType('BulletText', str)
Theme       = NewType('Theme', str)
CompanyName = NewType('CompanyName', str)

# Type Aliases
SectionContent = Dict[str, Dict[str, Any]]  # {'header': str, 'content': List[str]}
BulletInfo     = Dict[str, Any]             # {'text': str, 'tags': List[str]}
ExperienceBlock = Dict[str, Any]            # {'company': str, 'role': str, 'bullets': List}

@dataclass(frozen=True)
class ParsedResume:
    """Immutable parsed resume data."""
    source_file: str
    role_intent: str
    summary: str
    skills: Dict[str, List[str]]
    patents: tuple
    publications: tuple
    talks: tuple

# --- Section Patterns ---
SEC_PATTERNS = {
    "Summary":     r"(?i)^(SUMMARY|PROFILE|PROFESSIONAL SUMMARY|EXECUTIVE SUMMARY|.*LEADER|.*OFFICER|.*CONTACT)$",
    "Experience":  r"(?i)^(PROFESSIONAL EXPERIENCE|EXPERIENCE|WORK HISTORY|CAREER HIGHLIGHTS|RECENT EXPERIENCES|PRIOR EXPERIENCES|ENGAGEMENT)$",
    "Skills":      r"(?i)^(SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|AREAS OF EXPERTISE|TECHNICAL ARSENAL|CAPABILITIES|TECHNOLOGIES)$",
    "Education":   r"(?i)^(EDUCATION|ACADEMIC BACKGROUND)$",
    "Patents":     r"(?i)^(PATENTS|INVENTIONS)$",
    "Publications": r"(?i)^(PUBLICATIONS|SELECTED PUBLICATIONS)$",
    "Talks":       r"(?i)^(TALKS|PRESENTATIONS|INVITED TALKS|SPEAKING ENGAGEMENTS)$",
    "Awards":      r"(?i)^(AWARDS|HONORS|RECOGNITION)$"
}

# Skill keywords
HARD_KW = {'python','java','c++','sql','aws','cloud','pytorch','tensorflow','machine learning',
           'ai','nlp','robotics','algorithms','architecture','distributed systems','api','backend',
           'frontend','react','node','docker','kubernetes','linux','git','ci/cd'}
SOFT_KW = {'leadership','strategy','management','mentoring','communication','negotiation',
           'stakeholder','vision','roadmap','agile','scrum','budget','hiring','team building',
           'cross-functional','collaboration','business development','transformation'}

# Themes for bullet tagging
THEMES = {
    "Leadership": ['led','managed','hired','mentored','strategy','vision','budget','team','stakeholder'],
    "Technical Delivery": ['built','developed','architected','deployed','engineered','platform','system'],
    "Optimization": ['reduced','saved','improved','efficiency','optimized','cost','profit'],
    "Innovation": ['patent','research','paper','novel','state-of-the-art','cutting-edge'],
    "Product": ['roadmap','customer','launch','user','market','revenue']
}

RECENT_COS = ['manifold','aspen','tag','staples','investor']

def extract_pdf(fp: Path) -> str:
    try:
        doc = pymupdf.open(fp)
        txt = "".join(p.get_text()+"\n" for p in doc)
        return txt
    except Exception as e:
        print(f"Error reading {fp.name}: {e}")
        return ""

def identify_sections(lines: List[str]) -> Dict[str,Dict]:
    """Segment text into sections."""
    secs = {"Uncategorized": {'header': 'Start', 'content': []}}
    cur = "Uncategorized"
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        matched = None
        for cat, pat in SEC_PATTERNS.items():
            if len(line) < 60 and re.match(pat, line):
                matched = cat
                break
        
        if matched:
            cur = matched
            if cur not in secs: secs[cur] = {'header': line, 'content': []}
        else:
            secs[cur]['content'].append(line)
            
    return secs

def classify_skills(lines: List[str]) -> Dict[str,List[str]]:
    """Split skills into Hard/Soft buckets."""
    hard, soft, other = [], [], []
    for line in lines:
        line = line.strip()
        if not line: continue
        lo = line.lower()
        has_hard = any(k in lo for k in HARD_KW)
        has_soft = any(k in lo for k in SOFT_KW)
        is_sent  = len(line.split()) > 5 or ":" in line
        
        if   has_soft:         soft.append(line)
        elif has_hard:
            if is_sent: soft.append(line)
            else:       hard.append(line)
        else:                  other.append(line)
    return {'hard': hard, 'soft': soft, 'other': other}

def tag_bullet(txt: str) -> List[str]:
    lo = txt.lower()
    return [th for th, kw in THEMES.items() if any(k in lo for k in kw)]

def parse_exp(lines: List[str]) -> Dict[str,List[Dict]]:
    """Segment experience into Recent vs Earlier."""
    recent, earlier = [], []
    blk = {'company': 'Unknown', 'role': '', 'bullets': [], 'tags': set(), 'raw_text': []}
    
    all_cos = RECENT_COS + ['zulily','amazon','fico','dash','fair isaac']
    
    for line in lines:
        line = line.strip()
        if not line: continue
        lo = line.lower()
        
        # Detect company header
        det_co = ""
        if len(line) < 100:
            for co in all_cos:
                if co in lo:
                    det_co = co.capitalize()
                    break
        
        if det_co:
            # Save previous
            if blk['raw_text']:
                is_recent = any(r in blk['company'].lower() for r in RECENT_COS)
                (recent if is_recent else earlier).append(blk)
            blk = {'company': det_co, 'role': '', 'bullets': [], 'tags': set(), 'raw_text': [line]}
        else:
            blk['raw_text'].append(line)
            if line.startswith(('•','-','*')) or len(line) > 60:
                clean = re.sub(r'^[•\-\*]\s*', '', line).strip()
                tags = tag_bullet(clean)
                blk['bullets'].append({'text': clean, 'tags': tags})
                blk['tags'].update(tags)
            elif len(line) < 60 and not blk['role']:
                blk['role'] = line
    
    # Save last
    if blk['raw_text']:
        is_recent = any(r in blk['company'].lower() for r in RECENT_COS)
        (recent if is_recent else earlier).append(blk)
    
    # Serialize sets
    for b in recent + earlier: b['tags'] = list(b['tags'])
    return {'recent': recent, 'earlier': earlier}

def process_resume(fp: Path) -> Dict[str,Any]:
    """Process a single resume file."""
    txt = extract_pdf(fp)
    secs = identify_sections(txt.split('\n'))
    
    data = {
        "source_file": fp.name, "role_intent": "General", "summary": "",
        "skills": {}, "experience": {'recent':[], 'earlier':[]},
        "patents": [], "publications": [], "talks": []
    }
    
    if "Summary" in secs:
        s = secs["Summary"]
        data["role_intent"] = s['header']
        data["summary"] = "\n".join(s['content'])
    if "Skills" in secs:
        data["skills"] = classify_skills(secs["Skills"]['content'])
    if "Patents" in secs:      data["patents"] = secs["Patents"]['content']
    if "Publications" in secs: data["publications"] = secs["Publications"]['content']
    if "Talks" in secs:        data["talks"] = secs["Talks"]['content']
    if "Experience" in secs:   data["experience"] = parse_exp(secs["Experience"]['content'])
    
    return data

def main(
    cls_file: Path = Path(__file__).parent.parent/"data"/"supply"/"2_file_inventory.json",
    out_db: Path = Path(__file__).parent.parent/"data"/"supply"/"4_raw_extracted_content.json"
):
    """Main extraction loop."""
    cls_file = Path(os.getenv('CLASSIFIED_FILE', str(cls_file)))
    
    if not cls_file.exists():
        print(f"Error: {cls_file} not found.")
        return
        
    with open(cls_file, 'r') as f: inv = json.load(f)
        
    print("Extracting content from resumes...")
    
    db = []
    n = 0
    
    for cat in ['user_resumes', 'user_combined']:
        if cat not in inv: continue
        for finfo in inv[cat]:
            p = Path(finfo['path'])
            if not p.exists(): continue
            db.append(process_resume(p))
            n += 1
            print(".", end="", flush=True)
            
    print(f"\n\n✓ Content extraction complete! Processed {n} documents.")
    
    with open(out_db, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    print(f"  Database saved to: {out_db}")

if __name__ == "__main__": main()
