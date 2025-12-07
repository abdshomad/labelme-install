#!/bin/bash

# monitor.sh - Monitor labelme application status
# Shows process status, resource usage, and logs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.labelme.pid"
LOG_FILE="${SCRIPT_DIR}/.labelme.log"

echo "=========================================="
echo "Labelme Monitor"
echo "=========================================="
echo ""

# Check PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "PID File: $PID_FILE"
    echo "Process ID: $PID"
    echo ""
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Status: ✓ RUNNING"
        echo ""
        
        # Show process details
        echo "Process Information:"
        echo "--------------------"
        ps -p "$PID" -o pid,ppid,user,%cpu,%mem,vsz,rss,tty,stat,start,time,cmd
        echo ""
        
        # Show resource usage
        echo "Resource Usage:"
        echo "---------------"
        if command -v top &> /dev/null; then
            top -b -n 1 -p "$PID" | tail -n 1
        fi
        echo ""
        
        # Show recent log entries
        if [ -f "$LOG_FILE" ]; then
            echo "Recent Log Entries (last 10 lines):"
            echo "-----------------------------------"
            tail -n 10 "$LOG_FILE" 2>/dev/null || echo "No log entries yet"
            echo ""
        fi
        
        # Show log file size
        if [ -f "$LOG_FILE" ]; then
            LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
            echo "Log file size: $LOG_SIZE"
        fi
        
    else
        echo "Status: ✗ NOT RUNNING (stale PID file)"
        echo ""
        echo "The PID file exists but the process is not running."
        echo "This may indicate the process crashed or was killed."
        echo ""
        echo "To clean up and start fresh:"
        echo "  rm -f $PID_FILE"
        echo "  ./run.sh"
    fi
else
    echo "Status: ✗ NOT RUNNING (no PID file)"
    echo ""
    echo "Labelme is not currently running."
    echo "To start it, run: ./run.sh"
fi

echo ""
echo "=========================================="

# Check for any other labelme processes
OTHER_PIDS=$(pgrep -f "labelme" || true)
if [ ! -z "$OTHER_PIDS" ] && [ -f "$PID_FILE" ]; then
    MAIN_PID=$(cat "$PID_FILE")
    for pid in $OTHER_PIDS; do
        if [ "$pid" != "$MAIN_PID" ]; then
            echo ""
            echo "Warning: Found additional labelme process (PID: $pid)"
            echo "This may be a child process or another instance."
        fi
    done
fi

echo ""
echo "Commands:"
echo "  ./run.sh      - Start labelme"
echo "  ./stop.sh     - Stop labelme"
echo "  ./restart.sh  - Restart labelme"
echo "  tail -f $LOG_FILE  - Follow logs in real-time"
echo ""

