!/bin/bash

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

# This script sets up a VM for the Trimet Bus Data Engineering project using uv
echo "[1] Updating and installing packages from apt-packages.txt"
sudo apt-get update
xargs -a ./apt-packages.txt sudo apt-get install -y 

echo "[2] Installing uv using install script"
if ! command -v uv >/dev/null 2>&1; then
    echo "[2] Installing uv using install script"
    curl -LsSf https://astral.sh/uv/install.sh | sh

    if [ -f "$HOME/.local/bin/env" ]; then
        source "$HOME/.local/bin/env"
    else
        export PATH="$HOME/.local/bin:$PATH"
    fi
else
    echo "[2] uv is already installed"
fi


echo "[3] Cloning the repository"

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

