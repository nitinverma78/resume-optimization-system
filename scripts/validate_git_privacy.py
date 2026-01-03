#!/usr/bin/env python3
"""[Privacy] Validate that git-tracked files contain no PII."""
import sys,argparse
from pathlib import Path
from scripts.lib_validation import scan_files, get_git_files

def main():
    p = argparse.ArgumentParser(description="Scan git repo for PII leaks")
    p.add_argument("--check-user", required=True, help="Name to check for (e.g., 'Nitin Verma')")
    p.add_argument("--check-email", required=True, help="Email to check for")
    args = p.parse_args()
    
    root = Path(__file__).parent.parent
    print(f"🔍 Scanning git repo for PII: {args.check_user} <{args.check_email}>")
    
    # Get ALL git-tracked files (no exclusions - if it's tracked, it should be clean)
    files = get_git_files(root)
    print(f"📂 Scanning {len(files)} git-tracked files")
    
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
