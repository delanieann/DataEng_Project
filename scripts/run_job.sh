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

# -- Run Python job --

if [ -z "$1" ]; then
    echo "[!] No Python job script specified."
    echo "Usage: bash run_job.sh path/to/job_script.py"
    exit 1
fi

PYTHON_JOB="$1"

echo "[Run Job] Running Python job: $PYTHON_JOB"

# Set up logging directory
LOG_DIR="$WORKSPACE_DIR/job_logs"
mkdir -p "$LOG_DIR"

# Log filename based on script name and timestamp
LOGFILE="$LOG_DIR/$(basename "$PYTHON_JOB" .py)_$(date +'%Y%m%d_%H%M%S').log"

# Run Python job, capture stdout and stderr into log
python "$PYTHON_JOB" > "$LOGFILE" 2>&1
PYTHON_EXIT_CODE=$?

if [ "$PYTHON_EXIT_CODE" -eq 0 ]; then
    echo "[Run Job] Job completed successfully. Log saved to: $LOGFILE"
else
    echo "[Run Job] Job failed! See log: $LOGFILE"
fi

exit "$PYTHON_EXIT_CODE"

# -- Done --
