# Using Labelme with YOLO Format Datasets

This guide explains how to use Labelme with existing Ultralytics YOLO format annotations.

## Quick Start

### Option 1: Use the Helper Script (Recommended)

```bash
# Convert YOLO format and open in Labelme
./run_with_yolo.sh /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format
```

This will:
1. Convert YOLO annotations to Labelme JSON format
2. Open Labelme with the converted annotations
3. Allow you to view and edit the annotations

### Option 2: Manual Conversion

```bash
# Activate virtual environment
source .venv/bin/activate

# Convert YOLO format to Labelme format
python yolo2labelme.py \
    /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format \
    ./chicken_labelme \
    --yaml /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format/chicken-detection-ultralytics-format.yaml

# Run Labelme on the converted directory
labelme ./chicken_labelme --labels ./chicken_labelme/labels.txt --nodata
```

## Conversion Script Options

The `yolo2labelme.py` script supports the following options:

```bash
python yolo2labelme.py <yolo_dir> <output_dir> [options]

Options:
  --yaml PATH          Path to YOLO YAML file (for class names)
  --no-image-data      Don't embed images in JSON (use relative paths)
  --split {train,val,test}  Dataset split to convert (default: train)
```

### Examples

```bash
# Convert train split with image data embedded
python yolo2labelme.py /path/to/yolo ./output --yaml dataset.yaml

# Convert validation split without embedding images
python yolo2labelme.py /path/to/yolo ./output --yaml dataset.yaml --split val --no-image-data

# Convert test split (YAML auto-detected)
python yolo2labelme.py /path/to/yolo ./output --split test
```

## YOLO Format Structure

The script expects the following YOLO dataset structure:

```
yolo_dataset/
├── images/
│   ├── train/
│   │   ├── image1.jpg
│   │   └── image2.jpg
│   └── val/
│       └── image3.jpg
├── labels/
│   ├── train/
│   │   ├── image1.txt
│   │   └── image2.txt
│   └── val/
│       └── image3.txt
└── dataset.yaml (optional, for class names)
```

### YOLO Label Format

Each `.txt` file contains one annotation per line:
```
class_id center_x center_y width height
```

All coordinates are normalized (0-1):
- `class_id`: Integer class ID
- `center_x`: Normalized x-coordinate of bbox center
- `center_y`: Normalized y-coordinate of bbox center
- `width`: Normalized bbox width
- `height`: Normalized bbox height

### YOLO YAML Format

The YAML file should contain class names:
```yaml
names:
  0: chicken
  1: rooster
  2: hen
```

## Labelme Format

After conversion, you'll get:
- JSON files (one per image) with annotations in Labelme format
- `labels.txt` file with class names (for use with `--labels` flag)

### Labelme JSON Structure

```json
{
  "version": "5.0.1",
  "flags": {},
  "shapes": [
    {
      "label": "chicken",
      "points": [[x1, y1], [x2, y2]],
      "shape_type": "rectangle",
      "flags": {}
    }
  ],
  "imagePath": "image.jpg",
  "imageData": null,
  "imageHeight": 1080,
  "imageWidth": 1920
}
```

## Using Labelme with Converted Data

### Basic Usage

```bash
# Open Labelme with converted annotations
labelme ./chicken_labelme --labels ./chicken_labelme/labels.txt --nodata
```

### Advanced Options

```bash
# With auto-save enabled
labelme ./chicken_labelme --labels ./chicken_labelme/labels.txt --nodata --autosave

# With label validation (only allow labels from labels.txt)
labelme ./chicken_labelme --labels ./chicken_labelme/labels.txt --nodata --validatelabel exact

# Open specific image
labelme ./chicken_labelme/image.jpg --labels ./chicken_labelme/labels.txt --nodata
```

## Converting Back to YOLO Format

If you edit annotations in Labelme and want to convert back to YOLO format, you can use the `labelme2yolo` script (if available) or export using Labelme's export functionality.

## Troubleshooting

### Issue: "No label file found for image"
- Ensure label files have the same name as image files (with `.txt` extension)
- Check that labels are in the correct split directory (`labels/train/`, `labels/val/`, etc.)

### Issue: "Images directory not found"
- Verify the YOLO dataset has the structure: `images/train/`, `images/val/`, etc.
- Check the path you provided to the script

### Issue: "Class names not loading"
- Ensure the YAML file exists and has the correct format
- Check that the `names` section is present in the YAML file

### Issue: DISPLAY not set (for GUI)
- If running remotely, enable X11 forwarding: `ssh -X user@host`
- Or set DISPLAY: `export DISPLAY=:0`

## Example: Full Workflow

```bash
# 1. Install labelme (if not already done)
./install.sh

# 2. Convert YOLO format to Labelme
python yolo2labelme.py \
    /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format \
    ./chicken_labelme \
    --yaml /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format/chicken-detection-ultralytics-format.yaml \
    --split train

# 3. Open in Labelme for viewing/editing
labelme ./chicken_labelme --labels ./chicken_labelme/labels.txt --nodata

# 4. Or use the helper script (does steps 2-3 automatically)
./run_with_yolo.sh /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format
```

## Notes

- The conversion script converts YOLO bounding boxes to Labelme rectangles
- Image data is not embedded by default (use `--no-image-data` is default in helper script)
- Original YOLO files are not modified - conversion creates new files
- You can convert multiple splits separately (train, val, test)

