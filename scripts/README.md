# Scripts for VM Workspace Management

This directory contains scripts for setting up, updating, and validating a Python workspace environment on a VM used for data collection, transformation, and publication tasks.

The scripts are organized as follows:

## Directory Structure

```
scripts/
├── check_workspace.sh   # Check workspace consistency (repo, environment)
├── update_vm.sh         # Update workspace to match latest repo and environment
├── setup/               # Setup scripts (excluded during normal deployments)
│   ├── setup_vm.sh      # Setup a new VM workspace
│   ├── setup_local.sh   # Local development setup script
```

---

## Script Descriptions

### `setup/setup_vm.sh`

- **Purpose:** Sets up a new VM with:
  - A cloned Git repository
  - A Python virtual environment
  - Environment configuration (`/etc/profile.d/`)
- **Usage:**

  ```bash
  bash scripts/setup/setup_vm.sh <repo_url> <branch> <workspace_dir>
  ```

- **Inputs Required:**
  - `repo_url` — URL of the Git repository to clone
  - `branch` — Git branch to track
  - `workspace_dir` — Target directory for workspace files
- **Notes:**  
  Should be run **once per VM** at initial setup.  
  Not included during repo syncing into the active workspace.

---

### `setup/setup_local.sh`

- **Purpose:** (Optional) Script to set up a **local development environment**.
- **Usage:**  
  Designed to bootstrap local workstations or staging environments.
- **Notes:**  
  Also **excluded** during deployment to avoid cluttering production VMs.

---

### `update_vm.sh`

- **Purpose:** Updates the VM workspace by:
  - Pulling latest code from the configured repository and branch
  - Resyncing Python environment dependencies
  - Refreshing environment fingerprint (`ENV_HASH.txt`) and Git commit hash (`COMMIT_HASH.txt`)
- **Usage:**

  ```bash
  bash scripts/update_vm.sh [optional_repo_url] [optional_branch] [--promote]
  ```

- **Behavior:**
  - If **no arguments**, uses the environment-configured repo and branch.
  - If **repo/branch arguments given**, temporarily overrides.
  - If `--promote` flag is provided, updates environment configuration permanently.

---

### `check_workspace.sh`

- **Purpose:** Verifies that the workspace is consistent with the expected:
  - Git repository branch
  - Python environment dependencies
- **Usage:**

  ```bash
  bash scripts/check_workspace.sh [optional_repo_url] [optional_branch] [optional_workspace_dir]
  ```

- **Exit Codes:**
  - `0` — Workspace is fully up to date
  - `1` — Workspace out of sync (requires update)
  - `2` — Critical missing files or invalid setup

- **Behavior:**
  - Without arguments, checks the configured environment.
  - With arguments, temporarily checks a different workspace/repo/branch.
  - Prints detailed messages about commit hash mismatch and/or environment fingerprint mismatch if applicable.

---

## Notes

- **Environment Variables:**
  - Loaded from `/etc/profile.d/trimet_pipeline_workspace.sh`
  - Managed automatically by `setup_vm.sh` and `update_vm.sh`
- **Workspace Artifacts:**
  - `COMMIT_HASH.txt` stores last deployed Git commit.
  - `ENV_HASH.txt` stores hash of `pyproject.toml` and `uv.lock` (Python environment fingerprint).
- **Deployment Behavior:**
  - `setup/` scripts are **excluded** when syncing workspace into deployment targets.
  - Only `update_vm.sh` and `check_workspace.sh` are needed after initial setup.
