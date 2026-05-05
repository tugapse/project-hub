#!/bin/bash

# --- CONFIGURATION ---
ACTIVATE_PYTHON="source .venv/bin/activate" 
DB_FILE="projects.json"
BACKEND_PORT=8000
FRONTEND_PORT=4200

# --- CLEANUP FUNCTION ---
cleanup() {
    echo -e "\n🛑 Shutdown signal received..."
    echo "🧹 Killing processes on ports $BACKEND_PORT and $FRONTEND_PORT..."
    
    # Kill by Port to be 100% sure
    fuser -k $BACKEND_PORT/tcp > /dev/null 2>&1
    fuser -k $FRONTEND_PORT/tcp > /dev/null 2>&1
    
    echo "✅ System offline."
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT

# --- PRE-FLIGHT ---
if [ ! -f "$DB_FILE" ]; then echo "[]" > "$DB_FILE"; fi

# Clear old logs
echo "" > backend.log
echo "" > frontend.log

# --- STARTUP ---
echo "📡 Starting Backend..."
$ACTIVATE_PYTHON
python3 server/main.py > backend.log 2>&1 &

echo "💻 Starting Frontend..."
cd project-hub
ng serve --host 0.0.0.0 --port $FRONTEND_PORT > ../frontend.log 2>&1 &
cd ..

echo "---------------------------------------"
echo "🚀 Trello Suite is LIVE"
echo "📡 Press Ctrl+C to stop both servers."
echo "---------------------------------------"
echo "📖 Streaming logs (Ctrl+C to stop everything):"
echo "---------------------------------------"

# This command "waits" by following the logs. 
# When you Ctrl+C, the trap triggers.
tail -f backend.log -f frontend.log