#!/bin/bash

# restart.sh - Restart labelme application
# Stops running instance and starts a new one

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Restarting Labelme..."
echo "=========================================="
echo ""

# Stop existing instance (ignore errors if not running)
"$SCRIPT_DIR/stop.sh" || true

# Wait a moment for processes to fully stop
sleep 2

# Start new instance
echo ""
"$SCRIPT_DIR/run.sh" "$@"

