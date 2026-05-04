#!/bin/bash

# --- CONFIGURATION ---
ACTIVATE_PYTHON="source .venv/bin/activate" 
BACKEND_PORT=9998

# --- CLEANUP FUNCTION ---
cleanup() {
    echo -e "\n🛑 Shutdown signal received..."
    echo "🧹 Killing processes on ports $BACKEND_PORT ..."
    
    # Kill by Port to be 100% sure
    fuser -k $BACKEND_PORT/tcp > /dev/null 2>&1
    
    echo "✅ System offline."
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT

# Clear old logs
echo "" > backend.log

# --- STARTUP ---
echo "📡 Starting Backend..."
$ACTIVATE_PYTHON

python3 server/main.py > backend.log 2>&1 &

echo "📖 Streaming logs (Ctrl+C to stop everything):"
echo "---------------------------------------"

tail -f backend.log 