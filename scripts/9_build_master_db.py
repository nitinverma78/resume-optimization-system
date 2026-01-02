#!/usr/bin/env python3
"""Step 9: Build Master Knowledge Base - Consolidate, dedupe, tag resume content."""
import json,re,difflib
from pathlib import Path
from collections import defaultdict
from typing import List,Dict,Set,Any

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

CO_MAP = {
    "amazon": "Amazon", "staples": "Staples", "a": "Amazon",
    "fico": "FICO", "fair isaac": "FICO",
    "the aspen group": "Aspen Dental", "tag": "Aspen Dental",
    "manifold": "Manifold Systems", "zulily": "Zulily"
}

def norm(txt: str) -> str: return re.sub(r'\W+', ' ', txt.lower()).strip()

def get_tags(txt: str) -> List[str]:
    tags = set()
    lo = txt.lower()
    for cat, kws in TAG_TAX.items():
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', lo):
                tags.add(cat)
                tags.add(kw.title())
    if re.search(r'(\$\d|\d%|\d\+)', txt): tags.add("Quantifiable_Impact")
    return list(tags)

def canon_co(name: str) -> str:
    clean = name.lower().replace("inc","").replace("technologies","").replace(".com","").strip()
    for k, v in CO_MAP.items():
        if k in clean: return v
    return name.strip()

def merge_bullets(bullets: List[Dict]) -> List[Dict]:
    """Dedupe similar bullets, keep best version."""
    unique = []
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
            unique.append({'text': b['text'], 'sources': [b['source']], 'tags': get_tags(b['text'])})
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
        
    master = {"meta": {"source_files_count": len(raw_db)}, "companies": defaultdict(lambda: {"roles": set(), "bullets": []})}
    temp = defaultdict(list)
    
    for entry in raw_db:
        src = entry.get('source_file')
        for stage in ['recent', 'earlier']:
            for blk in entry.get('experience', {}).get(stage, []):
                co = canon_co(blk['company'])
                master['companies'][co]['roles'].add(blk.get('role', 'Unknown'))
                for b in blk.get('bullets', []):
                    temp[co].append({'text': b['text'], 'source': src})

    print(f"  Consolidating {len(temp)} unique companies...")
    
    final = {}
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
