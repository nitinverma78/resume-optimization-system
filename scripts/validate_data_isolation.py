#!/usr/bin/env python3
"""[Validation] Data Isolation Check: Verify generated data matches the configured user."""
import json
import os
import sys
from pathlib import Path
import pymupdf

ROOT = Path(__file__).parent.parent
def get_data_dir():
    if d := os.getenv('DATA_DIR'): return Path(d)
    return Path(__file__).parent.parent/"data"

def load_json(path):
    if not path.exists(): return None
    with open(path) as f: return json.load(f)

def normalize(text):
    """Simple normalization for name matching."""
    return text.lower().strip() if text else ""

def extract_text(path):
    """Extract text from file (PDF or Text)."""
    try:
        if path.suffix.lower() == '.pdf':
            doc = pymupdf.open(path)
            return "".join([page.get_text() for page in doc])
        else:
            return path.read_text(errors='ignore')
    except Exception as e:
        print(f"Warning: Could not read {path.name}: {e}")
        return ""

def check_identity_consistency(current_name, current_email):
    """
    Verify that the generated structured profile matches the current user.
    This ensures the pipeline actually processed the correct person.
    """
    profile_path = get_data_dir()/"supply"/"profile_data"/"profile-structured.json"
    if not profile_path.exists():
        print(f"⚠️  Profile not found at {profile_path} (Run pipeline first)")
        return True # Can't check if not generated
    
    profile = load_json(profile_path)
    if not profile: return False
    
    prof_name = normalize(profile.get('name', ''))
    prof_email = normalize(profile.get('email', ''))
    curr_name = normalize(current_name)
    curr_email = normalize(current_email)
    
    errors = []
    
    # Check Name (Fuzzy: split parts)
    if curr_name not in prof_name:
        errors.append(f"Profile Name Parsed: '{profile.get('name')}' != Expected: '{current_name}'")
        
    # Check Email (Exact if present)
    if prof_email and curr_email and prof_email != curr_email:
        errors.append(f"Profile Email Parsed: '{profile.get('email')}' != Expected: '{current_email}'")

    if errors:
        print("❌ PROFILE IDENTITY MISMATCH!")
        for e in errors: print(f"  • {e}")
        return False
    
    print(f"✅ Profile Identity Verification: Matches '{current_name}'")
    return True

def check_file_ownership(current_name, current_email):
    """
    Verify that files classified as 'user_resumes' actually belong to the user.
    Heuristic: User Resumes MUST contain the user's name or email (in Filename OR Content).
    """
    inv_path = get_data_dir()/"supply"/"2_file_inventory.json"
    inv = load_json(inv_path)
    if not inv: return True
    
    user_resumes = inv.get('user_resumes', [])
    if not user_resumes: return True
    
    print(f"Checking ownership of {len(user_resumes)} resume(s)...")
    
    errors = []
    skipped = 0
    passed_filename = 0
    
    name_parts = normalize(current_name).split()
    
    for f in user_resumes:
        path = Path(f['path'])
        if not path.exists(): continue
        
        # 1. Filename Check (Strong Indicator)
        # If filename contains user name, we assume ownership without reading content
        fn_lower = path.name.lower()
        if all(part in fn_lower for part in name_parts):
            passed_filename += 1
            continue
            
        # 2. Content Check
        # Only check content if filename matches didn't pass
        # And only if we support the filetype
        if path.suffix.lower() not in ['.pdf', '.txt', '.md', '.json', '.html']:
            skipped += 1
            continue
            
        try:
            content = extract_text(path).lower()
            if not content:
                skipped += 1
                continue
            
            # Check: Does file contain name or email?
            has_email = current_email and normalize(current_email) in content
            # Loose name check: all parts of name present
            has_name = all(part in content for part in name_parts)
            
            if not (has_name or has_email):
                errors.append(f"{path.name} (Content missing User Name/Email)")
        except Exception as e:
            print(f"Warning: Error checking {path.name}: {e}")
            skipped += 1

    if errors:
        print("❌ OWNERSHIP CHECK FAILED!")
        print("  Files classified as 'user_resumes' do not appear to match the current user:")
        for e in errors: print(f"  • {e}")
        return False
        
    print(f"✅ Ownership Verification: All checks passed ({passed_filename} via filename, {skipped} skipped binaries)")
    return True

def check_demo_contamination(current_name):
    """
    If NOT in demo mode, ensure 'Jane Doe' (simulation data) didn't leak in.
    """
    # If we ARE Jane Doe, this check is irrelevant
    if "jane" in current_name.lower() and "doe" in current_name.lower():
        return True
        
    print("Checking for Demo Data contamination...")
    
    prof_path = get_data_dir()/"supply"/"profile_data"/"profile-structured.json"
    if prof_path.exists():
        content = prof_path.read_text().lower()
        if "jane doe" in content or "jane.doe@example.com" in content:
            print("❌ DEMO CONTAMINATION DETECTED!")
            print("  • Profile contains 'Jane Doe' data while running as '{current_name}'")
            return False
            
    print("✅ Demo Isolation: No Jane Doe traces found")
    return True

def main():
    print("🔍 Data Isolation & Integrity Validation")
    print("="*60)
    
    user = os.getenv('USER_NAME')
    email = os.getenv('USER_EMAIL')
    
    if not user:
        print("❌ USER_NAME not set"); sys.exit(1)
        
    print(f"Target Identity: {user} <{email}>")
    print()
    
    # 1. Identity Consistency
    if not check_identity_consistency(user, email):
        sys.exit(1)
        
    # 2. File Ownership (Resumes must match User)
    if not check_file_ownership(user, email):
        sys.exit(1)
        
    # 3. Demo Contamination (Ensure Jane doesn't appear in Real runs)
    if not check_demo_contamination(user):
        sys.exit(1)
        
    print()
    print("✅ VALIDATION PASSED: Data consistent with current user.")

if __name__ == "__main__":
    main()
