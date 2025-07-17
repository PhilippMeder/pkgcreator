#!/bin/bash

# Usage:
# ./github_download.sh <owner> <repo> [branch] [target_dir] [folder]

# Required parameters
OWNER="$1"
REPO="$2"

# Optional parameters with defaults
BRANCH="${3:-main}"
TARGET_DIR="${4:-${REPO}_sparse}"
FOLDER="$5"

# Check for required arguments
if [ -z "$OWNER" ] || [ -z "$REPO" ]; then
    echo "Error: You must provide <owner> and <repo>."
    echo "Usage: $0 <owner> <repo> [branch] [target_dir] [folder]"
    exit 1
fi

# Construct GitHub URL
REPO_URL="https://github.com/${OWNER}/${REPO}.git"

echo "Cloning repository: $REPO_URL"
echo "Branch: $BRANCH"
echo "Target directory: $TARGET_DIR"
if [ -n "$FOLDER" ]; then
    echo "Sparse folder: $FOLDER"
else
    echo "No folder specified. The entire repository will be checked out."
fi

# Clone the repository without checking out files
git clone --filter=blob:none --no-checkout "$REPO_URL" "$TARGET_DIR"
cd "$TARGET_DIR" || exit 1

# Enable sparse-checkout only if a folder is specified
if [ -n "$FOLDER" ]; then
    git sparse-checkout init --cone
    git sparse-checkout set "$FOLDER"
else
    git sparse-checkout init --cone
    git sparse-checkout set ""
fi

# Checkout the specified branch
git checkout "$BRANCH"

echo "Done."
