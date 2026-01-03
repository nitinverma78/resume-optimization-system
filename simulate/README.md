# Simulation Data

This directory contains **fake data** for simulating the Resume Optimization System end-to-end.

## Contents

- **`config/`** - Test configuration for validation
  - `classification_config.json` - Test cases verifying classification works correctly
- **`input_resumes/`** - Demo input files (matches production `RESUME_FOLDER` structure)
  - `JaneDoe_Resume.txt` - Jane's sample resume
  - `MyLinkedInProfile.pdf` - Jane's LinkedIn profile export
  - `SoftwareEngineer_JD.txt` - Demo job description (gets classified as "job_descriptions" in Step 2)

All files use the "Jane Doe" persona with fake companies and generic data.

## Running the Simulation

Use the built-in demo flag to verify installation and docker setup:

```bash
# Verify system using "Jane Doe" simulation
python main.py --demo
```

This will:
1. Temporarily point `RESUME_FOLDER` to `simulate/input_resumes`.
2. Set virtual identity to **Jane Doe** (`jane.doe@example.com`).
3. Run the full 11-step pipeline to prove functionality.

## Verifying Docker Setup

To verify your Docker build works using the simulation:

```bash
docker compose run app python main.py --demo
```

## Generated Output (Local Only)

When you run the simulation, a `simulate/data/` directory is created. This ensures your real `data/` folder is never touched.

```text
simulate/data/
├── supply/                          # Extracted resume data
│   ├── 1_file_inventory.json        # All scanned files
│   ├── 2_file_inventory.json        # Classified files
│   ├── 4_section_headers.json       # Detected section headers
│   ├── 5_extracted_content.json     # Raw text content
│   ├── 6_knowledge_base.json        # Consolidated skills/entities
│   └── profile_data/                # Finalized Jane Doe profile
│       ├── linkedin-profile-parsed.json
│       ├── profile-structured.json  # The Master Profile
│       └── linkedin-profile.md      # Markdown version
├── demand/                          # Job Market data
│   └── 1_jd_database.json           # Ingested JDs
└── matching/                        # Analysis results
    ├── 11_gap_analysis.json         # Fit scores
    └── 11_gap_analysis_report.md    # Actionable advice
```
