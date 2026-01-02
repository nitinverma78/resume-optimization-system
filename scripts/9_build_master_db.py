#!/usr/bin/env python3
"""Step 9: Build Master Knowledge Base - Consolidate, dedupe, tag resume content."""
import json,re,difflib
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import List,Dict,Set,Any,NewType

# --- Domain Types (RL-book pattern) ---
CompanyName = NewType('CompanyName', str)
BulletText  = NewType('BulletText', str)
Tag         = NewType('Tag', str)
SourceFile  = NewType('SourceFile', str)

@dataclass(frozen=True)
class Bullet:
    """Immutable bullet point with metadata."""
    text: BulletText
    sources: tuple  # Use tuple for immutability
    tags: tuple     # Use tuple for immutability

@dataclass(frozen=True)
class CompanyPool:
    """Immutable company experience pool."""
    name: CompanyName
    roles: tuple
    bullets: tuple
    bullet_count: int

# --- Type Aliases (RL-book pattern) ---
RawBullet = Dict[str, Any]  # {'text': str, 'source': str}
BulletPool = List[Dict[str, Any]]
KnowledgeBase = Dict[str, Any]

# --- Rich Taxonomy ---
TAG_TAX = {
    "Leadership": ["led","managed","hired","mentored","strategy","vision","roadmap","stakeholder",
                   "c-suite","board","budget","transformation","persuaded","negotiated","change management"],
    "AI_ML": ["ai","ml","machine learning","genai","generative ai","llm","nlp","computer vision",
              "pytorch","tensorflow","model","inference","training","rag","agentic","algorithm"],
    "Tech_Cloud": ["architecture","cloud","aws","gcp","azure","distributed systems","microservices",
                   "api","platform","engineering","devops","kubernetes","docker","scalability","latency"],
    "Business_Impact": ["revenue","sales","cost","savings","profit","roi","growth","conversion",
                        "budget","p&l","market share","efficiency","productivity"],
    "Domain_Specific": ["supply chain","e-commerce","healthcare","fintech","retail","logistics",
                        "fulfillment","inventory","pricing","personalization","search","recommendation"]
}

CO_MAP: Dict[str, CompanyName] = {
    "amazon": CompanyName("Amazon"), "staples": CompanyName("Staples"), "a": CompanyName("Amazon"),
    "fico": CompanyName("FICO"), "fair isaac": CompanyName("FICO"),
    "the aspen group": CompanyName("Aspen Dental"), "tag": CompanyName("Aspen Dental"),
    "manifold": CompanyName("Manifold Systems"), "zulily": CompanyName("Zulily")
}

def norm(txt: str) -> str: return re.sub(r'\W+', ' ', txt.lower()).strip()

def get_tags(txt: BulletText) -> List[Tag]:
    """Apply taxonomy tags to bullet text."""
    tags: Set[Tag] = set()
    lo = txt.lower()
    for cat, kws in TAG_TAX.items():
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', lo):
                tags.add(Tag(cat))
                tags.add(Tag(kw.title()))
    if re.search(r'(\$\d|\d%|\d\+)', txt): tags.add(Tag("Quantifiable_Impact"))
    return list(tags)

def canon_co(name: str) -> CompanyName:
    """Canonicalize company name."""
    clean = name.lower().replace("inc","").replace("technologies","").replace(".com","").strip()
    for k, v in CO_MAP.items():
        if k in clean: return v
    return CompanyName(name.strip())

def merge_bullets(bullets: List[RawBullet]) -> BulletPool:
    """Dedupe similar bullets, keep best version."""
    unique: BulletPool = []
    for b in bullets:
        b_norm = norm(b['text'])
        is_dup = False
        for u in unique:
            if difflib.SequenceMatcher(None, b_norm, norm(u['text'])).ratio() > 0.85:
                is_dup = True
                u['sources'].append(b['source'])
                if len(b['text']) > len(u['text']): u['text'] = b['text']
                break
        if not is_dup:
            unique.append({'text': b['text'], 'sources': [b['source']], 'tags': get_tags(BulletText(b['text']))})
    return unique

def main(
    inp: Path = Path(__file__).parent.parent/"data"/"supply"/"4_raw_extracted_content.json",
    out: Path = Path(__file__).parent.parent/"data"/"supply"/"5_master_knowledge_base.json"
):
    """Main build loop."""
    if not inp.exists():
        print(f"Error: {inp} not found. Run Step 8 first.")
        return

    print("Building Master Knowledge Base...")
    with open(inp, 'r') as f: raw_db = json.load(f)
        
    master: KnowledgeBase = {"meta": {"source_files_count": len(raw_db)}, "companies": defaultdict(lambda: {"roles": set(), "bullets": []})}
    temp: Dict[CompanyName, List[RawBullet]] = defaultdict(list)
    
    for entry in raw_db:
        src = SourceFile(entry.get('source_file', ''))
        for stage in ['recent', 'earlier']:
            for blk in entry.get('experience', {}).get(stage, []):
                co = canon_co(blk['company'])
                master['companies'][co]['roles'].add(blk.get('role', 'Unknown'))
                for b in blk.get('bullets', []):
                    temp[co].append({'text': b['text'], 'source': src})

    print(f"  Consolidating {len(temp)} unique companies...")
    
    final: Dict[CompanyName, Dict] = {}
    for co, raw in temp.items():
        uniq = merge_bullets(raw)
        final[co] = {"name": co, "roles": list(master['companies'][co]['roles']),
                     "bullet_pool": uniq, "bullet_count": len(uniq)}
        print(f"    - {co}: {len(raw)} raw -> {len(uniq)} unique bullets")
        
    master['companies'] = final
    
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Knowledge Base built: {out}")

if __name__ == "__main__": main()
