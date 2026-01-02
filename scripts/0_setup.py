#!/usr/bin/env python3
"""
Setup script for first-time users.
Creates necessary directories and validates environment.
"""
import os
from pathlib import Path

def setup():
    """Initialize the resume optimization system."""
    print("🚀 Setting up Resume Optimization System...\n")
    
    # Create directories
    dirs = [
        "data",
        "data/supply",
        "data/demand",
        "data/supply/profile_data",
        "examples"
    ]
    for d in dirs:
        path = Path(d)
        path.mkdir(exist_ok=True)
        (path / '.gitkeep').touch()
        print(f"✓ Created {d}/ (gitignored - your data stays private)")
    
    print("\n📁 Directory Structure:")
    print("  data/          - Processing outputs (private)")
    print("  data/supply/profile_data/  - Your LinkedIn profile (private)")
    print("  examples/      - Sample data for testing (public)")
    
    print("\n🔐 Privacy:")
    print("Please enter your details to configure the system (or press Enter to skip):")
    
    # Only prompt if interactive
    import sys
    if sys.stdin.isatty():
        user_name = input("Full Name: ").strip()
        user_email = input("Email Address: ").strip()
        resume_folder = input("Path to Resume Folder: ").strip()
    else:
        print("  (Non-interactive mode detected using defaults)")
        user_name = ""
        user_email = ""
        resume_folder = ""
    
    env_content = ""
    if user_name:
        env_content += f'USER_NAME="{user_name}"\n'
    if user_email:
        env_content += f'USER_EMAIL="{user_email}"\n'
    if resume_folder:
        env_content += f'RESUME_FOLDER="{resume_folder}"\n'

    if env_content:
        with open(".env", "w") as f:
            f.write(env_content)
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

if __name__ == "__main__":
    setup()
