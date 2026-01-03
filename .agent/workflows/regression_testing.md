---
description: Run full end-to-end regression tests (Pipeline, Privacy, Docker Distribution)
---

# 1. Direct Code Execution Tests
1. Run Pipeline (Demo Mode) - Verifies simulation logic
// turbo
.venv/bin/python main.py --demo

2. Run Pipeline (Normal Mode) - Verifies real data processing
// turbo
.venv/bin/python main.py

3. Validate Data Isolation - Verifies ownership of processed data
// turbo
PYTHONPATH=. .venv/bin/python scripts/validate_data_isolation.py

4. Validate Git Privacy - Verifies no PII in tracked files (Strict)
// turbo
.venv/bin/python -m scripts.validate_git_privacy --check-user "Nitin" --check-email "nitin"

# 2. Docker Development Environment Tests
5. Setup Dev Environment (Copy Repo to ~/docker-test-resume-app)
// turbo
bash setup-docker-test.sh

6. Verify Dev Container: Demo Mode (Simulated Data)
// turbo
cd ~/docker-test-resume-app && docker compose run --rm demo

7. Verify Dev Container: App Mode (Real Data, Host Mounted)
// turbo
cd ~/docker-test-resume-app && docker compose run --rm app

# 3. Docker Distribution Tests
8. Simulate Distribution (Build Image -> ~/resume-app-user)
// turbo
bash simulate-distribution.sh

9. Verify Distro Container: Demo Mode (Simulated Data)
// turbo
cd ~/resume-app-user && docker compose run --rm demo

10. Verify Distro Container: App Mode (Real Data, Host Mounted)
// turbo
cd ~/resume-app-user && docker compose run --rm app
