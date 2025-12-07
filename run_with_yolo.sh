#!/bin/bash

# run_with_yolo.sh - Convert YOLO format to Labelme and run labelme
# Usage: ./run_with_yolo.sh <yolo_dataset_dir> [output_dir]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <yolo_dataset_dir> [output_dir] [--split train|val|test]"
    echo ""
    echo "Example:"
    echo "  $0 /path/to/yolo/dataset"
    echo "  $0 /path/to/yolo/dataset /path/to/output"
    echo "  $0 /path/to/yolo/dataset /path/to/output --split train"
    exit 1
fi

YOLO_DIR="$1"
OUTPUT_DIR=""
SPLIT="train"

# Parse arguments
shift
while [ $# -gt 0 ]; do
    case "$1" in
        --split)
            SPLIT="$2"
            shift 2
            ;;
        *)
            if [ -z "$OUTPUT_DIR" ]; then
                OUTPUT_DIR="$1"
            fi
            shift
            ;;
    esac
done

# Set default output directory if not provided
if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="${YOLO_DIR}_labelme"
fi

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at: $VENV_DIR"
    echo "Please run ./install.sh first to install dependencies."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install uv first."
    echo "Visit: https://github.com/astral-sh/uv"
    exit 1
fi

# Check if YOLO directory exists
if [ ! -d "$YOLO_DIR" ]; then
    echo "Error: YOLO dataset directory not found: $YOLO_DIR"
    exit 1
fi

# Find YAML file
YAML_FILE=""
if [ -f "$YOLO_DIR"/*.yaml ]; then
    YAML_FILE=$(ls "$YOLO_DIR"/*.yaml | head -1)
elif [ -f "$YOLO_DIR"/*.yml ]; then
    YAML_FILE=$(ls "$YOLO_DIR"/*.yml | head -1)
fi

echo "=========================================="
echo "YOLO to Labelme Converter"
echo "=========================================="
echo "YOLO directory: $YOLO_DIR"
echo "Output directory: $OUTPUT_DIR"
if [ -n "$YAML_FILE" ]; then
    echo "YAML file: $YAML_FILE"
fi
echo "Split: $SPLIT"
echo ""

# Convert YOLO to Labelme format
cd "$SCRIPT_DIR"
uv run python yolo2labelme.py "$YOLO_DIR" "$OUTPUT_DIR" \
    ${YAML_FILE:+--yaml "$YAML_FILE"} \
    --split "$SPLIT" \
    --no-image-data

echo ""
echo "=========================================="
echo "Starting Labelme..."
echo "=========================================="
echo ""

# Check for labels.txt
LABELS_FILE="$OUTPUT_DIR/labels.txt"
if [ -f "$LABELS_FILE" ]; then
    echo "Using labels from: $LABELS_FILE"
    uv run labelme "$OUTPUT_DIR" --labels "$LABELS_FILE" --nodata
else
    echo "No labels.txt found, starting labelme without predefined labels..."
    uv run labelme "$OUTPUT_DIR" --nodata
fi

