#!/usr/bin/env python3
"""[Supply Public Profile] Step 9: Generate markdown."""
import json,os,sys,re
from pathlib import Path
from scripts.lib_profile import parse_profile

def render(p):
    L = [f"# {p.name}", f"**{p.headline}**", ""]
    c = []
    if 'email' in p.contact: c.append(f"📧 {p.contact['email']}")
    if 'linkedin' in p.contact: c.append(f"🔗 [{p.contact['linkedin']}](https://www.{p.contact['linkedin']})")
    if 'company_website' in p.contact: c.append(f"🌐 {p.contact['company_website']}")
    L.append(" | ".join(c) + "\n")
    if p.summary: L+=[f"## Professional Summary\n{p.summary}\n"]
    if p.skills: L+=[f"## Top Skills\n{', '.join(p.skills)}\n"]
    if p.experiences:
        L+=["## Professional Experience"]
        for e in p.experiences:
            L+=[f"### {e.company}\n**{e.title}** | {e.duration}"]
            d=[]
            for l in [x.strip() for x in e.description.split('\n') if x.strip()]:
                d.append(f"\n**{l}**\n" if re.search(r'\d{4}.*\d{4}',l) or (len(l)<80 and any(t in l for t in ['Manager','Director','Engineer']) and not l.startswith(('-','•'))) else f"> {l}")
            L+=["\n".join(d)+"\n"]
    if p.education:
        L+=["## Education"] + [f"### {e.school}\n{e.degree}, {e.field}\n_{e.years}_\n" for e in p.education]
    for k,v in [("Patents",p.patents),("Publications",p.publications)]:
        if v: L+=[f"## {k}"] + [f"- {x}" for x in v] + [""]
    return "\n".join(L)

def main():
    dd=Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data"); inp,out = dd/"supply"/"profile_data"/"linkedin-profile-parsed.json", dd/"supply"/"profile_data"/"linkedin-profile.md"
    if not inp.exists(): return
    
    print("Generating MD...")
    with open(out,'w') as f: f.write(render(parse_profile(json.loads(inp.read_text())['raw_text'], os.getenv('USER_NAME'))))
    print(f"✓ Saved to {out}")

if __name__=="__main__": main()
