"""
Shared library for parsing LinkedIn profiles.
Contains data structures and parsing logic used by Step 5 and Step 6.
"""

import json, re, os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict


@dataclass
class Experience:
    """Work experience entry."""
    company: str
    title: str
    duration: str
    location: str
    description: str
    achievements: List[str]


@dataclass
class Education:
    """Education entry."""
    school: str
    degree: str
    field: str
    years: str


@dataclass
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


def extract_section(
    text: str,                # Full document text
    section_start: str,       # Section header to find
    next_section: str = None  # Next section header (optional)
) -> str:  # Extracted section text
    """Extract text between section headers."""
    pattern = f"{re.escape(section_start)}(.*?)({'(' + re.escape(next_section) + ')' if next_section else '$'})"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_experiences_section(
    text: str,  # Full LinkedIn profile text
    custom_companies: Dict[str, str] = None  # Optional custom patterns
) -> List[Experience]:  # List of parsed experiences
    """Parse work experience section."""
    exp_section = extract_section(text, "Experience", "Education")
    experiences = []
    
    # Use custom patterns if provided, otherwise generic defaults
    if custom_companies:
        companies = custom_companies
    else:
        companies = {
            "Example Corp": r"Example Corp\nTitle\n(.*?)(?=NextCompany|$)",
            "Another Company": r"Another Company\nTitle\n(.*?)(?=PreviousCompany|$)",
        }
    
    for company, pattern in companies.items():
        match = re.search(pattern, exp_section, re.DOTALL)
        if match:
            exp_text = match.group(0).strip()
            
            # extract title (usually 2nd line)
            lines = exp_text.split('\n')
            title = lines[1] if len(lines) > 1 else "See details"
            
            # extract duration (look for date patterns in first few lines)
            duration_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}.*?(?:Present|\d{4}))', exp_text[:200])
            duration = duration_match.group(1) if duration_match else "See parsed data"
            
            # full text without the company name header if possible
            description = exp_text
            
            experiences.append(Experience(
                company=company,
                title=title,
                duration=duration,
                location="",
                description=description,  # Full text!
                achievements=[]
            ))
    
    return experiences


def _parse_education_section(
    text: str,  # Full LinkedIn profile text
    custom_education: List[Dict] = None  # Optional custom patterns
) -> List[Education]:  # List of parsed education entries
    """Parse education section."""
    # Education is usually the last section, so next_section can be None (End of String)
    # But sometimes there are other sections.
    edu_section = extract_section(text, "Education", "Page")
    if not edu_section:
        # If Page keyword was removed or not found, try extracting until end of text
        edu_section = extract_section(text, "Education", None)

    education = []
    
    if custom_education:
        for item in custom_education:
            # Check if keyword(s) exist in section
            matches = item['keyword'] in edu_section
            if 'keyword2' in item:
                matches = matches or (item['keyword2'] in edu_section)
                
            if matches:
                education.append(Education(
                    school=item['school'],
                    degree=item['degree'],
                    field=item['field'],
                    years=item['years']
                ))
    else:
        # Example University 1
        if "University" in edu_section:
            education.append(Education(
                school="University Name",
                degree="Degree Name",
                field="Field of Study",
                years="2010-2014"
            ))
    
    return education


def parse_profile(
    raw_text: str,  # Raw text from LinkedIn PDF
    user_name: str = None  # User's full name (default: USER_NAME env var)
) -> Profile:  # Structured Profile object
    """Parse LinkedIn profile text into structured data."""
    # Get user name from env or parameter
    if user_name is None:
        user_name = os.getenv('USER_NAME', 'Your Name')  # Generic placeholder
    
    # Load custom parsing config if available
    config_path = Path(os.getenv('PARSING_CONFIG', Path(__file__).parent.parent / "profile-data" / "parsing_config.json"))
    parsing_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                parsing_config = json.load(f)
            print(f"Loaded custom parsing config from {config_path.name}")
        except Exception as e:
            print(f"Warning: Could not load config {config_path}: {e}")
            parsing_config = {}
    
    # Pre-clean text to remove artifacts
    raw_text = re.sub(r'\n\s*Page \d+ of \d+\s*\n', '\n', raw_text)
    raw_text = re.sub(r'Page \d+ of \d+', '', raw_text)

    # Extract basic info
    name_match = re.search(rf"({re.escape(user_name)})", raw_text)
    name = name_match.group(1) if name_match else user_name
    
    # Extract headline (the long title after name)
    headline_match = re.search(rf"{re.escape(user_name)}\n(.*?)\n(?:Greater|Summary)", raw_text, re.DOTALL)
    headline = headline_match.group(1).strip().replace('\n', ' ') if headline_match else ""
    
    # Extract summary
    summary_section = extract_section(raw_text, "Summary", "Experience")
    summary = summary_section.strip() if summary_section else ""
    
    # Extract contact info using pythonic patterns
    contact = {}
    if email_match := re.search(r"([\w\.-]+@[\w\.-]+\.\w+)", raw_text):
        contact['email'] = email_match.group(1)
    if linkedin_match := re.search(r"www\.linkedin\.com/in/([\w-]+)", raw_text):
        contact['linkedin'] = f"linkedin.com/in/{linkedin_match.group(1)}"
    if website_match := re.search(r"([\w-]+\.ai) \(Company\)", raw_text):
        contact['company_website'] = website_match.group(1)
    
    # Extract top skills
    skills_section = extract_section(raw_text, "Top Skills", "Publications")
    skills = [s.strip() for s in skills_section.split('\n') if s.strip()]
    
    # Parse experiences
    experiences = _parse_experiences_section(raw_text, parsing_config.get('companies'))
    
    # Parse education
    education = _parse_education_section(raw_text, parsing_config.get('education'))
    
    # Extract patents - with smart line merging
    patents_section = extract_section(raw_text, "Patents", user_name)
    patents = []
    current_patent = ""
    for line in patents_section.split('\n'):
        line = line.strip()
        if not line: continue
        # If line starts with capital and we have a previous short line, might be continuation
        if current_patent and not line[0].isupper():
             current_patent += " " + line
        elif current_patent:
             patents.append(current_patent)
             current_patent = line
        else:
             current_patent = line
    if current_patent: patents.append(current_patent)
    
    # Extract publications - with smart line merging
    pubs_section = extract_section(raw_text, "Publications", "Patents")
    publications = []
    current_pub = ""
    for line in pubs_section.split('\n'):
        line = line.strip()
        if not line: continue
        
        # Heuristic: Uppercase start loosely implies new item in this formatting
        if current_pub and not line[0].isupper():
             current_pub += " " + line
        elif current_pub:
             publications.append(current_pub)
             current_pub = line
        else:
             current_pub = line
    if current_pub: publications.append(current_pub)
    
    return Profile(
        name=name,
        headline=headline,
        summary=summary,
        contact=contact,
        skills=skills,
        experiences=experiences,
        education=education,
        patents=patents[:4] if len(patents) > 4 else patents,  # Limit to actual patents
        publications=publications[:2] if len(publications) > 2 else publications,
    )
