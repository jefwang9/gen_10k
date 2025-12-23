#!/bin/bash
# Script to push code to GitHub
# Usage: ./push_to_github.sh <github-repo-url>

if [ -z "$1" ]; then
    echo "Usage: ./push_to_github.sh <github-repo-url>"
    echo "Example: ./push_to_github.sh https://github.com/jevin6236/ML_assignment.git"
    exit 1
fi

REPO_URL=$1

echo "Adding remote repository..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

echo "Pushing to GitHub..."
git branch -M main
git push -u origin main

echo "✓ Code pushed to GitHub successfully!"

