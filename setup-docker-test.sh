#!/bin/bash
# Clean Docker Test Setup Script
# This creates an isolated directory to test Docker without mixing with local runs

set -e

echo "🧪 Setting up clean Docker test environment..."

REPO_ROOT="$PWD"

# Create test directory
TEST_DIR=~/docker-test-resume-app
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "📁 Created clean directory: $TEST_DIR"

# Copy only Docker-related files
cp "$REPO_ROOT/Dockerfile" .
cp "$REPO_ROOT/docker-compose.yml" .
cp "$REPO_ROOT/pyproject.toml" .
cp "$REPO_ROOT/uv.lock" .
cp "$REPO_ROOT/main.py" .
cp "$REPO_ROOT/.env" .
cp -r "$REPO_ROOT/scripts" .
cp -r "$REPO_ROOT/hooks" .
cp -r "$REPO_ROOT/simulate" .
cp -r "$REPO_ROOT/config" .

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
