# Sample Resume Data

This directory contains **fake sample data** for testing the Resume Optimization System.

## Contents

- `sample_resumes/` - Sample resume and cover letter files (fake data)
- `sample_profile.json` - Example LinkedIn profile structure
- `expected_output/` - What the pipeline produces

## Purpose

These examples allow you to:
1. **Test the system** without using your real resumes
2. **Understand data formats** expected by the scripts
3. **Verify installation** works correctly

## Your Real Data

Your actual resume data should go in:
- `data/` - Processing outputs (`.gitignore`'d)
- `profile-data/` - Your LinkedIn profile (`.gitignore`'d)
- Custom folder for your resumes (set via `RESUME_FOLDER` env var)

**These folders are not committed to git - your data stays private!**

## Quick Test

```bash
# Run scanner on sample data
export RESUME_FOLDER=./examples/sample_resumes
python scripts/1_scan_resume_folder.py
```
