#!/bin/bash
# Install git pre-commit hook for privacy protection

echo "📦 Installing git pre-commit hook..."

if [ ! -f "hooks/pre-commit" ]; then
    echo "❌ Error: hooks/pre-commit not found"
    exit 1
fi

cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✅ Pre-commit hook installed!"
echo ""
echo "🔒 Privacy protection is now active!"
echo ""
echo "The hook will run before every commit to validate no PII is present."
echo "This protects you when using:"
echo "  • Command line (git commit)"
echo "  • Git UIs (VSCode, GitHub Desktop, etc.)"
echo "  • Any git operation that creates commits"
echo ""
echo "To bypass (not recommended): git commit --no-verify"
