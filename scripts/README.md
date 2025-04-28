# Scripts for VM Workspace Management

This directory contains scripts for setting up, updating, and validating a Python workspace environment on a VM used for data collection, transformation, and publication tasks.

## Directory Structure

```
scripts/
├── check_workspace.sh   # Check workspace consistency (repo, environment)
├── update_vm.sh         # Update workspace to match latest repo and environment
├── run_job.sh           # Run specific Python job inside workspace
├── setup/               # Setup scripts (excluded during normal deployments)
│   ├── setup_vm.sh      # Setup a new VM workspace
│   ├── setup_local.sh   # Local development setup script
```

---

## Script Descriptions

### `setup/setup_vm.sh`
- **Purpose:** Sets up a new VM by:
  - Cloning a Git repository
  - Creating a Python virtual environment
  - Configuring environment variables (`/etc/profile.d/`)
- **Usage:**
  ```bash
  bash scripts/setup/setup_vm.sh <repo_url> <branch> <workspace_dir>
  ```
- **Notes:**  
  Should be run once per VM during initial setup.

---

### `setup/setup_local.sh`
- **Purpose:** Sets up a local development environment for workstation testing.
- **Notes:**  
  Excluded from production deployments.

---

### `update_vm.sh`
- **Purpose:** Updates the VM workspace by:
  - Pulling the latest code from the configured repository and branch
  - Syncing Python environment dependencies
  - Updating environment and commit fingerprints
- **Usage:**
  ```bash
  bash scripts/update_vm.sh [optional_repo_url] [optional_branch] [--promote]
  ```
- **Notes:**
  - Without arguments, uses current configuration.
  - With `--promote`, updates environment permanently.

---

### `check_workspace.sh`
- **Purpose:** Verifies workspace consistency:
  - Git repository branch matches expected
  - Python environment matches expected
- **Usage:**
  ```bash
  bash scripts/check_workspace.sh [optional_repo_url] [optional_branch] [optional_workspace_dir]
  ```
- **Exit Codes:**
  - `0` — Workspace is up to date
  - `1` — Workspace is out of sync
  - `2` — Critical setup files missing

---

### `run_job.sh`
- **Purpose:** Runs a specific Python job script inside the workspace.
- **Usage:**
  ```bash
  bash scripts/run_job.sh path/to/job_script.py
  ```
- **Behavior:**
  - Activates the virtual environment
  - Runs the specified Python script
  - Captures all stdout and stderr into a timestamped log under `job_logs/`
- **Notes:**
  - Exits with `0` on success, or the Python script's exit code on failure.
  - Intended to be triggered manually or via cronjobs.
  - When scheduling with cron, redirect run_job.sh output separately to capture Bash-level errors.

---

## Notes

- **Environment Variables:**
  - Loaded from `/etc/profile.d/trimet_pipeline_workspace.sh`
- **Workspace Artifacts:**
  - `COMMIT_HASH.txt` — Last deployed Git commit
  - `ENV_HASH.txt` — Hash of `pyproject.toml` + `uv.lock`
- **Deployment Behavior:**
  - `setup/` scripts are excluded during deployments
  - Only `update_vm.sh`, `check_workspace.sh`, and `run_job.sh` are needed for operations
- **Logging Behavior:**
  - Python script logs are saved under `job_logs/` with timestamps.
  - Cronjob scheduling should redirect run_job.sh output separately if desired, e.g.:
    ```cron
    0 3 * * * /path/to/scripts/run_job.sh scripts/publisher_job.py >> /path/to/workspace/job_logs/cron_run_job.log 2>&1
    ```

---

