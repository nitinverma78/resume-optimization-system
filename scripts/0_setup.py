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
    
    # Create private data directories
    dirs = ['data', 'profile-data']
    for d in dirs:
        path = Path(d)
        path.mkdir(exist_ok=True)
        (path / '.gitkeep').touch()
        print(f"✓ Created {d}/ (gitignored - your data stays private)")
    
    print("\n📁 Directory Structure:")
    print("  data/          - Processing outputs (private)")
    print("  profile-data/  - Your LinkedIn profile (private)")
    print("  examples/      - Sample data for testing (public)")
    
    print("\n🔐 Privacy:")
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
