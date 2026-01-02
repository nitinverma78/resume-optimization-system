#!/usr/bin/env python3
"""
Generate a clean Markdown CV/Profile from the parsed LinkedIn data.
This ensures the human-readable view matches the system's structured data.
"""

import json, os, sys, re
from pathlib import Path
from profile_parser_lib import parse_profile, Profile

def render_markdown(profile: Profile) -> str:
    """Render Profile object to Markdown."""
    lines = []
    
    # Header
    lines.append(f"# {profile.name}")
    lines.append(f"**{profile.headline}**")
    lines.append("")
    
    # Contact
    contact_parts = []
    if 'email' in profile.contact: contact_parts.append(f"📧 {profile.contact['email']}")
    if 'linkedin' in profile.contact: contact_parts.append(f"🔗 [{profile.contact['linkedin']}](https://www.{profile.contact['linkedin']})")
    if 'company_website' in profile.contact: contact_parts.append(f"🌐 {profile.contact['company_website']}")
    lines.append(" | ".join(contact_parts))
    lines.append("")
    
    # Summary
    if profile.summary:
        lines.append("## Professional Summary")
        lines.append(profile.summary)
        lines.append("")
        
    # Skills
    if profile.skills:
        lines.append("## Top Skills")
        lines.append(", ".join(profile.skills))
        lines.append("")
        
    # Experience
    if profile.experiences:
        lines.append("## Professional Experience")
        for exp in profile.experiences:
            lines.append(f"### {exp.company}")
            lines.append(f"**{exp.title}** | {exp.duration}")
            if exp.description:
                # Preserve line structure for readability
                # Try to detect sub-roles or dates to bold them
                desc_lines = exp.description.split('\n')
                formatted_desc = []
                for line in desc_lines:
                    line = line.strip()
                    if not line: continue
                    # Heuristic: If line looks like a date range or job title, bold it
                    # Improved heuristic: Catch more titles even if long
                    is_date = re.search(r'\d{4}\s*-\s*\d{4}', line)
                    is_title_keyword = any(t in line for t in ['Manager', 'Director', 'VP', 'Head', 'Scientist', 'Officer', 'Founder', 'Researcher', 'Engineer'])
                    is_title_format = len(line) < 80 and is_title_keyword and not line.startswith('•') and not line.startswith('-')
                    
                    if is_date or is_title_format:
                        formatted_desc.append(f"\n**{line}**\n")
                    else:
                        formatted_desc.append(f"> {line}")
                
                lines.append("\n".join(formatted_desc))
            lines.append("")
            
    # Education
    if profile.education:
        lines.append("## Education")
        for edu in profile.education:
            lines.append(f"### {edu.school}")
            lines.append(f"{edu.degree}, {edu.field}")
            lines.append(f"_{edu.years}_")
            lines.append("")
            
    # Patents & Publications
    if profile.patents:
        lines.append("## Patents")
        for p in profile.patents:
            lines.append(f"- {p}")
        lines.append("")
        
    if profile.publications:
        lines.append("## Publications")
        for p in profile.publications:
            lines.append(f"- {p}")
        lines.append("")
        
    return "\n".join(lines)


def main(
    linkedin_json: Path = Path(__file__).parent.parent / "profile-data" / "linkedin-profile-parsed.json",
    output_md: Path = Path(__file__).parent.parent / "profile-data" / "linkedin-profile.md",
    user_name: str = None
):
    """Main execution."""
    # Environment variable overrides
    linkedin_json = Path(os.getenv('LINKEDIN_JSON', str(linkedin_json)))
    output_md = Path(os.getenv('PROFILE_MD', str(output_md)))
    user_name = os.getenv('USER_NAME', user_name)

    if not linkedin_json.exists():
        print(f"Error: Source file not found: {linkedin_json}", file=sys.stderr)
        return

    with open(linkedin_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Generating Markdown profile...")
    profile = parse_profile(data['raw_text'], user_name)
    
    md_content = render_markdown(profile)
    
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print(f"✓ Markdown profile saved to: {output_md}")

if __name__ == "__main__":
    main()
