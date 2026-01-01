# Resume Optimization System

An AI-powered system that automatically generates optimized resumes and cover letters tailored to specific job descriptions by analyzing and learning from past successful applications.

## Overview

This system uses semantic search and LLM-based content generation to:
1. Retrieve relevant past resumes from Google Drive
2. Extract the best-matching experiences and accomplishments
3. Generate tailored resumes optimized for ATS and hiring managers
4. Create personalized cover letters with company research

## Tech Stack

- **Python 3.14** - Latest stable Python with modern performance improvements
- **uv** - Fast, reproducible Python package management
- **PyMuPDF** - PDF parsing and text extraction
- **LLM Integration** (planned) - GPT-4/Claude/Gemini for content generation
- **Vector Database** (planned) - For semantic search of resume library

## Project Structure

```
resume-optimization-system/
├── profile-data/              # Your LinkedIn profile and structured data
│   ├── NitinVermaLinkedInProfile.pdf
│   ├── linkedin-profile-parsed.json
│   └── profile-structured.json
├── samples/                   # Manual optimization examples (to be added)
│   └── role-{N}-{company}/
│       ├── job-description.txt
│       ├── final-resume.pdf
│       ├── source-resumes/
│       └── notes.md
├── scripts/                   # Utility scripts
│   ├── parse_linkedin_pdf.py
│   └── create_profile_db.py
├── pyproject.toml            # Project dependencies
└── README.md                 # This file
```

## Setup

### Prerequisites
- Python 3.14
- uv (installed automatically if not present)

### Installation

```bash
# Clone/navigate to the project
cd resume-optimization-system

# Install dependencies (uv will create a virtual environment automatically)
uv sync

# Verify installation
uv run python3 --version
```

### Running Scripts

```bash
# Parse LinkedIn PDF
uv run python3 scripts/parse_linkedin_pdf.py

# Create structured profile database
uv run python3 scripts/create_profile_db.py
```

## Current Status

✅ **Phase 1: Profile Data Processing** (Complete)
- Parsed LinkedIn profile PDF
- Extracted structured data (name, headline, summary, skills, experiences, education, patents)
- Created searchable profile database

🚧 **Phase 2: Manual Process Analysis** (Pending)
- Awaiting sample applications to analyze manual optimization process

📋 **Phase 3: AI System Design** (Planned)
- Design retrieval & ranking system
- Build resume optimization engine
- Create cover letter generator
- Add Google Drive integration

## Next Steps

1. **Add Manual Samples**: Place 2-3 examples of past applications in `samples/` folder
2. **Analyze Patterns**: Review how you manually optimized resumes
3. **Design AI System**: Create implementation plan for autonomous optimization
4. **Build MVP**: Implement core resume generation functionality

## Profile Summary

- **Name**: Nitin Verma
- **Headline**: AI & Technology Executive | CTO / CAIO Leadership
- **Experience**: 25+ years across Amazon, Staples, Zulily, FICO, and more
- **Education**: Wharton MBA, UNC MS (Stats & OR), IIT Madras BTech
- **Patents**: 4+ in AI/ML and robotics
- **Skills**: AI Strategy, Agentic AI, Cloud Infrastructure, Team Building

## Development Notes

- All dependencies managed via `uv` for reproducibility
- Python 3.14 chosen for latest performance improvements
- PDF parsing uses PyMuPDF for robust text extraction
- Structured data stored as JSON for easy processing

---

**Project Status**: Active Development  
**Last Updated**: 2026-01-01
