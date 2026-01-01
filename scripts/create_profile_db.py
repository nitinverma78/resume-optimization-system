#!/usr/bin/env python3
"""
Create a structured profile database from LinkedIn PDF.
Extracts experiences, skills, education, and achievements into searchable format.
"""

import json, re
from pathlib import Path
from dataclasses import dataclass,asdict
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


def parse_profile(
    raw_text: str  # Raw text from LinkedIn PDF
) -> Profile:  # Structured Profile object
    """Parse LinkedIn profile text into structured data."""
    # Extract basic info
    name_match = re.search(r"(Nitin Verma)", raw_text)
    name = name_match.group(1) if name_match else ""
    
    # Extract headline (the long title after name)
    headline_match = re.search(r"Nitin Verma\n(.*?)\n(?:Greater Boston|Summary)", raw_text, re.DOTALL)
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
    
    # Parse experiences (simplified - would need more sophisticated parsing)
    experiences = _parse_experiences_section(raw_text)
    
    # Parse education
    education = _parse_education_section(raw_text)
    
    # Extract patents
    patents_section = extract_section(raw_text, "Patents", "Nitin Verma")
    patents = [p.strip() for p in patents_section.split('\n') if p.strip() and len(p.strip()) > 10]
    
    # Extract publications
    pubs_section = extract_section(raw_text, "Publications", "Patents")
    publications = [p.strip() for p in pubs_section.split('\n') if p.strip() and len(p.strip()) > 10]
    
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


def _parse_experiences_section(
    text: str  # Full LinkedIn profile text
) -> List[Experience]:  # List of parsed experiences
    """Parse work experience section."""
    exp_section = extract_section(text, "Experience", "Education")
    experiences = []
    
    # Simple company extraction (would need refinement for production)
    companies = {
        "Manifold Systems": r"Manifold Systems\nCo-Founder\n(.*?)(?=TAG|$)",
        "TAG - The Aspen Group": r"TAG - The Aspen Group\nVP Tech, AI & Innovation\n(.*?)(?=Staples|$)",
        "Staples": r"Staples\n9 years.*?(?=Zulily|$)",
        "Zulily": r"Zulily\nSr Customer Programs Manager\n(.*?)(?=Amazon|$)",
        "Amazon": r"Amazon\n7 years.*?(?=FICO|$)",
        "FICO": r"FICO®\n5 years.*?(?=Education|$)",
    }
    
    for company, pattern in companies.items():
        match = re.search(pattern, exp_section, re.DOTALL)
        if match:
            # Extract basic details (simplified)
            exp_text = match.group(0)
            experiences.append(Experience(
                company=company,
                title="Multiple roles" if "years" in exp_text[:50] else "See details",
                duration="See parsed data",
                location="",
                description=exp_text[:500],  # First 500 chars as summary
                achievements=[]
            ))
    
    return experiences


def _parse_education_section(
    text: str  # Full LinkedIn profile text
) -> List[Education]:  # List of parsed education entries
    """Parse education section."""
    edu_section = extract_section(text, "Education", "Page")
    education = []
    
    # Wharton
    if "Wharton" in edu_section:
        education.append(Education(
            school="The Wharton School",
            degree="MBA",
            field="General Management",
            years="2012-2014"
        ))
    
    # UNC
    if "North Carolina" in edu_section:
        education.append(Education(
            school="University of North Carolina at Chapel Hill",
            degree="MS",
            field="Statistics & Operations Research",
            years="2000-2002"
        ))
    
    # IIT Madras
    if "IIT" in edu_section or "Madras" in edu_section:
        education.append(Education(
            school="Indian Institute of Technology, Madras",
            degree="BTech",
            field="Chemical Engineering, Operations Research minor",
            years="1996-2000"
        ))
    
    return education


def main():
    """Main execution."""
    # Load parsed JSON
    json_path = Path(__file__).parent.parent / "profile-data" / "linkedin-profile-parsed.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("Creating structured profile database...")
    profile = parse_profile(data['raw_text'])
    
    # Convert to dict for JSON serialization
    profile_dict = {
        "name": profile.name,
        "headline": profile.headline,
        "summary": profile.summary,
        "contact": profile.contact,
        "skills": profile.skills,
        "experiences": [asdict(e) for e in profile.experiences],
        "education": [asdict(e) for e in profile.education],
        "patents": profile.patents,
        "publications": profile.publications,
    }
    
    # Save structured profile
    output_path = json_path.parent / "profile-structured.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(profile_dict, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Structured profile saved to: {output_path}")
    print(f"\n=== Profile Summary ===")
    print(f"Name: {profile.name}")
    print(f"Headline: {profile.headline[:100]}...")
    print(f"Skills: {len(profile.skills)} extracted")
    print(f"Experiences: {len(profile.experiences)} companies")
    print(f"Education: {len(profile.education)} degrees")
    print(f"Patents: {len(profile.patents)}")
    print(f"Publications: {len(profile.publications)}")


if __name__ == "__main__":
    main()
