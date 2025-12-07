#!/bin/bash

# run.sh - Run labelme application
# Activates venv and runs labelme with optional arguments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
PID_FILE="${SCRIPT_DIR}/.labelme.pid"
LOG_FILE="${SCRIPT_DIR}/.labelme.log"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at: $VENV_DIR"
    echo "Please run ./install.sh first to install dependencies."
    exit 1
fi

# Check if labelme is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Labelme is already running (PID: $OLD_PID)"
        echo "Use ./stop.sh to stop it first, or ./restart.sh to restart it."
        exit 1
    else
        # PID file exists but process is not running, remove stale PID file
        rm -f "$PID_FILE"
    fi
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Change to script directory
cd "$SCRIPT_DIR"

# Check for DISPLAY (required for GUI applications)
if [ -z "$DISPLAY" ]; then
    echo "Warning: DISPLAY environment variable is not set."
    echo "Labelme is a GUI application and requires a display server."
    echo "If running remotely, ensure X11 forwarding is enabled or DISPLAY is set."
    echo ""
fi

echo "=========================================="
echo "Starting Labelme..."
echo "=========================================="
echo "PID file: $PID_FILE"
echo "Log file: $LOG_FILE"
if [ -n "$DISPLAY" ]; then
    echo "DISPLAY: $DISPLAY"
fi
echo ""

# Run labelme in background and capture PID
# Pass all arguments to labelme
nohup labelme "$@" > "$LOG_FILE" 2>&1 &
LABELME_PID=$!

# Save PID to file
echo "$LABELME_PID" > "$PID_FILE"

echo "✓ Labelme started (PID: $LABELME_PID)"
echo ""
echo "To view logs: tail -f $LOG_FILE"
echo "To stop: ./stop.sh"
echo "To monitor: ./monitor.sh"
echo ""

# Wait a moment to check if process started successfully
sleep 1
if ! ps -p "$LABELME_PID" > /dev/null 2>&1; then
    echo "Error: Labelme process failed to start. Check logs: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi

