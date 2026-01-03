#!/bin/bash
# Clean Docker Test Setup Script
# This creates an isolated directory to test Docker without mixing with local runs

set -e

echo "🧪 Setting up clean Docker test environment..."

# Create test directory
TEST_DIR=~/docker-test-resume-app
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "📁 Created clean directory: $TEST_DIR"

# Copy only Docker-related files
cp /Users/nitin/.gemini/antigravity/scratch/resume-optimization-system/Dockerfile .
cp /Users/nitin/.gemini/antigravity/scratch/resume-optimization-system/docker-compose.yml .
cp /Users/nitin/.gemini/antigravity/scratch/resume-optimization-system/pyproject.toml .
cp /Users/nitin/.gemini/antigravity/scratch/resume-optimization-system/uv.lock .
cp /Users/nitin/.gemini/antigravity/scratch/resume-optimization-system/main.py .
cp /Users/nitin/.gemini/antigravity/scratch/resume-optimization-system/.env .
cp -r /Users/nitin/.gemini/antigravity/scratch/resume-optimization-system/scripts .
cp -r /Users/nitin/.gemini/antigravity/scratch/resume-optimization-system/hooks .
cp -r /Users/nitin/.gemini/antigravity/scratch/resume-optimization-system/simulate .
cp -r /Users/nitin/.gemini/antigravity/scratch/resume-optimization-system/config .

echo "✅ Files copied"
echo ""
echo "📂 Current directory structure:"
ls -la
echo ""
echo "🎯 Ready to test! Run these commands:"
echo ""
echo "  cd $TEST_DIR"
echo ""
echo "  # Demo mode (no data/ folder needed):"
echo "  docker compose run --rm demo"
echo ""
echo "  # Normal mode (will create data/ folder):"
echo "  docker compose run --rm app"
echo ""
echo "  # After running, check what was generated:"
echo "  ls -R data/"
