#!/bin/bash

# Get current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
  echo "You're already on 'main'. This script is meant to update a feature branch from main."
  exit 1
fi

echo "You are on branch: $CURRENT_BRANCH"

# Step 1: Switch to main
echo "Switching to main..."
git checkout main || { echo "Failed to switch to main"; exit 1; }

# Step 2: Pull latest main
echo "Pulling latest changes from origin/main..."
git pull origin main || { echo "Failed to pull from origin/main"; exit 1; }

# Step 3: Switch back to original branch
echo "Switching back to $CURRENT_BRANCH..."
git checkout "$CURRENT_BRANCH" || { echo "Failed to switch back to $CURRENT_BRANCH"; exit 1; }

# Step 4: Merge main into the feature branch
echo "Merging main into $CURRENT_BRANCH..."
git merge main --no-edit || { echo "Merge failed – resolve conflicts manually"; exit 1; }

# Step 5: Tag the new version
read -p "Enter tag version (e.g. v1.2.1): " TAG_NAME
read -p "Enter tag description: " TAG_MESSAGE

echo "Creating tag: $TAG_NAME"
git tag -a "$TAG_NAME" -m "$TAG_MESSAGE" || { echo "Failed to create tag"; exit 1; }

# Step 6: Push updated branch and tag
echo "Pushing $CURRENT_BRANCH and tag $TAG_NAME to GitHub..."
git push origin "$CURRENT_BRANCH" || { echo "Failed to push branch"; exit 1; }
git push origin "$TAG_NAME" || { echo "Failed to push tag"; exit 1; }

echo "Sync and tag complete. $CURRENT_BRANCH is up-to-date with main and tagged as $TAG_NAME."
