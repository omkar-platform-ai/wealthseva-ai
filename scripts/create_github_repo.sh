#!/bin/bash
# Run this on YOUR machine (requires gh CLI: https://cli.github.com)
# Usage: bash scripts/create_github_repo.sh

REPO_NAME="wealthseva-ai"

echo "Creating GitHub repo: $REPO_NAME"
gh repo create "$REPO_NAME" --public --description "AI-powered multilingual wealth advisor for IDBI Bank — IDBI Innovate 2026"

echo "Initialising git and pushing..."
git init
git add .
git commit -m "feat: initial project scaffold — WealthSeva AI"
git branch -M main
git remote add origin "https://github.com/$(gh api user -q .login)/$REPO_NAME.git"
git push -u origin main

echo "Creating dev branch..."
git checkout -b dev
git push -u origin dev

echo ""
echo "✅ Done! Repo live at: https://github.com/$(gh api user -q .login)/$REPO_NAME"
