# Simulation Data

This directory contains **fake data** for simulating the Resume Optimization System end-to-end.

## Contents
- `input_resumes/` - Dummy resumes (matches Docker `/input_resumes` volume).
  - `JaneDoe_Resume.txt` - Jane's resume
  - `MyLinkedInProfile.pdf` - Jane's LinkedIn export
- `input_jds/` - Dummy Job Descriptions.
- `config/classification_config.json` - Test cases for the dummy data.

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
