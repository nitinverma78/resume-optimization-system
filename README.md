# Resume Optimization System

An AI-powered system that automatically generates optimized resumes and cover letters tailored to specific job descriptions by analyzing and learning from past successful applications.

## Overview

This system uses semantic search and LLM-based content generation to:
1. Retrieve relevant past resumes from Google Drive
2. Extract the best-matching experiences and accomplishments
3. Generate tailored resumes optimized for ATS and hiring managers
4. Create personalized cover letters with company research

## Tech Stack

- **Python 3.14** - Modern, stable Python environment (via Docker/UV)
- **uv** - Fast, reproducible Python package management
- **Docker** - Containerized execution for consistency and privacy
- **PyMuPDF** - PDF parsing and text extraction

## Project Structure

```
resume-optimization-system/
├── data/                      # Output data (GitIgnored)
│   ├── supply/                # Parsed resumes & classification
│   └── demand/                # Ingested JDs
├── simulate/                  # Simulation Data (Fake)
│   ├── input_resumes/         # Dummy resumes (for testing)
│   ├── input_jds/             # Dummy JDs
│   ├── sample_profile.json    # Example configuration
│   └── demo_classification_config.json
├── scripts/                   # Core Logic
│   ├── 1_scan_resume_folder.py
│   ├── 2_classify_files.py
│   ├── ... (Steps 3-10)
│   └── main.py                # CLI Entry Point
├── docker-compose.yml         # Container config
└── README.md                  # This file
```

## Quick Start (Simulation)

Run the full end-to-end simulation using "Jane Doe" (fake persona):

```bash
# Local simulation
python main.py --demo

# Docker simulation
docker compose run app python main.py --demo
```

## Setup

### Prerequisites
- Python 3.14+ OR Docker

### Installation

```bash
git clone <repo>
cd resume-optimization-system
uv sync
```

## Current Status

✅ **Phase 1: Supply Discovery** (Complete)
- Scans and classifies resumes (User vs Other)
- Extracts content (Skills, Experience, Education)
- Generates structured profile data

✅ **Phase 2: Infrastructure** (Complete)
- Dockerized setup for privacy
- `main.py` CLI runner
- Classification Test Suite

🚧 **Phase 3: Demand Discovery** (In Progress)
- Ingesting JDs (Raw + Classified)
- Matching Engine (Gap Analysis) - *Coming Soon*

## Persona: Jane Doe (Simulation)

- **Name**: Jane Doe
- **Role**: Software Engineer
- **Skills**: Python, Machine Learning, AWS, Docker


## Development Notes

- All dependencies managed via `uv` for reproducibility
- Python 3.14 chosen for latest performance improvements
- PDF parsing uses PyMuPDF for robust text extraction
- Structured data stored as JSON for easy processing

---

**Project Status**: Active Development  
**Last Updated**: 2026-01-01
