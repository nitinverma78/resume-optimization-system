#!/usr/bin/env python3
"""[Privacy] Validate that git-tracked files contain no PII."""
import sys,argparse
from pathlib import Path
from scripts.lib_validation import scan_files, get_git_files

def main():
    p = argparse.ArgumentParser(description="Scan git repo for PII leaks")
    p.add_argument("--check-user", required=True, help="Name to check for (e.g., 'Jane Doe')")
    p.add_argument("--check-email", required=True, help="Email to check for")
    args = p.parse_args()
    
    root = Path(__file__).parent.parent
    print(f"🔍 Scanning git repo for PII: {args.check_user} <{args.check_email}>")
    
    # Exclude hooks that contain PII as configuration parameters
    exclude_files = {'hooks/pre-commit'}
    all_files = get_git_files(root)
    files = [f for f in all_files if str(f.relative_to(root)) not in exclude_files]
    print(f"📂 Scanning {len(files)} files (excluding {len(exclude_files)} hook config)")
    
    # Scan for PII (mode='absent' means PII should NOT be present)
    passed, violations = scan_files(files, args.check_user, args.check_email, mode='absent')
    
    if not passed:
        print(f"\n❌ PRIVACY VIOLATION: Found {len(violations)} file(s) with PII:")
        for v in violations[:10]:  # Show first 10
            print(f"  • {v}")
        if len(violations) > 10:
            print(f"  ... and {len(violations)-10} more")
        sys.exit(1)
    
    print(f"✅ PRIVACY CHECK PASSED: No PII found in {len(files)} files")

if __name__ == "__main__": main()
