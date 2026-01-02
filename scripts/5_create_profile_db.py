#!/usr/bin/env python3
"""
Create a structured profile database from LinkedIn PDF.
Extracts experiences, skills, education, and achievements into searchable format.
"""

import json, os
from pathlib import Path
from dataclasses import asdict

# Import shared parsing logic
from lib_profile_steps_5_6 import parse_profile, Profile


def main(
    linkedin_json: Path = Path(__file__).parent.parent / "profile-data" / "linkedin-profile-parsed.json",  # Input LinkedIn JSON
    output_json: Path = Path(__file__).parent.parent / "profile-data" / "profile-structured.json",  # Output structured
    user_name: str = None  # User's full name for parsing (default: USER_NAME env var)
) -> Profile:  # Structured Profile object
    """Main execution."""
    # Allow environment variables to override defaults
    linkedin_json = Path(os.getenv('LINKEDIN_JSON', str(linkedin_json)))
    output_json = Path(os.getenv('PROFILE_JSON', str(output_json)))
    user_name = os.getenv('USER_NAME', user_name)  # Get from env if not provided
    
    with open(linkedin_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("Creating structured profile database...")
    profile = parse_profile(data['raw_text'], user_name)
    
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
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(profile_dict, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Structured profile saved to: {output_json}")
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
