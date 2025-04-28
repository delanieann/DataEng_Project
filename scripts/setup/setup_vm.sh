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

echo "[VM Setup] Updating package list and installing git and curl"

sudo apt-get update
sudo apt-get install -y git curl rsync

echo "[VM Setup] Installing uv if needed"
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

echo "[VM Setup] Cloning or updating the repo into $CLONES_DIR"
# Detect URL type (SSH or HTTPS)
if [[ "$REPO_URL" =~ ^git@ ]]; then
    echo "[*] Detected SSH repository"
    
    if [ -z "$SSH_AUTH_SOCK" ]; then
        echo "[*] Starting ssh-agent"
        eval "$(ssh-agent -s)"
    fi

    echo "[*] Adding available SSH keys"
    ssh-add -l >/dev/null 2>&1 || ssh-add
    
elif [[ "$REPO_URL" =~ ^https:// ]]; then
    echo "[*] Detected HTTPS repository"
else
    echo "[!] Unknown URL format: $REPO_URL"
    exit 1
fi

mkdir -p "$CLONES_DIR"
if [ -d "$REPO_DIR/.git" ]; then
    echo "[*] Repository already exists at $REPO_DIR. Pulling latest changes."
    cd "$REPO_DIR"
    git fetch origin
    if git show-ref --verify --quiet refs/heads/"$BRANCH"; then
        git checkout "$BRANCH"
        git pull origin
    else
        echo "[!] Branch $BRANCH not found. Exiting."
        exit 1
    fi
    echo "[*] Pulling latest changes from $BRANCH branch."
    git pull origin "$BRANCH"
else
    echo "[*]Cloning repository into $REPO_DIR."
    git clone "$REPO_URL" "$REPO_DIR" || {
        echo "[ERROR] Failed to clone repository. Exiting."
        exit 1
    }
    cd "$REPO_DIR"
    git checkout "$BRANCH"
    echo "[*] Cloned repository into $REPO_DIR and checked out branch $BRANCH."
fi

echo "[VM Setup] Creating workspace directory"
sudo mkdir -p "$WORKSPACE_DIR"

echo "[VM Setup] Copying repository contents to workspace"
EXCLUDES=(
  --exclude='.git'
  --exclude='.vscode/'
  --exclude='*.md'
  --exclude='tests/'
  --exclude='.pre-commit-config.yaml'
  --exclude='.venv/'
  --exclude='scripts/setup/'
)
sudo rsync -a --delete "${EXCLUDES[@]}" "$REPO_DIR/" "$WORKSPACE_DIR/"

sudo chown -R "$USER:$USER" "$WORKSPACE_DIR"

echo "[VM Setup] Setting up virtual environment"
cd "$WORKSPACE_DIR"

if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment..."
    uv venv
else
    echo "[*] Reusing existing .venv and syncing dependencies..."
fi
uv sync --no-dev

echo "[*] Activating virtual environment..."
source .venv/bin/activate

# Save environment fingerprint
echo "[VM Setup] Saving environment fingerprint"
cat pyproject.toml uv.lock 2>/dev/null | sha256sum | cut -d' ' -f1 > ENV_HASH.txt

echo "[VM Setup] Saving current commit hash"
cd "$REPO_DIR"
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "$CURRENT_COMMIT" > "$WORKSPACE_DIR/COMMIT_HASH.txt"
echo "[VM Setup] Current commit hash saved to $WORKSPACE_DIR/COMMIT_HASH.txt"

echo "[VM Setup] Copying helper scripts to workspace"
cp "$REPO_DIR/scripts/update_vm.sh" "$WORKSPACE_DIR/"
cp "$REPO_DIR/scripts/check_workspace.sh" "$WORKSPACE_DIR/"
chmod +x "$WORKSPACE_DIR/update_vm.sh" "$WORKSPACE_DIR/check_workspace.sh"

CONFIG_FILE="$WORKSPACE_DIR/.vm_workspace_config"
echo "[VM Setup] Writing configuration to $CONFIG_FILE"
cat <<EOF > "$CONFIG_FILE"
REPO_URL=$REPO_URL
BRANCH=$BRANCH
WORKSPACE_DIR=$WORKSPACE_DIR
EOF

# Make workspace variables global for all users
echo "[VM Setup] Creating /etc/profile.d/trimet_pipeline_workspace.sh for global environment variables"
sudo tee /etc/profile.d/trimet_pipeline_workspace.sh > /dev/null <<EOF
# Trimet Pipeline workspace environment
$(cat "$CONFIG_FILE" | sed 's/^/export /')
EOF
sudo chmod 644 /etc/profile.d/trimet_pipeline_workspace.sh

echo "[VM Setup] Global environment file created at /etc/profile.d/trimet_pipeline_workspace.sh"

echo "Setup complete."
echo "Workspace: $WORKSPACE_DIR"
echo "Virtual environment: $WORKSPACE_DIR/.venv"
echo "Current commit hash: $CURRENT_COMMIT"
echo "Branch: $BRANCH"
echo "Repository URL: $REPO_URL"