#!/usr/bin/env python3
"""
Last Validation Script
Runs the entire Resume Optimization System pipeline from Step 0 to Step 10.
Ensures all scripts execute successfully and data flows correctly.
"""

import subprocess
import sys
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
        result = subprocess.run(cmd, check=False)
        
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
