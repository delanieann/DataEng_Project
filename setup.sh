!/bin/bash

# This script sets up the VM for the Trimet Bus Data Engineering project 
echo "[0. SETUP]: Starting setup script..."
echo "[1. SETUP]: Updating system packages..."
sudo apt-get update -y

echo "[2. SETUP]: Installing required packages..."
sudo apt install -y git pipx

# Install pyenv
echo "[3. SETUP]: Installing pyenv..."
curl -fsSL https://pyenv.run | bash

# Set up pyenv environment variables
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init - bash)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

echo "pyenv configuration added to ~/.bashrc"
echo "Restart your shell or run 'source ~/.bashrc' to apply changes"

echo "[4. SETUP]: pipx setup..."
pipx ensurepath

echo "[5. SETUP]: Installing pipenv via pipx..."
pipx install pipenv

echo "[6. SETUP]: Cloning project repository(ies)..."

# Assumes ssh key created, added to ssh-agent, and added to github (only required if using ssh to clone private repo)

mkdir ~/code
cd ~/code
# git clone https://github.com/delanieann/DataEng_Project ./dataeng_project

# THIS SHOULD BE UPDATED TO REFLECT SHARED PROJECT REPO AND POTENTIALLY A SPECIFIC BRANCH
git clone git@github.com:whitham-powell/pdx-edu-cs510-data-eng-project.git ./project_code

echo "[7. SETUP]: pipenv installing dependencies..."

cd ~/code/project_code
pipenv install


mkdir -p ~/data/raw

