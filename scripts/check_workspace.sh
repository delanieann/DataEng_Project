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

COMMIT_FILE="$WORKSPACE_DIR/COMMIT_HASH.txt"
HASH_FILE="$WORKSPACE_DIR/ENV_HASH.txt"

echo "[Check] Checking workspace: $WORKSPACE_DIR"
echo "        Against clone: $REPO_DIR ($BRANCH)"

# --- Check commit hash ---
if [ ! -f "$COMMIT_FILE" ]; then
    echo "[!] No COMMIT_HASH.txt found. Run setup or update first."
    exit 2
fi

cd "$REPO_DIR"
git fetch origin "$BRANCH" >/dev/null
CURRENT_REPO_COMMIT=$(git rev-parse "$BRANCH")
DEPLOYED_COMMIT=$(cat "$COMMIT_FILE")

if [ "$CURRENT_REPO_COMMIT" != "$DEPLOYED_COMMIT" ]; then
    echo "[!] Workspace is out of date:"
    echo "     Workspace commit: $DEPLOYED_COMMIT"
    echo "     Latest in repo:   $CURRENT_REPO_COMMIT"
    COMMIT_OUT_OF_DATE=1
else
    echo "[*] Commit hash matches: $DEPLOYED_COMMIT"
    COMMIT_OUT_OF_DATE=0
fi

# --- Check environment hash ---
if [ -f pyproject.toml ] || [ -f uv.lock ]; then
    CURRENT_ENV_HASH=$(cat pyproject.toml uv.lock 2>/dev/null | sha256sum | cut -d' ' -f1)
else
    CURRENT_ENV_HASH=""
fi

if [ ! -f "$HASH_FILE" ]; then
    echo "[!] No ENV_HASH.txt found in workspace."
    ENV_OUT_OF_DATE=1
elif [ "$CURRENT_ENV_HASH" != "$(cat "$HASH_FILE")" ]; then
    echo "[!] Environment hash mismatch:"
    echo "     Workspace ENV_HASH: $(cat "$HASH_FILE")"
    echo "     Current   ENV_HASH: $CURRENT_ENV_HASH"
    ENV_OUT_OF_DATE=1
else
    echo "[*] Environment hash matches."
    ENV_OUT_OF_DATE=0
fi

if [ "$COMMIT_OUT_OF_DATE" -eq 0 ] && [ "$ENV_OUT_OF_DATE" -eq 0 ]; then
    echo "[*] Workspace is up to date."
    exit 0
else
    echo "[!] Workspace is out of sync."
    exit 1
fi
