#!/bin/bash
# JumboShell launcher — handles venv setup automatically.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "First-time setup: creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt --quiet
    echo "Setup complete. Launching JumboShell..."
else
    source venv/bin/activate
fi

python -m jumbo_shell

deactivate
