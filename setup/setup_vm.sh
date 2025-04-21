#!/bin/bash

set -e

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: $0 <repo_url> <branch> <workspace_dir>"
    echo "Example: $0 https://github.com/yourusername/yourrepo.git main /path/to/workspace"
    exit 1
fi

REPO_URL=$1
BRANCH=$2
WORKSPACE_DIR=$3
CLONES_DIR="$HOME/clones"
REPO_NAME=$(basename "${REPO_URL%.git}")
REPO_DIR="$CLONES_DIR/$REPO_NAME"


echo "[VM Setup]"

echo "[VM Setup] Updating package list and installing git"

sudo apt-get update
sudo apt-get install -y git

echo "[VM Setup] Installing uv"
if ! command -v uv >/dev/null 2>&1; then
    echo "[*] Installing uv using install script"
    curl -LsSf https://astral.sh/uv/install.sh | sh

    if [ -f "$HOME/.local/bin/env" ]; then
        source "$HOME/.local/bin/env"
    else
        export PATH="$HOME/.local/bin:$PATH"
    fi
else
    echo "[*] uv is already installed"
fi

echo "[VM Setup] Cloning the repository"

# Detect URL type (SSH or HTTPS)
if [[ "$REPO_URL" =~ ^git@ ]]; then
    echo "[*] Detected SSH repository"
    HOST=$(echo "$REPO_URL" | cut -d@ -f2 | cut -d: -f1)
    PATH_PART=$(echo "$REPO_URL" | cut -d: -f2)
elif [[ "$REPO_URL" =~ ^https:// ]]; then
    echo "[*] Detected HTTPS repository"
    HOST=$(echo "$REPO_URL" | cut -d/ -f3)
    PATH_PART=$(echo "$REPO_URL" | cut -d/ -f4-)
else
    echo "[!] Unknown URL format: $REPO_URL"
    exit 1
fi

mkdir -p $CLONES_DIR

if [ -d "$REPO_DIR/.git" ]; then
    echo "Repository already cloned at $REPO_DIR."
    cd "$REPO_DIR"
    git fetch origin
    if git show-ref --verify --quiet refs/heads/"$BRANCH"; then
        git checkout "$BRANCH"
        git pull origin
    else
        echo "Warning: Branch $BRANCH does not exist. Switching to main branch. This may not be what you want."
        BRANCH="main"
        git checkout "$BRANCH"
    fi
    echo "Pulling latest changes from $BRANCH branch."
    git pull origin "$BRANCH"
else
    echo "Cloning repository into $REPO_DIR."
    git clone "$REPO_URL" "$REPO_DIR" || {
        echo "Failed to clone repository. Exiting."
        exit 1
    }
fi

echo "[VM Setup] Creating workspace directory"
mkdir -p $WORKSPACE_DIR

cp -r $REPO_DIR $WORKSPACE_DIR

echo "[VM Setup] Setting up virtual environment"
cd $WORKSPACE_DIR

if [ -d ".venv" ]; then
    echo "Virtual environment already exists. Activating..."
else
    echo "Creating virtual environment..."
    uv venv
fi
source .venv/bin/activate

