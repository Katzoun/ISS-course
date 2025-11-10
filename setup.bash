#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="${VENV_DIR:-.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-requirements.txt}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python not found (looked for: $PYTHON_BIN)." >&2
  exit 1
fi

echo "Creating virtual environment in: $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"

# Activate the environment
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip wheel

if [ -f "$REQUIREMENTS_FILE" ]; then
  echo "Installing dependencies from $REQUIREMENTS_FILE"
  pip install -r "$REQUIREMENTS_FILE"
else
  echo "$REQUIREMENTS_FILE not found — skipping install."
fi

echo "Done. Activate next time with: source $VENV_DIR/bin/activate"