#!/bin/bash

# bu.sh - Backup and push script for larryseyer.github.io
# Stages all changes, commits with provided message, and pushes to GitHub

if [ -z "$1" ]; then
    echo "Usage: ./bu.sh \"Your commit message\""
    echo "Example: ./bu.sh \"Updated homepage styling\""
    exit 1
fi

# Stage all changes
git add -A

# Commit with the provided message
git commit -m "$1"

# Push to origin/main
git push origin main

echo "Done! Changes pushed to GitHub."
