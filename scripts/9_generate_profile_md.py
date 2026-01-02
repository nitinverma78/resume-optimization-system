#!/usr/bin/env python3
"""[Supply Public Profile] Step 9: Generate markdown profile from parsed data."""
import json,os,sys,re
from pathlib import Path
from lib_profile import Profile, parse_profile

def render_md(p: Profile) -> str:
    """Render Profile object to Markdown."""
    lines = []
    
    # Header
    lines.append(f"# {p.name}")
    lines.append(f"**{p.headline}**")
    lines.append("")
    
    # Contact
    parts = []
    if 'email' in p.contact:           parts.append(f"📧 {p.contact['email']}")
    if 'linkedin' in p.contact:        parts.append(f"🔗 [{p.contact['linkedin']}](https://www.{p.contact['linkedin']})")
    if 'company_website' in p.contact: parts.append(f"🌐 {p.contact['company_website']}")
    lines.append(" | ".join(parts))
    lines.append("")
    
    # Summary
    if p.summary:
        lines.extend(["## Professional Summary", p.summary, ""])
        
    # Skills
    if p.skills:
        lines.extend(["## Top Skills", ", ".join(p.skills), ""])
        
    # Experience
    if p.experiences:
        lines.append("## Professional Experience")
        for exp in p.experiences:
            lines.append(f"### {exp.company}")
            lines.append(f"**{exp.title}** | {exp.duration}")
            if exp.description:
                desc_lines = exp.description.split('\n')
                fmt = []
                for line in desc_lines:
                    line = line.strip()
                    if not line: continue
                    is_date = re.search(r'\d{4}\s*-\s*\d{4}', line)
                    title_kw = any(t in line for t in ['Manager','Director','VP','Head','Scientist','Officer','Founder','Researcher','Engineer'])
                    is_title = len(line) < 80 and title_kw and not line.startswith(('•', '-'))
                    if is_date or is_title: fmt.append(f"\n**{line}**\n")
                    else:                   fmt.append(f"> {line}")
                lines.append("\n".join(fmt))
            lines.append("")
            
    # Education
    if p.education:
        lines.append("## Education")
        for edu in p.education:
            lines.extend([f"### {edu.school}", f"{edu.degree}, {edu.field}", f"_{edu.years}_", ""])
            
    # Patents & Publications
    if p.patents:
        lines.append("## Patents")
        lines.extend([f"- {x}" for x in p.patents])
        lines.append("")
    if p.publications:
        lines.append("## Publications")
        lines.extend([f"- {x}" for x in p.publications])
        lines.append("")
        
    return "\n".join(lines)

def main(
    inp: Path = Path(__file__).parent.parent/"data"/"supply"/"profile_data"/"linkedin-profile-parsed.json",
    out: Path = Path(__file__).parent.parent/"data"/"supply"/"profile_data"/"linkedin-profile.md",
    name: str = None
):
    """Main execution."""
    name = os.getenv('USER_NAME', name)

    if not inp.exists():
        print(f"Error: Source file not found: {inp}", file=sys.stderr)
        return

    with open(inp, 'r', encoding='utf-8') as f: data = json.load(f)

    print("Generating Markdown profile...")
    p = parse_profile(data['raw_text'], name)
    
    md = render_md(p)
    
    with open(out, 'w', encoding='utf-8') as f: f.write(md)
    print(f"✓ Markdown profile saved to: {out}")

if __name__ == "__main__": main()
