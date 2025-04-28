#!/bin/bash
set -e

# -- Load environment variables --
# Load from profile.d if not set
if [ -z "$WORKSPACE_DIR" ] || [ -z "$REPO_URL" ] || [ -z "$BRANCH" ]; then
    if [ -f "/etc/profile.d/trimet_pipeline_workspace.sh" ]; then
        source /etc/profile.d/trimet_pipeline_workspace.sh
    else
        echo "[!] Environment variables not set and no profile.d file found. Exiting."
        exit 1
    fi
fi

# Optional override for repo URL and branch to promote to config after update
OVERRIDE_REPO_URL="$REPO_URL"
OVERRIDE_BRANCH="$BRANCH"
PROMOTE_OVERRIDE=false

if [ ! -z "$1" ]; then
    echo "[Override] Forcing REPO_URL to $1"
    OVERRIDE_REPO_URL="$1"
fi

if [ ! -z "$2" ]; then
    echo "[Override] Forcing BRANCH to $2"
    OVERRIDE_BRANCH="$2"
fi

if [ "$3" == "--promote" ]; then
    echo "[Override] Will promote override to config after update"
    PROMOTE_OVERRIDE=true
fi

CLONES_DIR="$HOME/clones"
REPO_NAME=$(basename "${OVERRIDE_REPO_URL%.git}")
REPO_DIR="$CLONES_DIR/$REPO_NAME"

echo "[Update VM] Pulling latest code from $OVERRIDE_REPO_URL ($OVERRIDE_BRANCH branch)"

if [ ! -d "$REPO_DIR/.git" ]; then
    echo "[!] Repo not cloned. Run setup_vm.sh first."
    exit 1
fi

cd "$REPO_DIR"
git fetch origin
if git ls-remote --exit-code --heads origin "$OVERRIDE_BRANCH" >/dev/null; then
    git checkout "$OVERRIDE_BRANCH"
    git pull origin "$OVERRIDE_BRANCH"
else
    echo "[!] Branch $OVERRIDE_BRANCH not found on origin. Exiting."
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
  --exclude='.venv/'
  --exclude='scripts/setup/'
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

echo "[Update VM] Saving updated environment fingerprint"
cat pyproject.toml uv.lock 2>/dev/null | sha256sum | cut -d' ' -f1 > ENV_HASH.txt

echo "[Update VM] Saving updated commit hash"
cd "$REPO_DIR"
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "$CURRENT_COMMIT" > "$WORKSPACE_DIR/COMMIT_HASH.txt"
cd "$WORKSPACE_DIR"


# -- Promote Override if Requested --
if [ "$PROMOTE_OVERRIDE" = true ]; then
    echo "[Update VM] Promoting override to new permanent configuration"

    CONFIG_FILE="$WORKSPACE_DIR/.vm_workspace_config"
    echo "REPO_URL=$OVERRIDE_REPO_URL" > "$CONFIG_FILE"
    echo "BRANCH=$OVERRIDE_BRANCH" >> "$CONFIG_FILE"
    echo "WORKSPACE_DIR=$WORKSPACE_DIR" >> "$CONFIG_FILE"

    echo "[Update VM] Writing global environment file to /etc/profile.d/trimet_pipeline_workspace.sh"

    sudo tee /etc/profile.d/trimet_pipeline_workspace.sh > /dev/null <<EOF
# Trimet Pipeline workspace environment
export WORKSPACE_DIR="$WORKSPACE_DIR"
export REPO_URL="$OVERRIDE_REPO_URL"
export BRANCH="$OVERRIDE_BRANCH"
EOF

    sudo chmod 644 /etc/profile.d/trimet_pipeline_workspace.sh

    echo "[Update VM] Promotion complete."
fi

echo "[Update VM] Update complete."
