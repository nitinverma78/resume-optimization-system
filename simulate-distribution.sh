#!/bin/bash
# End-User Distribution Simulation Script
# This mimics the "Build Once, Run Anywhere" flow

set -e

echo "🏭 STEP 1: Mainainer (You) Builds the Image"
REPO_ROOT="$PWD"
# In real life, you'd do: docker build -t generic-user/resume-optimizer:v1 .
# For simulation, we'll just tag it locally
docker build -t local-resume-optimizer:latest .
echo "✅ Image built: local-resume-optimizer:latest"
echo ""

echo "📦 STEP 2: create Clean 'End-User' Environment"
USER_DIR=~/resume-app-user
rm -rf "$USER_DIR"
mkdir -p "$USER_DIR"
cd "$USER_DIR"

# ---------------------------------------------------------
# CRITICAL: Copy ONLY what the end-user needs
# NO source code, NO scripts, NO Dockerfile
# ---------------------------------------------------------

# 1. The Compose File (Modified to use image instead of build)
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  # Demo mode
  demo:
    image: local-resume-optimizer:latest
    command: python main.py --demo
    volumes:
      - ./simulate_output:/app/simulate/data

  # Normal mode
  app:
    image: local-resume-optimizer:latest
    env_file: .env
    environment:
      - RESUME_FOLDER=/input_resumes
    volumes:
      # Mount the user's resume folder (Must be set in .env)
      # Falback to current dir if unset (just to pass docker validation)
      - \${RESUME_FOLDER:-.}:/input_resumes:ro
      - ./data:/app/data
EOF

# 2. Key Config (Env file template)
# We copy the example, but the user must fill it in.
cp "$REPO_ROOT/.env.example" ./.env

echo "⚠️ NOTE: We copied .env.example to .env. You MUST edit it with your details!"

echo "✅ Environment created at $USER_DIR"
echo "📂 Contents of user folder (Notice: NO CODE!):"
ls -la
echo ""

echo "🚀 STEP 3: User Runs the App"
echo "Run these commands to verify:"
echo ""
echo "  cd $USER_DIR"
echo ""
echo "  # Demo Mode (simulation):"
echo "  docker compose run --rm demo"
echo ""
echo "  # Normal Mode (real data):"
echo "  docker compose run --rm app"
echo ""
echo "Notice Docker uses the pre-built image. It does NOT need to build anything."
