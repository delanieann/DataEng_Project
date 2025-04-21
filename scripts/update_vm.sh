#!/bin/bash
set -e

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: $0 <repo_url> <branch> <workspace_dir>"
    exit 1
fi

REPO_URL=$1
BRANCH=$2
WORKSPACE_DIR=$3
CLONES_DIR="$HOME/clones"
REPO_NAME=$(basename "${REPO_URL%.git}")
REPO_DIR="$CLONES_DIR/$REPO_NAME"

echo "[Update] Updating repo in $REPO_DIR"

if [ ! -d "$REPO_DIR/.git" ]; then
    echo "[!] Repo not cloned. Run setup_vm.sh first."
    exit 1
fi

cd "$REPO_DIR"
git fetch origin
if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null; then
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    echo "[!] Branch $BRANCH not found on origin. Exiting."
    exit 1
fi

echo "[Update] Syncing repo to workspace: $WORKSPACE_DIR"

EXCLUDES=(
  --exclude='.git'
  --exclude='.venv/'
  --exclude='.vscode/'
  --exclude='*.md'
  --exclude='tests/'
  --exclude='.pre-commit-config.yaml'
)

sudo rsync -a --delete "${EXCLUDES[@]}" "$REPO_DIR/" "$WORKSPACE_DIR/"
sudo chown -R "$USER:$USER" "$WORKSPACE_DIR"

echo "[Update] Updating virtual environment"
cd "$WORKSPACE_DIR"
if [ ! -d ".venv" ]; then
    echo "[!] No virtualenv found. Run setup_vm.sh first."
    exit 1
fi

source .venv/bin/activate
uv sync --no-dev

cd "$REPO_DIR"
cat pyproject.toml uv.lock 2>/dev/null | sha256sum | cut -d' ' -f1 > "$WORKSPACE_DIR/ENV_HASH.txt"


echo "[Update] Saving commit hash"
cd "$REPO_DIR"
git rev-parse HEAD > "$WORKSPACE_DIR/COMMIT_HASH.txt"

echo "Update complete."
