# Git Hook for Privacy Protection

## Overview
This directory contains a git `pre-commit` hook that prevents accidental commits of PII (Personally Identifiable Information).

## Installation

Run the installation script:
```bash
./hooks/install.sh
```

This will install the `pre-commit` hook into `.git/hooks/`.

## What Gets Checked

The hook runs `scripts/validate_git_privacy.py` before every commit, scanning all git-tracked files for configured PII (name and email).

If any PII is found, the commit is **blocked** until you fix the violations.

## Protection Coverage

This hook protects you across **all git interfaces**:
- ✅ Command line (`git commit`)
- ✅ VSCode Source Control
- ✅ GitHub Desktop
- ✅ Any Git UI that uses standard git operations

**Why pre-commit is sufficient:** If PII can't be committed, it can't be pushed. One hook at the earliest point is all you need.

## Bypassing (Not Recommended)

In rare cases where you need to bypass:
```bash
git commit --no-verify
```

**Warning:** Only use this if you're absolutely certain no PII is present.

## Updating the Hook

If you need to change the PII being checked:
1. Edit `hooks/pre-commit`
2. Run `./hooks/install.sh` again to reinstall

## Files

- `pre-commit`: Hook that runs before commits
- `install.sh`: Installation script
- `README.md`: This file
