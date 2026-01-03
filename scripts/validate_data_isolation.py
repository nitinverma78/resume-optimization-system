#!/usr/bin/env python3
"""[Validation] Data Isolation Check: Ensure data/ contains only current USER_NAME's data."""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT/"data"

# Known test personas (don't flag these as contamination)
TEST_PERSONAS = {"Jane Doe", "jane.doe@example.com"}

def scan_file_for_names(file_path, current_user, known_other_users):
    """Scan a single file for references to other user names."""
    try:
        if file_path.suffix in ['.json', '.md', '.txt']:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Check for other user names
            contamination = []
            for other_user in known_other_users:
                if other_user.lower() in content.lower():
                    contamination.append(other_user)
            
            return contamination
    except Exception as e:
        print(f"Warning: Could not scan {file_path}: {e}")
    
    return []

def load_known_users():
    """Load list of known user names from config (if exists)."""
    # Hardcoded list of "real" users that should NEVER contaminate each other
    real_users = {"Nitin Verma", "nitinverma78@gmail.com"}
    
    # Demo/test users that can be ignored
    test_users = {"Jane Doe", "jane.doe@example.com"}
    
    return real_users, test_users

def main():
    print("🔍 Data Isolation Validation")
    print("="*60)
    
    # Get current user
    current_user = os.getenv('USER_NAME')
    current_email = os.getenv('USER_EMAIL')
    
    if not current_user:
        print("❌ USER_NAME not set")
        sys.exit(1)
    
    print(f"Current user: {current_user}")
    print(f"Scanning: {DATA_DIR}")
    print()
    
    # Get list of known users
    real_users, test_users = load_known_users()
    
    # Determine what to check for based on current user
    if current_user in test_users or (current_email and current_email in test_users):
        # Demo mode: Check for contamination from REAL users
        check_for = real_users
        mode = "Demo Mode"
    else:
        # Normal mode: Check for contamination from OTHER real users 
        check_for = real_users - {current_user}
        if current_email:
            check_for.discard(current_email)
        mode = "Normal Mode"
    
    if not check_for:
        print(f"ℹ️  {mode}: No other users to check against")
        print("✅ Validation passed")
        return
    
    print(f"{mode}: Checking for contamination from: {', '.join(check_for)}")
    print()
    
    # Scan all files in data/
    if not DATA_DIR.exists():
        print("✅ data/ folder doesn't exist (clean state)")
        return
    
    contaminated_files = []
    files_scanned = 0
    
    for file_path in DATA_DIR.rglob("*"):
        if file_path.is_file() and file_path.suffix in ['.json', '.md', '.txt']:
            files_scanned += 1
            found = scan_file_for_names(file_path, current_user, check_for)
            if found:
                contaminated_files.append((file_path, found))
    
    print(f"Scanned {files_scanned} files")
    print()
    
    # Report results
    if contaminated_files:
        print("❌ CONTAMINATION DETECTED!")
        print()
        for file_path, users in contaminated_files:
            rel_path = file_path.relative_to(ROOT)
            print(f"  • {rel_path}")
            print(f"    Contains: {', '.join(users)}")
        print()
        print(f"Expected: Only '{current_user}' data")
        print(f"Found: References to {len(contaminated_files)} contaminated files")
        sys.exit(1)
    else:
        print("✅ No contamination detected")
        print(f"✅ All data belongs to: {current_user}")

if __name__ == "__main__":
    main()
