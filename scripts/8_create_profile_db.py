#!/usr/bin/env python3
"""[Supply Public Profile] Step 8: Create structured profile database."""
import json,os
from pathlib import Path
from dataclasses import asdict
from lib_profile import parse_profile, Profile

def main(
    inp: Path = Path(__file__).parent.parent/"data"/"supply"/"profile_data"/"linkedin-profile-parsed.json",
    cfg: Path = Path(__file__).parent.parent/"data"/"supply"/"profile_data"/"parsing_config.json",
    out: Path = Path(__file__).parent.parent/"data"/"supply"/"profile_data"/"profile-structured.json",
    name: str = None  # User's full name (default: USER_NAME env var)
) -> Profile:
    """Main execution."""
    inp  = Path(os.getenv('LINKEDIN_JSON', str(inp)))
    out  = Path(os.getenv('PROFILE_JSON', str(out)))
    name = os.getenv('USER_NAME', name)
    
    with open(inp, 'r', encoding='utf-8') as f: data = json.load(f)
    
    print("Creating structured profile database...")
    p = parse_profile(data['raw_text'], name)
    
    # Convert to dict
    pdict = {
        "name": p.name, "headline": p.headline, "summary": p.summary,
        "contact": p.contact, "skills": p.skills,
        "experiences": [asdict(e) for e in p.experiences],
        "education": [asdict(e) for e in p.education],
        "patents": p.patents, "publications": p.publications,
    }
    
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(pdict, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Structured profile saved to: {out}")
    print(f"\n=== Profile Summary ===")
    print(f"Name: {p.name}")
    print(f"Headline: {p.headline[:100]}...")
    print(f"Skills: {len(p.skills)} extracted")
    print(f"Experiences: {len(p.experiences)} companies")
    print(f"Education: {len(p.education)} degrees")
    print(f"Patents: {len(p.patents)}")
    print(f"Publications: {len(p.publications)}")

if __name__ == "__main__": main()
