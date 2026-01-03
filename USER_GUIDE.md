# User Guide: Running the Resume Optimization System

## Required Parameters

When running the system with YOUR data, set these parameters:

---

## 1. Environment Variables

```bash
# Your personal information
export USER_NAME="Your Full Name"  # e.g., "Jane Doe"
export USER_EMAIL="you@example.com"

# Your resume folder location
export RESUME_FOLDER="/path/to/your/resumes"

# LINKEDIN_PDF is auto-detected in RESUME_FOLDER
```

---

## 2. Running the Pipeline

### Step 1: Scan Your Resume Folder
```bash
python scripts/1_scan_resume_folder.py
```
- Uses: `RESUME_FOLDER` → e.g., `/Users/yourname/Documents/Resumes`
- **Output:** `data/supply/1_file_inventory.json`
  *(Note: Normal runs output to `data/`. Simulation runs output to `simulate/data/`.)*

### Step 2: Classify Files
```bash
python scripts/2_classify_files.py
```
- Uses: `USER_NAME` to detect ownership.
- **Output:** `data/supply/2_file_inventory.json`

### Validation
Run the test suite to confirm everything is classified correctly:
```bash
python scripts/2_confirm.py
```

### Step 3: Generate Report
```bash
python scripts/3_classification_report.py
```
- Output: `data/supply/2_classification_report.md`

### Step 9: Generate Profile
```bash
python scripts/9_generate_profile_md.py
```
- Requires: `USER_EMAIL` and `USER_NAME`.
- Output: `data/supply/profile_data/linkedin-profile.md`

---

## 3. Security Audit

Before making repo public, verify no personal info leaked:

```bash
# Set YOUR information
YOUR_NAME="Your Full Name"
YOUR_USERNAME="yourname"

# Run checks from SECURITY_AUDIT.md
git grep -i "$YOUR_NAME"              # Should find ZERO matches
git grep -i "/Users/$YOUR_USERNAME"   # Should find ZERO matches
```

---

## Quick Reference

| Parameter | Example Value | Purpose |
|-----------|------------------|---------|
| `USER_NAME` | `"Jane Doe"` | Detect your docs |
| `USER_EMAIL` | `"jane@example.com"` | ID matching |
| `RESUME_FOLDER` | `/path/to/resumes` | Input source |

**Note:** The code has NO defaults. You MUST set these environment variables.

---

## Complete Setup Example

```bash
# One-time setup
export USER_NAME="Jane Doe"
export USER_EMAIL="jane@example.com"
export RESUME_FOLDER="$HOME/Documents/Resumes"

# Run complete pipeline
python main.py
```
