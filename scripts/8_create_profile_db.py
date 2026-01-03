#!/usr/bin/env python3
"""[Supply Public Profile] Step 8: Create structured profile database."""
import json,os
from pathlib import Path
from dataclasses import asdict
from scripts.lib_profile import parse_profile

def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")

def main():
    dd=get_data_dir(); inp,out = dd/"supply"/"profile_data"/"linkedin-profile-parsed.json", dd/"supply"/"profile_data"/"profile-structured.json"
    if not inp.exists(): return
    
    print("Structuring profile...")
    p = parse_profile(json.loads(inp.read_text())['raw_text'], os.getenv('USER_NAME'))
    
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w') as f: key_d=asdict(p); key_d['experiences']=[asdict(e) for e in p.experiences]; key_d['education']=[asdict(e) for e in p.education]; json.dump(key_d, f, indent=2)
    print(f"✓ Saved to {out}\n{p.name}: {len(p.skills)} skills, {len(p.experiences)} jobs")

if __name__ == "__main__": main()
