#!/usr/bin/env python3
"""[Initiation] Setup script - Creates directories and validates environment."""
import os,sys
from pathlib import Path

def setup():
    """Initialize the resume optimization system."""
    print("🚀 Setting up Resume Optimization System...\n")
    
    # Create directories - aligned for clarity
    dirs = ["data", "data/supply", "data/demand", "data/supply/profile_data", "examples"]
    for d in dirs:
        p = Path(d)
        p.mkdir(exist_ok=True)
        (p / '.gitkeep').touch()
        print(f"✓ Created {d}/ (gitignored - your data stays private)")
    
    print("\n📁 Directory Structure:")
    print("  data/                      - Processing outputs (private)")
    print("  data/supply/profile_data/  - Your LinkedIn profile (private)")
    print("  examples/                  - Sample data for testing (public)")
    
    print("\n🔐 Privacy:")
    print("Please enter your details to configure the system (or press Enter to skip):")
    
    # Only prompt if interactive
    if sys.stdin.isatty():
        name  = input("Full Name: ").strip()
        email = input("Email Address: ").strip()
        folder = input("Path to Resume Folder: ").strip()
    else:
        print("  (Non-interactive mode detected using defaults)")
        name,email,folder = "","",""
    
    # Build .env content
    env = ""
    if name:   env += f'USER_NAME="{name}"\n'
    if email:  env += f'USER_EMAIL="{email}"\n'
    if folder: env += f'RESUME_FOLDER="{folder}"\n'

    if env:
        with open(".env", "w") as f: f.write(env)
        print("\n✓ .env file created with your details.")
    else:
        print("\nNo details provided. Skipping .env file creation.")

    print("  All data directories are in .gitignore")
    print("  Your resumes and personal data will NEVER be committed")
    
    print("\n⚙️  Next Steps:")
    print("  1. Set your resume folder:")
    print("     export RESUME_FOLDER=/path/to/your/resumes")
    print("\n  2. Run the pipeline:")
    print("     python scripts/1_scan_resume_folder.py")
    print("     python scripts/2_classify_files.py")
    print("\n  3. Or test with sample data:")
    print("     export RESUME_FOLDER=./examples/sample_resumes")
    print("     python scripts/1_scan_resume_folder.py")
    
    print("\n✅ Setup complete! Your data is safe and private.")

if __name__ == "__main__": setup()
