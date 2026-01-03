# Resume Optimization System

![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)
![Docker](https://img.shields.io/badge/docker-available-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Turn your chaotic folder of PDF resumes into a structured, queryable knowledge base—and generate tailored resumes for every job application.**

This system uses local AI models and semantic search to analyze your past resumes, understand your experiences, and automatically tailor your profile to match new job descriptions.

---

## 🏗️ Architecture

```mermaid
graph TD
    subgraph "Phase 1: Supply (Your Data)"
        Raw[Reference Resumes (PDFs)] -->|Scanning| Inventory[Inventory JSON]
        Inventory -->|Classification| Classified[Classified Resumes]
        Classified -->|Extraction| Chunks[Content Chunks]
        Chunks -->|Structuring| Profile[Structured Profile DB]
    end

    subgraph "Phase 2: Demand (Job Market)"
        JD[Job Description] -->|Ingestion| JD_Parsed[Parsed Role Requirements]
    end

    subgraph "Phase 3: Matching"
        Profile & JD_Parsed -->|Gap Analysis| Match[Match Score & Gaps]
        Match -->|Optimization| Final[Tailored Resume.md]
    end
```

## ✨ Features

-   **Intelligent Classification**: Automatically distinguishes between your resumes, cover letters, and random files in your folder.
-   **Structured Extraction**: Converts unstructured PDF text into structured JSON data (Skills, Experience, Education).
-   **Privacy First**: Runs entirely locally (or in Docker). Your personal PII never leaves your machine.
-   **Semantic Matching**: Matches your actual experience to job requirements, not just keyword stuffing.
-   **Simulation Mode**: Includes a full "Jane Doe" dummy dataset to test the pipeline without using your own data.

## 🚀 Quick Start

You can run the system in **Simulation Mode** (using fake data) or **Real Mode** (using your data).

### Option A: Simulation (Try it out!)

Generate a tailored resume for "Jane Doe" applying for a Software Engineer role.

**Using Docker (Recommended):**
```bash
docker compose run app python main.py --demo
```

**Using Local Python:**
```bash
# Requires Python 3.14+ and uv
uv sync
python main.py --demo
```

### Option B: Real Usage (Your Data)

1.  **Set Environment Variables**:
    You must tell the system who you are and where your PDF resumes live.

    ```bash
    export USER_NAME="Your Full Name"
    export USER_EMAIL="you@email.com"
    export RESUME_FOLDER="/absolute/path/to/your/pdf_resumes"
    ```

2.  **Run the Pipeline**:
    ```bash
    python main.py
    ```

    *This will scan your folder, build your profile, and prepare the system for matching.*

## 📂 Project Structure

The pipeline is divided into clear phases:

| Phase | Script | Description |
| :--- | :--- | :--- |
| **1. Supply** | `scripts/1_scan...` | Scans `RESUME_FOLDER` for files. |
| | `scripts/2_classify...` | Identifies which files are *yours* vs. others. |
| | `scripts/5_extract...` | OCRs and parses text from PDFs. |
| | `scripts/8_create...` | Builds `profile-structured.json`. |
| **2. Demand** | `scripts/10_ingest...` | Parses Job Descriptions from `data/demand`. |
| **3. Match** | `scripts/11_match...` | Compares your profile to JDs. |

Data is stored in `data/` (or `simulate/data` for demos), which is git-ignored to protect your privacy.

## 🛠️ Configuration

Configuration is handled via environment variables (see Quick Start) or `.env` file.

**Key Config Files:**
-   `config/classification_config.json`: rules for file classification.
-   `simulate/sample_profile.json`: baseline data for the simulation persona.

## 🔒 Privacy & Security

-   **Local Execution**: All processing happens on your machine.
-   **Git Ignore**: The `data/` directory is strictly ignored to prevent accidental commits of personal info.
-   **PII Stripping**: The codebase includes tools to strip PII from logs and internal datasets.

## 📋 Requirements

-   **Python**: 3.14 or higher
-   **Dependencies**: managed via `uv` (see `pyproject.toml`)
-   **Docker**: Optional, but recommended for isolation.
