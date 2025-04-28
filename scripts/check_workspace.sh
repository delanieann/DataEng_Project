#!/bin/bash
set -e

# Load from profile.d if environment not already set
if [ -z "$WORKSPACE_DIR" ] || [ -z "$REPO_URL" ] || [ -z "$BRANCH" ]; then
    if [ -f "/etc/profile.d/trimet_pipeline_workspace.sh" ]; then
        source /etc/profile.d/trimet_pipeline_workspace.sh
    else
        echo "[!] Environment variables not set and no profile.d file found. Exiting."
        exit 1
    fi
fi

# Optional positional overrides
if [ ! -z "$1" ]; then
    REPO_URL="$1"
fi

if [ ! -z "$2" ]; then
    BRANCH="$2"
fi

if [ ! -z "$3" ]; then
    WORKSPACE_DIR="$3"
fi

CLONES_DIR="$HOME/clones"
REPO_NAME=$(basename "${REPO_URL%.git}")
REPO_DIR="$CLONES_DIR/$REPO_NAME"

COMMIT_FILE="$WORKSPACE_DIR/COMMIT_HASH.txt"
HASH_FILE="$WORKSPACE_DIR/ENV_HASH.txt"


echo "[Check Workspace] Checking workspace: $WORKSPACE_DIR"
echo "        Against clone: $REPO_DIR ($BRANCH)"

# --- Check workspace directory ---
if [ ! -d "$WORKSPACE_DIR" ]; then
    echo "[!] Workspace directory not found at $WORKSPACE_DIR. Exiting."
    exit 2
fi

# --- Check that .venv exists ---
if [ ! -d "$WORKSPACE_DIR/.venv" ]; then
    echo "[!] Virtual environment (.venv) not found at $WORKSPACE_DIR/.venv. Exiting."
    exit 2
fi

# --- Check commit hash ---
echo "[Check Workspace] Checking commit fingerprint (COMMIT_HASH.txt)"

if [ ! -f "$COMMIT_FILE" ]; then
    echo "[!] No COMMIT_HASH.txt found in workspace. Run setup_vm.sh or update_vm.sh first."
    exit 2
fi

cd "$REPO_DIR"
git fetch origin "$BRANCH" >/dev/null

CURRENT_REPO_COMMIT=$(git rev-parse "$BRANCH")
DEPLOYED_COMMIT=$(cat "$COMMIT_FILE")

if [ "$CURRENT_REPO_COMMIT" == "$DEPLOYED_COMMIT" ]; then
    echo "[*] Commit hash matches: $DEPLOYED_COMMIT"
    COMMIT_OUT_OF_DATE=0
else
    echo "[!] Commit hash mismatch!"
    echo "     Workspace commit: $DEPLOYED_COMMIT"
    echo "     Latest in repo:   $CURRENT_REPO_COMMIT"
    COMMIT_OUT_OF_DATE=1
fi


# --- Check environment hash ---
echo "[Check Workspace] Checking environment fingerprint (ENV_HASH.txt)"

cd "$WORKSPACE_DIR"

if [ ! -f "$HASH_FILE" ]; then
    echo "[!] No ENV_HASH.txt found in workspace. Run setup_vm.sh or update_vm.sh first."
    exit 2
fi

# Compute current environment fingerprint
if [ -f pyproject.toml ] || [ -f uv.lock ]; then
    CURRENT_ENV_HASH=$(cat pyproject.toml uv.lock 2>/dev/null | sha256sum | cut -d' ' -f1)
else
    echo "[!] pyproject.toml and uv.lock not found in workspace. Cannot compute environment fingerprint."
    exit 2
fi

SAVED_ENV_HASH=$(cat "$HASH_FILE")

if [ "$CURRENT_ENV_HASH" == "$SAVED_ENV_HASH" ]; then
    echo "[Check Workspace] Environment hash matches."
    ENV_OUT_OF_DATE=0
else
    echo "[!] Environment hash mismatch!"
    echo "     Workspace ENV_HASH: $SAVED_ENV_HASH"
    echo "     Current   ENV_HASH: $CURRENT_ENV_HASH"
    echo "Recommendation: Run update_vm.sh to re-sync environment."
    ENV_OUT_OF_DATE=1
fi

# --- Check if workspace is up to date ---
echo "[Check Workspace] Checking if workspace is up to date..."

if [ "$COMMIT_OUT_OF_DATE" -eq 0 ] && [ "$ENV_OUT_OF_DATE" -eq 0 ]; then
    echo "[*] Workspace is fully up to date."
    exit 0
else
    echo "[!] Workspace is out of sync."

    if [ "$COMMIT_OUT_OF_DATE" -ne 0 ]; then
        echo "[!] Problem detected: Commit hash mismatch."
    fi

    if [ "$ENV_OUT_OF_DATE" -ne 0 ]; then
        echo "[!] Problem detected: Environment fingerprint mismatch."
    fi

    exit 1
fi
