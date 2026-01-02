#!/usr/bin/env python3
"""
Last Validation Script
Runs the entire Resume Optimization System pipeline from Step 0 to Step 10.
Ensures all scripts execute successfully and data flows correctly.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

# Define the pipeline order
PIPELINE = [
    "0_setup.py",
    "1_scan_resume_folder.py",
    "2_classify_files.py",
    "3_generate_classification_report.py",
    "4_parse_linkedin_pdf.py",
    "5_create_profile_db.py",
    "6_generate_markdown_profile.py",
    "7_discover_resume_sections.py",
    "8_extract_resume_content.py",
    "9_build_master_db.py",
    "10_ingest_jds.py"
]

def run_script(script_name):
    """Run a single script and check exit code."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"❌ [MISSING] {script_name}")
        return False
        
    print(f"\n{'='*60}")
    print(f"▶️  Running: {script_name}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    try:
        # Use sys.executable to ensure we use the same python env (e.g. uv)
        # We assume dependencies are installed or we are in the right venv.
        cmd = [sys.executable, str(script_path)]
        
        # Stream output to console so user sees progress
        # Run with input disabled to prevent interactive prompts from hanging
        result = subprocess.run(cmd, check=False, stdin=subprocess.DEVNULL)
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"\n✅ [PASS] {script_name} ({duration:.2f}s)")
            return True
        else:
            print(f"\n❌ [FAIL] {script_name} (Exit Code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"\n❌ [ERROR] Failed to launch {script_name}: {e}")
        return False

def main():
    print("🚀 Starting End-to-End Pipeline Validation...")
    print(f"📂 Scripts Directory: {SCRIPTS_DIR}")
    
    # Unset legacy environment variables that might interfere with new paths
    # (Scrubbing these ensures we rely on defaults OR the new .env values below)
    legacy_vars = [
        'CLASSIFIED_FILE', 'INVENTORY_FILE', 'REPORT_FILE', 'RESUME_CONTENT_DB',
        'LINKEDIN_PDF', 'LINKEDIN_JSON', 'PROFILE_JSON', 'PROFILE_MD'
    ]
    for var in legacy_vars:
        if var in os.environ:
            print(f"⚠️  Unsetting legacy env var: {var}={os.environ.pop(var)}")

    # Load configuration from .env
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        print(f"\n📄 Loading configuration from {env_path}...")
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    os.environ[key] = value
                    if key in ['USER_NAME', 'USER_EMAIL', 'RESUME_FOLDER']:
                        print(f"   ✅ Set {key}='{value}'")
                except ValueError:
                    pass
    else:
        print("\n⚠️  No .env file found. Using script defaults.")
    
    failed_steps = []
    
    for script in PIPELINE:
        success = run_script(script)
        if not success:
            failed_steps.append(script)
            print(f"\n🛑 Pipeline halted at {script}. Fix the error and re-run.")
            break
            
    print(f"\n{'='*60}")
    if not failed_steps:
        print("🎉 SUCCESS! All steps completed successfully.")
        print("   The Resume Optimization System is fully operational.")
    else:
        print(f"⚠️  FAILED. The following step failed: {failed_steps[0]}")
    print(f"{'='*60}\n")
    
    sys.exit(1 if failed_steps else 0)

if __name__ == "__main__":
    main()
