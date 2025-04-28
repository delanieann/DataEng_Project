#!/bin/bash
set -e

# -- Load environment variables --

if [ -z "$WORKSPACE_DIR" ]; then
    if [ -f "/etc/profile.d/trimet_pipeline_workspace.sh" ]; then
        source /etc/profile.d/trimet_pipeline_workspace.sh
    else
        echo "[!] WORKSPACE_DIR not set and no profile.d file found. Exiting."
        exit 1
    fi
fi

# -- Activate virtual environment --

cd "$WORKSPACE_DIR"

if [ ! -d ".venv" ]; then
    echo "[!] Virtual environment (.venv) not found at $WORKSPACE_DIR/.venv. Exiting."
    exit 1
fi

echo "[Run Job] Activating virtual environment..."
source .venv/bin/activate

# -- Setup logging directory --

LOG_DIR="$WORKSPACE_DIR/job_logs"
mkdir -p "$LOG_DIR"

# -- Prepare logfile path --

if [ -z "$1" ]; then
    echo "[!] No Python job script specified."
    echo "Usage: bash run_job.sh path/to/job_script.py"
    exit 1
fi

PYTHON_JOB="$1"

LOGFILE="$LOG_DIR/$(basename "$PYTHON_JOB" .py)_$(date +'%Y%m%d_%H%M%S').log"

# -- Record environment info into logfile --

ENV_HASH_FILE="$WORKSPACE_DIR/ENV_HASH.txt"
COMMIT_HASH_FILE="$WORKSPACE_DIR/COMMIT_HASH.txt"
NOW_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

{
    echo "[Run Job] --- Environment Info ---"
    echo "[Run Job] Timestamp (UTC): $NOW_UTC"
    echo "[Run Job] Hostname: $(hostname)"
    echo "[Run Job] Username: $(whoami)"
    echo "[Run Job] Workspace Directory: $WORKSPACE_DIR"
    echo "[Run Job] Python Version: $(python --version 2>&1)"
    
    if [ -f "$ENV_HASH_FILE" ]; then
        echo "[Run Job] ENV_HASH: $(cat "$ENV_HASH_FILE")"
    else
        echo "[Run Job] ENV_HASH file not found."
    fi

    if [ -f "$COMMIT_HASH_FILE" ]; then
        echo "[Run Job] COMMIT_HASH: $(cat "$COMMIT_HASH_FILE")"
    else
        echo "[Run Job] COMMIT_HASH file not found."
    fi
    echo "[Run Job] -------------------------"
} >> "$LOGFILE"

# -- Run Python job --

echo "[Run Job] Running Python job: $PYTHON_JOB" >> "$LOGFILE"
python "$PYTHON_JOB" >> "$LOGFILE" 2>&1
PYTHON_EXIT_CODE=$?

# -- Final reporting --

if [ "$PYTHON_EXIT_CODE" -eq 0 ]; then
    echo "[Run Job] Job completed successfully. Log saved to: $LOGFILE"
else
    echo "[Run Job] Job failed! See log: $LOGFILE"
fi

exit "$PYTHON_EXIT_CODE"

# -- Done --
