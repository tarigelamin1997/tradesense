
#!/bin/bash

set -e

# Version management script for TradeSense

ACTION=${1:-current}

case $ACTION in
    "current")
        echo "Current version:"
        git describe --tags --always --dirty
        ;;
    "bump")
        TYPE=${2:-patch}
        echo "Bumping $TYPE version..."
        
        # Get current version
        CURRENT=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
        
        # Parse version numbers
        VERSION=${CURRENT#v}
        IFS='.' read -ra PARTS <<< "$VERSION"
        MAJOR=${PARTS[0]:-0}
        MINOR=${PARTS[1]:-0}
        PATCH=${PARTS[2]:-0}
        
        # Increment based on type
        case $TYPE in
            "major")
                MAJOR=$((MAJOR + 1))
                MINOR=0
                PATCH=0
                ;;
            "minor")
                MINOR=$((MINOR + 1))
                PATCH=0
                ;;
            "patch")
                PATCH=$((PATCH + 1))
                ;;
            *)
                echo "Invalid bump type. Use: major, minor, or patch"
                exit 1
                ;;
        esac
        
        NEW_VERSION="v$MAJOR.$MINOR.$PATCH"
        
        # Create and push tag
        git tag -a $NEW_VERSION -m "Release $NEW_VERSION"
        git push origin $NEW_VERSION
        
        echo "Created new version: $NEW_VERSION"
        ;;
    "changelog")
        echo "Generating changelog..."
        LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
        
        if [ -z "$LAST_TAG" ]; then
            git log --oneline --pretty=format:"- %s" > CHANGELOG.md
        else
            git log $LAST_TAG..HEAD --oneline --pretty=format:"- %s" > CHANGELOG.md
        fi
        
        echo "Changelog updated in CHANGELOG.md"
        ;;
    *)
        echo "Usage: $0 [current|bump|changelog] [major|minor|patch]"
        exit 1
        ;;
esac
