#!/bin/env bash

set -e

# Check for system dependencies
echo "Checking system dependencies..."
MISSING_DEPS=0

for cmd in python3 pip node; do
  if ! command -v "$cmd" &> /dev/null; then
    # Fallback to check for pip3 if pip is missing
    if [ "$cmd" = "pip" ] && command -v pip3 &> /dev/null; then
      continue
    fi
    echo "Error: $cmd is not installed."
    MISSING_DEPS=1
  fi
done

# Check specifically for python3-venv
if command -v python3 &> /dev/null && ! python3 -m venv -h &> /dev/null; then
  echo "Error: python3-venv is not installed."
  MISSING_DEPS=1
fi

if [ $MISSING_DEPS -ne 0 ]; then
  echo "Please install the missing dependencies and run the script again."
  exit 1
fi

# check for .venv create python env if not exist
if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

# activate env
echo "Activating environment..."
source .venv/bin/activate

# install server deps
if [ -f "server/requirements.txt" ]; then
  echo "Installing server dependencies..."
  pip install -r server/requirements.txt
fi

# go to ./project-hub folder and install deps 
echo "Navigating to ./project-hub in a subshell..."
(
  cd ./project-hub || exit
  echo "Installing Node dependencies..."
  npm install
  echo "Building Angular project for the server..."
  npm run build-to-server
)

echo ""
echo "======================================================"
echo "Build completed successfully!"
echo "To start the application, run:"
echo "  source .venv/bin/activate && python server/main.py"
echo "======================================================"
