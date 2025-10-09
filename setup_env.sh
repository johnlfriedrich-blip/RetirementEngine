#!/bin/bash

set -e  # Exit on error
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
log="setup_env.log"

echo "[$timestamp] Starting environment setup..." | tee -a $log

# Define paths
VENV_PATH="$HOME/RetirementEngine_venv"
SYMLINK_PATH=".venv"
REQUIREMENTS="requirements.txt"
LOCKFILE="requirements-locked.txt"

# Remove old symlink if exists
if [ -L "$SYMLINK_PATH" ]; then
    rm "$SYMLINK_PATH"
    echo "[$timestamp] Removed old symlink." | tee -a $log
fi

# Create virtual environment
python3 -m venv "$VENV_PATH"
echo "[$timestamp] Created virtual environment at $VENV_PATH." | tee -a $log

# Create symlink
ln -s "$VENV_PATH" "$SYMLINK_PATH"
echo "[$timestamp] Symlinked .venv → $VENV_PATH." | tee -a $log

# Activate and install
source "$SYMLINK_PATH/bin/activate"
echo "[$timestamp] Activated environment." | tee -a $log

pip install -r "$REQUIREMENTS"
echo "[$timestamp] Installed dependencies from $REQUIREMENTS." | tee -a $log

pip freeze > "$LOCKFILE"
echo "[$timestamp] Frozen dependencies to $LOCKFILE." | tee -a $log

echo "[$timestamp] Setup complete." | tee -a $log