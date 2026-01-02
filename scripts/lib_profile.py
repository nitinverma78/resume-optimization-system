"""Shared library for parsing LinkedIn profiles (Steps 5 & 6)."""
import json,re,os
from pathlib import Path
from dataclasses import dataclass
from typing import List,Dict,NewType

# Domain Types (RL-book pattern)
CompanyName = NewType('CompanyName', str)
SkillName   = NewType('SkillName', str)
PatentText  = NewType('PatentText', str)
PubText     = NewType('PubText', str)

@dataclass(frozen=True)
class Experience:
    """Work experience entry."""
    company: str
    title: str
    duration: str
    location: str
    description: str
    achievements: List[str]

@dataclass(frozen=True)
class Education:
    """Education entry."""
    school: str
    degree: str
    field: str
    years: str

@dataclass(frozen=True)
class Profile:
    """Complete professional profile."""
    name: str
    headline: str
    summary: str
    contact: Dict[str, str]
    skills: List[str]
    experiences: List[Experience]
    education: List[Education]
    patents: List[str]
    publications: List[str]

def extract_sec(txt: str, start: str, end: str=None) -> str:
    """Extract text between section headers."""
    pat = f"{re.escape(start)}(.*?)({'(' + re.escape(end) + ')' if end else '$'})"
    m = re.search(pat, txt, re.DOTALL)
    return m.group(1).strip() if m else ""

def _parse_exp(txt: str, custom_cos: Dict[str,str]=None) -> List[Experience]:
    """Parse work experience section."""
    sec = extract_sec(txt, "Experience", "Education")
    exps = []
    
    cos = custom_cos or {"Example Corp": r"Example Corp\nTitle\n(.*?)(?=NextCompany|$)"}
    
    for co, pat in cos.items():
        m = re.search(pat, sec, re.DOTALL)
        if m:
            etxt = m.group(0).strip()
            lines = etxt.split('\n')
            title = lines[1] if len(lines) > 1 else "See details"
            dur_m = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}.*?(?:Present|\d{4}))', etxt[:200])
            dur = dur_m.group(1) if dur_m else "See parsed data"
            exps.append(Experience(company=co, title=title, duration=dur,
                                   location="", description=etxt, achievements=[]))
    return exps

def _parse_edu(txt: str, custom_edu: List[Dict]=None) -> List[Education]:
    """Parse education section."""
    sec = extract_sec(txt, "Education", "Page") or extract_sec(txt, "Education", None)
    edus = []
    
    if custom_edu:
        for item in custom_edu:
            kw1 = item.get('keyword', '')
            kw2 = item.get('keyword2', '')
            if kw1 in sec or kw2 in sec:
                edus.append(Education(school=item['school'], degree=item['degree'],
                                      field=item['field'], years=item['years']))
    elif "University" in sec:
        edus.append(Education(school="University Name", degree="Degree Name",
                              field="Field of Study", years="2010-2014"))
    return edus

def _merge_lines(txt: str) -> List[str]:
    """Merge lines for patents/publications."""
    items, cur = [], ""
    for line in txt.split('\n'):
        line = line.strip()
        if not line: continue
        if cur and not line[0].isupper(): cur += " " + line
        elif cur:
            items.append(cur)
            cur = line
        else: cur = line
    if cur: items.append(cur)
    return items

def parse_profile(raw: str, name: str=None) -> Profile:
    """Parse LinkedIn profile text into structured data."""
    name = name or os.getenv('USER_NAME', 'Your Name')
    
    # Load custom config
    cfg_path = Path(os.getenv('PARSING_CONFIG', Path(__file__).parent.parent/"profile-data"/"parsing_config.json"))
    cfg = {}
    if cfg_path.exists():
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f: cfg = json.load(f)
            print(f"Loaded custom parsing config from {cfg_path.name}")
        except Exception as e:
            print(f"Warning: Could not load config {cfg_path}: {e}")
    
    # Clean text
    raw = re.sub(r'\n\s*Page \d+ of \d+\s*\n', '\n', raw)
    raw = re.sub(r'Page \d+ of \d+', '', raw)

    # Name
    nm = re.search(rf"({re.escape(name)})", raw)
    nm = nm.group(1) if nm else name
    
    # Headline
    hl = re.search(rf"{re.escape(name)}\n(.*?)\n(?:Greater|Summary)", raw, re.DOTALL)
    hl = hl.group(1).strip().replace('\n', ' ') if hl else ""
    
    # Summary
    summ = extract_sec(raw, "Summary", "Experience").strip()
    
    # Contact
    contact = {}
    if em := re.search(r"([\w\.-]+@[\w\.-]+\.\w+)", raw): contact['email'] = em.group(1)
    if li := re.search(r"www\.linkedin\.com/in/([\w-]+)", raw): contact['linkedin'] = f"linkedin.com/in/{li.group(1)}"
    if ws := re.search(r"([\w-]+\.ai) \(Company\)", raw): contact['company_website'] = ws.group(1)
    
    # Skills
    sk_sec = extract_sec(raw, "Top Skills", "Publications")
    skills = [s.strip() for s in sk_sec.split('\n') if s.strip()]
    
    # Experience & Education using config
    exps = _parse_exp(raw, cfg.get('companies'))
    edus = _parse_edu(raw, cfg.get('education'))
    
    # Patents & Publications
    pats = _merge_lines(extract_sec(raw, "Patents", name))
    pubs = _merge_lines(extract_sec(raw, "Publications", "Patents"))
    
    return Profile(
        name=nm, headline=hl, summary=summ, contact=contact, skills=skills,
        experiences=exps, education=edus,
        patents=pats[:4], publications=pubs[:2]
    )
