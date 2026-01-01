# AI Assistant Working Instructions
<!-- This file provides instructions for AI coding assistants like Cursor, Claude, and Antigravity -->

## Project Context

### Overview
Resume Optimization System - AI-first system for generating optimized resumes and cover letters by analyzing past application data and resume variations.

### Tech Stack
- **Python**: 3.14 (latest stable with GIL improvements)
- **Package Management**: `uv` (fast, reproducible dependency management)
- **Key Libraries**: pymupdf, pydantic, python-docx, openpyxl
- **Version Control**: Git + GitHub

### Project Structure
```
resume-optimization-system/
├── scripts/          # Modular processing scripts (numbered)
├── data/             # Generated data (inventories, classifications, KB)
├── profile-data/     # LinkedIn profile and structured data
├── .agent/           # Meta-instructions and workflows
└── pyproject.toml    # Dependencies and project config
```

---

## Command Execution Rules

### Always Explain Before Running
Before proposing ANY command, explain:
1. **Purpose**: What the command does
2. **Parameters**: What each parameter means
3. **Expected Outcome**: What will happen  
4. **Side Effects**: Any changes to files/system

**Example:**
```markdown
### Command: Install Dependencies
```bash
uv add openpyxl pydantic
```

**Purpose:** Install Python packages for Excel parsing and data validation  
**Parameters:**
- `openpyxl` - Library to read/write Excel files
- `pydantic` - Data validation using Python type hints
  
**What it does:** Downloads packages into `.venv` and updates `pyproject.toml`
```

### Never Auto-Run Destructive Operations
The following require explicit approval (SafeToAutoRun=false):
- Git operations (commit, push, pull, merge)
- File deletions or moves
- System-level changes
- Package installations
- Database modifications

### Safe Auto-Run Examples
These are safe to auto-run (SafeToAutoRun=true):
- Reading files
- Running scripts that only output data
- Creating directories (mkdir -p)
- Running tests (read-only verification)

---

## Git Workflow Standards

### Commit Checkpoints
- **Remind before major phase boundaries**: Before starting new phases (e.g., Phase 1 → Phase 2)
- **Show git status**: Display what's changed before suggesting commit
- **Suggest meaningful commit messages**: Include what was accomplished, not just "update files"

### Commit Message Format
```
<type>: <concise description>

<optional detailed explanation>
```

**Types**: feat, fix, refactor, docs, test, chore

**Example:**
```bash
git commit -m "feat: Phase 1 complete - file discovery and classification (181 user documents)"
```

### Before Major Changes
Always suggest:
```bash
git status
git add .
git commit -m "[message]"
git push origin main
```

---

## Code Style & Standards

### Python Standards
- **Python Version**: 3.14 minimum
- **Type Hints**: Use type hints for all function signatures
- **Data Models**: Use Pydantic for structured data
- **Docstrings**: Google-style docstrings for functions and classes
- **Error Handling**: Explicit try/except with descriptive messages
- **Package Management**: ALWAYS use `uv`, NEVER use `pip`

### Pydantic Models
```python
from pydantic import BaseModel

class FileInfo(BaseModel):
    """Model for file information."""
    path: str
    name: str
    extension: str
    size_bytes: int
```

### Script Naming
- **Numbered for pipeline order**: `1_scan_folder.py`, `2_classify.py`
- **Descriptive names**: `extract_metadata.py`, not just `process.py`
- **Snake_case**: All lowercase with underscores

### File Organization
- **Modular scripts**: Each script does ONE thing well
- **Data separation**: Generated data in `data/`, source code in `scripts/`
- **Version control**: Include `.gitignore` for generated files

---

## Coding Patterns & Preferences

### Fast.ai Coding Style
Based on [fast.ai style guide](https://docs.fast.ai/dev/style.html) - informed by APL/J/K and "Notation as a Tool For Thought"

**Core Philosophy:**
- **Brevity facilitates reasoning** - Keep concepts within one screenful (~160 chars width)
- **One line = one complete idea** - Easier to understand at a glance
- **Domain-specific abbreviations** - Assume domain knowledge in naming

**Naming Conventions:**
```python
# Common abbreviations (use liberally)
sz      # size
img     # image  
txt     # text
doc     # document
cls     # classification
meta    # metadata
ext     # extension
dir     # directory

# Comprehensions and loops
o       # object in comprehension
i       # index
k,v     # key, value in dict comprehension

# Domain-specific (resume parsing)
cl      # cover letter
res     # resume
jd      # job description
```

**Layout & Structure:**
```python
# One-line functions with similar purpose - no blank lines between
def extract_pdf(p): return pymupdf.open(p).get_text()
def extract_docx(p): return Document(p).text
def extract_pptx(p): return Presentation(p).slides.text

# Align similar concepts to show differences
if typ == 'pdf':  text = extract_pdf(path)
elif typ == 'docx': text = extract_docx(path)
elif typ == 'pptx': text = extract_pptx(path)

# Destructuring assignment - no spaces after commas
self.sz,self.ext,self.path = sz,ext,path

# Import commonly used modules together
import json, re, pymupdf, pathlib
from pathlib import Path

# Ternary for simple conditionals  
category = 'resume' if has_sections else 'other'
```

**What NOT to Do:**
- ❌ Don't use auto-linters/formatters (autopep8, yapf, black)
- ❌ Don't add unnecessary vertical space
- ❌ Don't use overly long symbol names (`kullback_leibler_divergence` → `kl_divergence`)
- ❌ Don't scroll - keep concepts on one screen

**When to Apply:**
- ✅ New code should follow these principles
- ✅ Refactoring can adopt this style incrementally
- ⚠️ Don't reformat existing code just for style - only when making functional changes

---

### Code Style References
- **[fast.ai style guide](https://docs.fast.ai/dev/style.html)** - Primary reference for this project
<!-- TODO: Add your other repo references -->

### Function Structure
```python
def function_name(param: Type) -> ReturnType:
    """
    Brief description of what function does.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    # Implementation
    return result
```

### Error Messages
- Be specific about what went wrong
- Suggest how to fix it
- Include relevant file paths or values

**Example:**
```python
if not file_path.exists():
    print(f"Error: File not found: {file_path}")
    print("Please update the path in the script.")
    return
```

---

## Decision Making & Problem Solving

### Content Over Names
**ALWAYS read and analyze actual file content**, not just filenames
- Extract text from PDFs/DOCX before classifying
- Look for specific patterns and keywords IN the content
- Don't rely solely on filename heuristics

### When Classification is Unclear
1. Extract and show actual content snippet
2. Explain what patterns you're seeing
3. Show the logic: "Has X indicators, lacks Y, therefore Z"
4. Ask for user confirmation if uncertain

### Iterative Refinement
- When user points out mistakes, fix immediately
- Don't defend wrong decisions - acknowledge and correct
- Update logic to prevent same mistake in future
- Track known issues in backlog

### Ask, Don't Assume
- If requirements are unclear, ASK clarifying questions
- List options and trade-offs when multiple approaches exist
- Don't make architectural decisions without user input

---

## Communication Style

### Conciseness
- Get to the point quickly
- Don't repeat what user already knows
- Use bullet points, not paragraphs
- Code examples > lengthy explanations

### Formatting
- Use markdown: headers, code blocks, lists, tables
- **Bold** for important points
- `Backticks` for file/function/variable names
- ✅ ❌ for status indicators

### Explain Reasoning
When making decisions, briefly explain WHY:
- "Classified as presentation because has 3+ presentation keywords AND no resume structure"
- "Using word count <600 to distinguish cover letters from combined docs"

### No Fluff
Avoid:
- Apologizing repeatedly
- Over-explaining obvious things
- Generic statements like "This is a great question!"
- Asking "Does this make sense?" after every explanation

---

## Testing & Validation

### Verify Before Claiming Success
- Actually RUN the code/script
- Check the OUTPUT matches expectations
- Don't just say "this should work" - verify it does

### Incremental Testing
- Test each script after creation
- Verify outputs before moving to next step
- Show actual results, not just "completed successfully"

### Example Verification
```python
# After running classifier
print(f"✓ Found {len(user_resumes)} user resumes")
print(f"✓ Found {len(cover_letters)} cover letters")

# Show samples
print("Sample user resumes:")
for resume in user_resumes[:3]:
    print(f"  - {resume['name']}")
```

---

## Workflow Management

### Task Tracking
- Update `task.md` artifact as work progresses
- Mark items `[/]` when in-progress, `[x]` when complete
- Add new items to backlog as issues are discovered

### Known Issues
Maintain backlog section in `task.md`:
```markdown
## Known Issues / Backlog
- [ ] Issue description with context
- [ ] Another issue to fix later
```

### Phase Boundaries
Clear separation between phases:
1. **Planning**: Design, create implementation plan
2. **Execution**: Build scripts, process data
3. **Verification**: Test, validate, create walkthrough

---

## Project-Specific Rules

### Resume Classification
- **Ownership detection**: If filename OR content has "Nitin Verma", it's user's document
- **Type detection**: Analyze structure (sections, bullets, cover letter phrases)
- **Word count heuristics**: 
  - Cover letters: < 600 words
  - Resumes: > 600 words
  - Combined: > 1200 words

### File Processing
- **Read full content**: Don't just analyze first page
- **Handle multiple formats**: PDF, DOCX, old .doc, PPTX
- **Skip deleted files**: Handle missing files gracefully

### Metadata Extraction (Upcoming)
- Extract company from filename first, then content
- Identify role from summary section or filename
- Use file modified date as application date

---

## Best Practices Summary

✅ **DO:**
- Read actual content before making decisions
- Explain commands before running them
- Use type hints and Pydantic models
- Test and verify outputs
- Track known issues in backlog
- Ask clarifying questions
- Show reasoning for decisions

❌ **DON'T:**
- Use `pip` (use `uv` instead)
- Auto-run git/destructive commands
- Classify based on filename alone
- Assume - ask instead
- Over-apologize
- Claim success without verification

---

## Notes & TODOs

<!-- Nitin: Add your coding style repo references here -->
<!-- Nitin: Update with any additional preferences as we work together -->
