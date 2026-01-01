# Security Audit Checklist - Public Release

Run this checklist before making the repository public.

## 1. Check Git History for Private Data

```bash
# Search for any committed files in private directories
git log --all --full-history --source -- data/ profile-data/

# Should return: (empty) or only .gitkeep files
```

**Expected:** No results (or only .gitkeep commits)

---

## 2. Verify No Private Files Committed

```bash
# Check for resume/document files
git ls-files | grep -E '\.(pdf|docx|doc|xlsx|pptx)$'

# Should return: (empty)
```

**Expected:** No files found

---

## 3. Search for Personal Information in Code

```bash
# Replace YOUR_NAME with your actual name
YOUR_NAME="John Doe"  # Set this to your name
YOUR_USERNAME="john"  # Set this to your system username

# Search for your name (case-insensitive)
git grep -i "$YOUR_NAME"

# Search for personal emails
git grep -E "[a-z]+@[a-z]+\.(com|ai|net)"

# Search for hardcoded paths with your username
git grep -i "/Users/$YOUR_USERNAME"
git grep -i "Downloads/MyResumes"
```

**Expected:** Only in examples/sample_profile.json or comments

---

## 4. Review Currently Tracked Files

```bash
# List all files in git
git ls-files

# Review data directories
git ls-files data/ profile-data/
```

**Expected:** Only .gitkeep files in data directories

---

## 5. Test .gitignore is Working

```bash
# Try to add a private file
touch data/test-private.json
git status

# Should show: nothing to commit (or only show new untracked files you want)
rm data/test-private.json
```

**Expected:** test-private.json not shown in `git status`

---

## 6. Verify Sample Data is Safe

```bash
# Check examples directory
cat examples/sample_profile.json

# Ensure it's fake data
```

**Expected:** Generic names like "Jane Doe", fake companies

---

## 7. Clean Git History (if needed)

If you find private data in git history:

```bash
# Option 1: Remove specific file from all history (DESTRUCTIVE)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/private/file" \
  --prune-empty --tag-name-filter cat -- --all

# Option 2: Start fresh repository (NUCLEAR OPTION)
# 1. Delete .git folder
# 2. git init
# 3. git add .
# 4. git commit -m "Initial commit"
```

⚠️ **Warning:** This rewrites history. Only do if necessary.

---

## 8. Final Checks

- [ ] .gitignore includes all private directories
- [ ] No .pdf/.docx files committed
- [ ] No personal information in code
- [ ] examples/ contains only fake data
- [ ] README updated for public users
- [ ] setup.py script works
- [ ] Environment variables documented in .env.example

---

## 9. Test Fresh Clone (Recommended)

```bash
# Clone to a new location
cd /tmp
git clone /path/to/your/repo resume-test
cd resume-test

# Run setup
python scripts/setup.py

# Try with sample data
export RESUME_FOLDER=./examples/sample_resumes
python scripts/1_scan_resume_folder.py
```

**Expected:** Everything works without your private data

---

## ✅ Ready to Make Public

Once all checks pass:

```bash
# On GitHub
# 1. Go to Settings
# 2. Scroll to "Danger Zone"
# 3. Change visibility to "Public"
```

Your private data is safe! 🔒
