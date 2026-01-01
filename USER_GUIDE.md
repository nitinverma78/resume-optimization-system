# User Guide: Running the Resume Optimization System

## Required Parameters

When running the system with YOUR data, set these parameters:

---

## 1. Environment Variables

```bash
# Your personal information
export USER_NAME="Your Full Name"  # e.g., "Jane Doe"

# Your resume folder location
export RESUME_FOLDER="$HOME/Downloads/MyResumes"  # Change to your actual folder

# LinkedIn profile PDF location (if different from default)
export LINKEDIN_PDF="./profile-data/MyLinkedInProfile.pdf"  # Change to your PDF name
```

---

## 2. Running the Pipeline

### Step 1: Scan Your Resume Folder
```bash
python scripts/1_scan_resume_folder.py
```
- Uses: `RESUME_FOLDER` → e.g., `/Users/yourname/Downloads/MyResumes`
- Default: `~/Downloads/MyResumes` (you override with your actual folder)
- Output: `data/file_inventory.json`

### Step 2: Classify Files
```bash
python scripts/2_classify_files.py
```
- Uses: `USER_NAME` → e.g., `"Jane Doe"` (to detect your documents)
- Default: `"YOUR_NAME"` (you must set this)
- Output: `data/classified_files.json`

### Step 3: Generate Report
```bash
python scripts/generate_classification_report.py
```
- Uses: `data/classified_files.json`
- Output: `data/classification_report.md`

### Step 4: Create Profile Database
```bash
python scripts/create_profile_db.py
```
- Uses: `USER_NAME` → `"Nitin Verma"`
- Uses: LinkedIn PDF (default: `profile-data/MyLinkedInProfile.pdf`)
- Output: `profile-data/profile-structured.json`

---

## 3. Security Audit

Before making repo public, verify no personal info leaked:

```bash
# Set YOUR information
YOUR_NAME="Your Full Name"  # e.g., "Jane Doe"
YOUR_USERNAME="yourname"      # e.g., "jane"

# Run checks from SECURITY_AUDIT.md
git grep -i "$YOUR_NAME"              # Should find ZERO matches
git grep -i "/Users/$YOUR_USERNAME"   # Should find ZERO matches
git ls-files | grep -E '\.(pdf|docx)$' # Should find ZERO files
```

---

## Quick Reference

| Parameter | Your Actual Value | Default (Generic) | Purpose |
|-----------|------------------|-------------------|---------|
| `USER_NAME` | `"Your Full Name"` | `"YOUR_NAME"` | Detect your docs |
| `RESUME_FOLDER` | `~/Downloads/MyResumes` | `~/Downloads/MyResumes` | Your resume location |
| `LINKEDIN_PDF` | `MyLinkedInProfile.pdf` | `MyLinkedInProfile.pdf` | Your profile |
| `YOUR_USERNAME` | `"yourname"` | N/A | Security audit only |

**Note:** The code defaults are now GENERIC (`MyResumes`, `MyLinkedInProfile`). You override with YOUR actual locations.

---

## Email Addresses

The app does **NOT** look for or use email addresses. It only uses:
- `USER_NAME` (your full name for document detection)
- File/folder paths

No email configuration needed! ✅

---

## Complete Setup Example

```bash
# One-time setup
export USER_NAME="Your Full Name"
export RESUME_FOLDER="$HOME/Downloads/MyResumes"

# Run complete pipeline
python scripts/1_scan_resume_folder.py
python scripts/2_classify_files.py
python scripts/generate_classification_report.py
python scripts/create_profile_db.py

# Before going public, run security audit
YOUR_NAME="Your Full Name"
YOUR_USERNAME="yourname"
git grep -i "$YOUR_NAME"
git grep -i "/Users/$YOUR_USERNAME"
```

---

## Summary

**You MUST set:** `USER_NAME="Your Full Name"`  
**You SHOULD set:** `RESUME_FOLDER` (change from default if needed)  
**For security audit:** Also set `YOUR_USERNAME="yourname"`

Everything else uses defaults that are already generic! 🎉
