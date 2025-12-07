#!/bin/bash

# stop.sh - Stop labelme application
# Finds and stops running labelme processes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.labelme.pid"

echo "=========================================="
echo "Stopping Labelme..."
echo "=========================================="

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Found running process (PID: $PID)"
        echo "Stopping process..."
        
        # Try graceful termination first
        kill "$PID" 2>/dev/null || true
        
        # Wait up to 5 seconds for graceful shutdown
        for i in {1..5}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                echo "✓ Process stopped gracefully"
                rm -f "$PID_FILE"
                exit 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Process did not stop gracefully, forcing termination..."
            kill -9 "$PID" 2>/dev/null || true
            sleep 1
            
            if ! ps -p "$PID" > /dev/null 2>&1; then
                echo "✓ Process force stopped"
                rm -f "$PID_FILE"
                exit 0
            else
                echo "Error: Failed to stop process"
                exit 1
            fi
        fi
    else
        echo "PID file exists but process is not running (stale PID file)"
        rm -f "$PID_FILE"
    fi
else
    echo "No PID file found. Searching for labelme processes..."
fi

# Also search for any labelme processes by name
LABELME_PIDS=$(pgrep -f "labelme" || true)

if [ -z "$LABELME_PIDS" ]; then
    echo "No running labelme processes found."
    rm -f "$PID_FILE"
    exit 0
else
    echo "Found additional labelme processes: $LABELME_PIDS"
    for pid in $LABELME_PIDS; do
        echo "Stopping process $pid..."
        kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
    done
    sleep 1
    
    # Verify all processes are stopped
    REMAINING=$(pgrep -f "labelme" || true)
    if [ -z "$REMAINING" ]; then
        echo "✓ All labelme processes stopped"
        rm -f "$PID_FILE"
        exit 0
    else
        echo "Warning: Some processes may still be running: $REMAINING"
        rm -f "$PID_FILE"
        exit 1
    fi
fi

