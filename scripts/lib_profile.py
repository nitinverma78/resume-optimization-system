"""Shared library for parsing LinkedIn profiles."""
import json,re,os
from pathlib import Path
from dataclasses import dataclass
from typing import List,Dict

@dataclass(frozen=True)
class Experience: company: str; title: str; duration: str; location: str; description: str; achievements: List[str]
@dataclass(frozen=True)
class Education: school: str; degree: str; field: str; years: str
@dataclass(frozen=True)
class Profile: name: str; headline: str; summary: str; contact: Dict[str, str]; skills: List[str]; experiences: List[Experience]; education: List[Education]; patents: List[str]; publications: List[str]

def txt_btwn(txt, s, e=None):
    m = re.search(f"{re.escape(s)}(.*?)({'(' + re.escape(e) + ')' if e else '$'})", txt, re.DOTALL)
    return m.group(1).strip() if m else ""

def parse_exp(txt, cfg_cos=None):
    sec = txt_btwn(txt, "Experience", "Education"); exps = []
    cos = cfg_cos or {"Example Corp": r"Example Corp\nTitle\n(.*?)(?=NextCompany|$)"}
    for co, pat in cos.items():
        if m := re.search(pat, sec, re.DOTALL):
            etxt = m.group(0).strip(); lines = etxt.split('\n')
            dur = (re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}.*?(?:Present|\d{4}))', etxt[:200]) or re.match(r'()',"")).group(1) or "See parsed"
            exps.append(Experience(company=co, title=lines[1] if len(lines)>1 else "Title", duration=dur, location="", description=etxt, achievements=[]))
    return exps

def parse_edu(txt, cfg_edu=None):
    sec = txt_btwn(txt, "Education", "Page") or txt_btwn(txt, "Education", None); edus = []
    if cfg_edu:
        for i in cfg_edu:
            if i.get('keyword','') in sec or i.get('keyword2','') in sec: edus.append(Education(school=i['school'], degree=i['degree'], field=i['field'], years=i['years']))
    elif "University" in sec: edus.append(Education("University Name", "Degree", "Field", "2010-2014"))
    return edus

def merge_lns(txt):
    i=[]; c=""
    for l in [x.strip() for x in txt.split('\n') if x.strip()]:
        if c and not l[0].isupper(): c+=" "+l
        else: 
            if c: i.append(c)
            c=l
    if c: i.append(c)
    return i

def parse_profile(raw, name=None):
    name = name or os.getenv('USER_NAME', 'Your Name')
    cfg_p = Path(__file__).parent.parent/"data"/"supply"/"profile_data"/"parsing_config.json"
    cfg = json.loads(cfg_p.read_text()) if cfg_p.exists() else {}
    
    raw = re.sub(r'Page \d+ of \d+', '', re.sub(r'\n\s*Page \d+ of \d+\s*\n', '\n', raw))
    nm = getattr(re.search(rf"({re.escape(name)})", raw), 'group', lambda x:name)(1)
    hl = getattr(re.search(rf"{re.escape(name)}\n(.*?)\n(?:Greater|Summary)", raw, re.DOTALL), 'group', lambda x:"")(1).strip().replace('\n', ' ')
    
    ct = {}
    if m:=re.search(r"([\w\.-]+@[\w\.-]+\.\w+)", raw): ct['email']=m.group(1)
    if m:=re.search(r"www\.linkedin\.com/in/([\w-]+)", raw): ct['linkedin']=f"linkedin.com/in/{m.group(1)}"
    if m:=re.search(r"([\w-]+\.ai) \(Company\)", raw): ct['company_website']=m.group(1)

    return Profile(name=nm, headline=hl, summary=txt_btwn(raw, "Summary", "Experience"), contact=ct, 
                   skills=[s.strip() for s in txt_btwn(raw,"Top Skills","Publications").split('\n') if s.strip()],
                   experiences=parse_exp(raw, cfg.get('companies')), education=parse_edu(raw, cfg.get('education')),
                   patents=merge_lns(txt_btwn(raw,"Patents",name))[:4], publications=merge_lns(txt_btwn(raw,"Publications","Patents"))[:2])
