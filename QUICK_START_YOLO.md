# Quick Start: Using Labelme with Your YOLO Dataset

## Your Dataset Path
```
/home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format
```

## Method 1: One-Command Solution (Easiest)

```bash
# Convert YOLO format and open in Labelme
./run_with_yolo.sh /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format
```

This will:
1. ✅ Convert all YOLO annotations to Labelme format
2. ✅ Create output directory: `chicken-detection-ultralytics-format_labelme`
3. ✅ Open Labelme GUI with your converted annotations

## Method 2: Step-by-Step

### Step 1: Convert YOLO to Labelme Format

```bash
# Activate virtual environment
source .venv/bin/activate

# Convert train split
python yolo2labelme.py \
    /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format \
    ./chicken_labelme_train \
    --yaml /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format/chicken-detection-ultralytics-format.yaml \
    --split train \
    --no-image-data

# Convert validation split (optional)
python yolo2labelme.py \
    /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format \
    ./chicken_labelme_val \
    --yaml /home/aiserver/LABS/CHICKEN-COUNTING/chicken-counting-video-github/chicken-detection-ultralytics-format/chicken-detection-ultralytics-format.yaml \
    --split val \
    --no-image-data
```

### Step 2: Run Labelme

```bash
# Open Labelme with train split
labelme ./chicken_labelme_train --labels ./chicken_labelme_train/labels.txt --nodata

# Or use the run script
./run.sh ./chicken_labelme_train --labels ./chicken_labelme_train/labels.txt --nodata
```

## Method 3: Using run.sh with Converted Data

After converting (using Method 2, Step 1), you can use the standard run script:

```bash
# Run labelme in background
./run.sh ./chicken_labelme_train --labels ./chicken_labelme_train/labels.txt --nodata

# Monitor the process
./monitor.sh

# Stop when done
./stop.sh
```

## What Gets Converted?

- **YOLO Format**: Bounding boxes in normalized coordinates
  - Format: `class_id center_x center_y width height` (all 0-1)
  - Class 0 = "chicken" (from your YAML file)

- **Labelme Format**: JSON files with rectangle annotations
  - Each image gets a `.json` file
  - Bounding boxes converted to rectangles
  - Class names loaded from YAML file

## Example: Viewing a Specific Image

```bash
# After conversion, open specific image
labelme ./chicken_labelme_train/2025-10-23-chicken-000001.jpg \
    --labels ./chicken_labelme_train/labels.txt \
    --nodata
```

## Tips

1. **Use `--nodata` flag**: Prevents embedding images in JSON (saves space, faster loading)

2. **Use `--labels` flag**: Ensures consistent label names and enables validation

3. **Use `--autosave` flag**: Automatically saves annotations as you work
   ```bash
   labelme ./chicken_labelme_train --labels ./chicken_labelme_train/labels.txt --nodata --autosave
   ```

4. **Validate labels**: Only allow labels from your labels.txt file
   ```bash
   labelme ./chicken_labelme_train --labels ./chicken_labelme_train/labels.txt --nodata --validatelabel exact
   ```

## File Structure After Conversion

```
chicken_labelme_train/
├── 2025-10-23-chicken-000001.jpg
├── 2025-10-23-chicken-000001.json
├── 2025-10-23-chicken-000001 (1).jpg
├── 2025-10-23-chicken-000001 (1).json
├── ...
└── labels.txt
```

## Troubleshooting

### "DISPLAY not set"
If running on a remote server, enable X11 forwarding:
```bash
ssh -X user@host
# Then run labelme
```

### "No label file found"
- Check that label files exist in `labels/train/` directory
- Ensure label files have same name as images (with `.txt` extension)

### "Virtual environment not found"
```bash
./install.sh
```

## Next Steps

After viewing/editing annotations in Labelme:
- Annotations are saved as JSON files
- You can export to other formats using Labelme's export tools
- Original YOLO files remain unchanged

