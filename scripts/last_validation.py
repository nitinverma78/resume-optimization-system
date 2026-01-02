#!/usr/bin/env python3
"""Last Validation Script - Runs entire pipeline from Step 0 to Step 10."""
import subprocess,sys,os,time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

PIPELINE = [
    # Initiation
    "0_setup.py",
    # Supply Discovery (Steps 1-3)
    "1_scan_resume_folder.py", "2_classify_files.py", "3_classification_report.py",
    # Supply Knowledge Extraction (Steps 4-6)
    "4_discover_sections.py", "5_extract_content.py", "6_build_knowledge_base.py",
    # Supply Public Profile (Steps 7-9)
    "7_parse_linkedin.py", "8_create_profile_db.py", "9_generate_profile_md.py",
    # Demand Discovery (Step 10)
    "10_ingest_jds.py"
]

LEGACY_VARS = ['CLASSIFIED_FILE','INVENTORY_FILE','REPORT_FILE','RESUME_CONTENT_DB',
               'LINKEDIN_PDF','LINKEDIN_JSON','PROFILE_JSON','PROFILE_MD']

def run_script(name: str) -> bool:
    """Run a single script and check exit code."""
    path = SCRIPTS_DIR / name
    if not path.exists():
        print(f"❌ [MISSING] {name}")
        return False
        
    print(f"\n{'='*60}\n▶️  Running: {name}\n{'='*60}\n")
    
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(path)], check=False, stdin=subprocess.DEVNULL)
        dt = time.time() - t0
        
        if r.returncode == 0:
            print(f"\n✅ [PASS] {name} ({dt:.2f}s)")
            return True
        print(f"\n❌ [FAIL] {name} (Exit Code: {r.returncode})")
        return False
    except Exception as e:
        print(f"\n❌ [ERROR] Failed to launch {name}: {e}")
        return False

def load_env():
    """Load .env file into environment."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        print(f"\n📄 Loading configuration from {env_path}...")
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                try:
                    k, v = line.split("=", 1)
                    v = v.strip('"').strip("'")
                    os.environ[k] = v
                    if k in ['USER_NAME', 'USER_EMAIL', 'RESUME_FOLDER']:
                        print(f"   ✅ Set {k}='{v}'")
                except ValueError: pass
    else:
        print("\n⚠️  No .env file found. Using script defaults.")

def main():
    print("🚀 Starting End-to-End Pipeline Validation...")
    print(f"📂 Scripts Directory: {SCRIPTS_DIR}")
    
    # Scrub legacy vars
    for v in LEGACY_VARS:
        if v in os.environ:
            print(f"⚠️  Unsetting legacy env var: {v}={os.environ.pop(v)}")

    load_env()
    
    failed = []
    for s in PIPELINE:
        if not run_script(s):
            failed.append(s)
            print(f"\n🛑 Pipeline halted at {s}. Fix the error and re-run.")
            break
            
    print(f"\n{'='*60}")
    if not failed:
        print("🎉 SUCCESS! All steps completed successfully.")
        print("   The Resume Optimization System is fully operational.")
    else:
        print(f"⚠️  FAILED. The following step failed: {failed[0]}")
    print(f"{'='*60}\n")
    
    sys.exit(1 if failed else 0)

if __name__ == "__main__": main()
