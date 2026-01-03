#!/usr/bin/env python3
"""[Validation] Check data isolation."""
import json,os,sys
from pathlib import Path
from scripts.lib_validation import scan_files, norm

def get_data_dir(): return Path(os.getenv('DATA_DIR') or Path(__file__).parent.parent/"data")

def main():
    print("🔍 Validating Isolation...")
    usr, em = os.getenv('USER_NAME'), os.getenv('USER_EMAIL')
    if not usr: sys.exit("❌ USER_NAME missing")
    dd = get_data_dir()
    
    # 1. Identity Check
    prof_p = dd/"supply"/"profile_data"/"profile-structured.json"
    if prof_p.exists():
        p = json.loads(prof_p.read_text()); pn, pe = norm(p.get('name')), norm(p.get('email'))
        if norm(usr) not in pn or (pe and norm(em)!=pe): sys.exit(f"❌ Identity Mismatch: {pn} vs {usr}")
        print(f"✅ Identity: Matches {usr}")

    # 2. Ownership Check (using shared library)
    inv_p = dd/"supply"/"2_file_inventory.json"
    if inv_p.exists():
        inv = json.loads(inv_p.read_text())
        files = [Path(f['path']) for f in inv.get('user_resumes',[])]
        print(f"Checking {len(files)} resumes...")
        
        # Use shared scan_files with mode='contains' (PII must exist)
        passed, violations = scan_files(files, usr, em or "", mode='contains')
        
        if not passed:
            print(f"❌ Ownership Fail:")
            for v in violations: print(f"  • {v}")
            sys.exit(1)
        
        print("✅ Ownership: Verified")

    print("✅ VALIDATION PASSED")

if __name__ == "__main__": main()
