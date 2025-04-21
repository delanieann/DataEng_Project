#!/bin/bash

set -e

echo "[Local Setup 0] Installing dependencies... with uv"

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

echo "[Local Setup 1] Installing pre-commit using uv tools"

uv tool install pre-commit --with pre-commit-uv --force-reinstall

if [ -f .pre-commit-config.yaml ]; then
    echo "[Local Setup 2] Installing pre-commit hooks"
    pre-commit install
else
    echo "[Local Setup 2] No .pre-commit-config.yaml found, skipping pre-commit installation"
fi

echo "[Local Setup 3] Installing dependencies using uv and activating virtual environment"

uv sync

uv venv

echo "[Local Setup] Complete."
echo "Next Steps: "
echo " - Activate with 'source .venv/bin/activate'"
echo " - OR uv run <script.py> to run a script in the virtual environment"
echo ""
echo "To add a dependency, use 'uv add <package>'"
