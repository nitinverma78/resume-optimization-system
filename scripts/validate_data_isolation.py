#!/usr/bin/env python3
"""[Validation] Check data isolation."""
import json,os,sys
from pathlib import Path
from scripts.lib_extract import extract

def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")
def norm(t): return (t or "").lower().strip()

def main():
    print("🔍 Validating Isolation...")
    usr, em = os.getenv('USER_NAME'), os.getenv('USER_EMAIL')
    if not usr: sys.exit("❌ USER_NAME missing")
    dd = get_data_dir()
    
    # 1. Identity
    prof_p = dd/"supply"/"profile_data"/"profile-structured.json"
    if prof_p.exists():
        p = json.loads(prof_p.read_text()); pn, pe = norm(p.get('name')), norm(p.get('email'))
        if norm(usr) not in pn or (pe and norm(em)!=pe): sys.exit(f"❌ Identity Mismatch: {pn} vs {usr}")
        print(f"✅ Identity: Matches {usr}")

    # 2. Ownership
    inv_p = dd/"supply"/"2_file_inventory.json"
    if inv_p.exists():
        inv = json.loads(inv_p.read_text())
        print(f"Checking {len(inv.get('user_resumes',[]))} resumes...")
        for f in inv.get('user_resumes',[]):
            p = Path(f['path']); n_pts = norm(usr).split()
            if not p.exists(): continue
            if all(pt in p.name.lower() for pt in n_pts): continue # Filename pass
            if p.suffix.lower() not in ['.pdf','.txt','.md','.html']: continue
            txt = extract(p).lower()
            if not (norm(em) in txt or all(pt in txt for pt in n_pts)): print(f"❌ Ownership Fail: {p.name}"); sys.exit(1)
        print("✅ Ownership: Verified")

    print("✅ VALIDATION PASSED")

if __name__ == "__main__": main()
