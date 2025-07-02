#!/bin/bash

# Ask for commit message
read -p "Enter commit message: " commit_msg

# Ask for version tag
read -p "Enter version tag (e.g. v1.2.0): " version_tag

# Ask for version description
read -p "Enter version description: " version_desc

# Get current branch name
branch=$(git branch --show-current)

# Run the full git flow
git add .
git commit -m "$commit_msg"
git tag -a $version_tag -m "$version_desc"
git push origin $branch
git push origin $version_tag
