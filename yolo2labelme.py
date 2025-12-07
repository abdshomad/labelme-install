#!/usr/bin/env python3
"""
Convert YOLO format annotations to Labelme JSON format.

Usage:
    python yolo2labelme.py <yolo_dataset_dir> <output_dir> [--yaml <yaml_file>]
    
Example:
    python yolo2labelme.py /path/to/yolo/dataset /path/to/output --yaml dataset.yaml
"""

import argparse
import base64
import json
import os
import os.path as osp
from pathlib import Path
from typing import Dict, List, Tuple

import yaml
from PIL import Image


def load_yolo_classes(yaml_file: str) -> Dict[int, str]:
    """Load class names from YOLO YAML file."""
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    
    classes = {}
    if 'names' in data:
        classes = {int(k): v for k, v in data['names'].items()}
    return classes


def yolo_to_labelme_bbox(
    yolo_line: str, img_width: int, img_height: int
) -> Tuple[float, float, float, float]:
    """
    Convert YOLO format (normalized center_x, center_y, width, height) 
    to labelme rectangle format (x1, y1, x2, y2).
    
    YOLO format: class_id center_x center_y width height (all normalized 0-1)
    Labelme format: [[x1, y1], [x2, y2]] (absolute pixel coordinates)
    """
    parts = yolo_line.strip().split()
    if len(parts) < 5:
        return None
    
    class_id = int(parts[0])
    center_x = float(parts[1])
    center_y = float(parts[2])
    width = float(parts[3])
    height = float(parts[4])
    
    # Convert normalized coordinates to absolute pixel coordinates
    x_center = center_x * img_width
    y_center = center_y * img_height
    bbox_width = width * img_width
    bbox_height = height * img_height
    
    # Calculate rectangle corners
    x1 = x_center - bbox_width / 2
    y1 = y_center - bbox_height / 2
    x2 = x_center + bbox_width / 2
    y2 = y_center + bbox_height / 2
    
    # Ensure coordinates are within image bounds
    x1 = max(0, min(x1, img_width))
    y1 = max(0, min(y1, img_height))
    x2 = max(0, min(x2, img_width))
    y2 = max(0, min(y2, img_height))
    
    return (x1, y1, x2, y2), class_id


def image_to_base64(image_path: str) -> str:
    """Convert image to base64 string."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def convert_yolo_to_labelme(
    yolo_dir: str,
    output_dir: str,
    yaml_file: str = None,
    include_image_data: bool = True,
    split: str = 'train'
):
    """
    Convert YOLO format dataset to Labelme JSON format.
    
    Args:
        yolo_dir: Root directory of YOLO dataset (contains images/ and labels/)
        output_dir: Output directory for labelme JSON files
        yaml_file: Path to YOLO YAML file (for class names)
        include_image_data: Whether to include image data in JSON (default: True)
        split: Dataset split to convert ('train', 'val', or 'test')
    """
    yolo_dir = Path(yolo_dir)
    output_dir = Path(output_dir)
    
    # Load class names
    classes = {}
    if yaml_file and osp.exists(yaml_file):
        classes = load_yolo_classes(yaml_file)
        print(f"Loaded {len(classes)} classes from {yaml_file}")
        for class_id, class_name in sorted(classes.items()):
            print(f"  {class_id}: {class_name}")
    else:
        print("Warning: No YAML file provided. Using class IDs as labels.")
    
    # Set up paths
    images_dir = yolo_dir / 'images' / split
    labels_dir = yolo_dir / 'labels' / split
    
    if not images_dir.exists():
        raise ValueError(f"Images directory not found: {images_dir}")
    if not labels_dir.exists():
        raise ValueError(f"Labels directory not found: {labels_dir}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_files = [
        f for f in images_dir.iterdir()
        if f.suffix.lower() in image_extensions
    ]
    
    print(f"\nFound {len(image_files)} images in {images_dir}")
    print(f"Converting to Labelme format in {output_dir}...")
    
    converted = 0
    skipped = 0
    
    for image_file in image_files:
        # Find corresponding label file
        label_file = labels_dir / (image_file.stem + '.txt')
        
        if not label_file.exists():
            print(f"Warning: No label file found for {image_file.name}, skipping...")
            skipped += 1
            continue
        
        # Load image to get dimensions
        try:
            img = Image.open(image_file)
            img_width, img_height = img.size
        except Exception as e:
            print(f"Error loading image {image_file.name}: {e}, skipping...")
            skipped += 1
            continue
        
        # Read YOLO labels
        shapes = []
        with open(label_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                result = yolo_to_labelme_bbox(line, img_width, img_height)
                if result is None:
                    continue
                
                (x1, y1, x2, y2), class_id = result
                
                # Get class name
                label = classes.get(class_id, f"class_{class_id}")
                
                # Create rectangle shape for labelme
                shape = {
                    "label": label,
                    "points": [[x1, y1], [x2, y2]],
                    "group_id": None,
                    "description": "",
                    "shape_type": "rectangle",
                    "flags": {}
                }
                shapes.append(shape)
        
        # Create labelme JSON structure
        labelme_data = {
            "version": "5.0.1",
            "flags": {},
            "shapes": shapes,
            "imagePath": osp.relpath(image_file, output_dir) if not include_image_data else osp.basename(image_file),
            "imageData": image_to_base64(image_file) if include_image_data else None,
            "imageHeight": img_height,
            "imageWidth": img_width
        }
        
        # Save JSON file
        json_file = output_dir / (image_file.stem + '.json')
        with open(json_file, 'w') as f:
            json.dump(labelme_data, f, indent=2)
        
        converted += 1
        if converted % 100 == 0:
            print(f"Converted {converted} files...")
    
    print(f"\n✓ Conversion complete!")
    print(f"  Converted: {converted} files")
    print(f"  Skipped: {skipped} files")
    print(f"  Output directory: {output_dir}")
    
    # Create labels.txt file for labelme
    if classes:
        labels_file = output_dir / 'labels.txt'
        with open(labels_file, 'w') as f:
            for class_id in sorted(classes.keys()):
                f.write(f"{classes[class_id]}\n")
        print(f"  Labels file: {labels_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert YOLO format annotations to Labelme JSON format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert train split
  python yolo2labelme.py /path/to/yolo/dataset output_dir --yaml dataset.yaml
  
  # Convert without embedding image data
  python yolo2labelme.py /path/to/yolo/dataset output_dir --yaml dataset.yaml --no-image-data
  
  # Convert validation split
  python yolo2labelme.py /path/to/yolo/dataset output_dir --yaml dataset.yaml --split val
        """
    )
    parser.add_argument(
        'yolo_dir',
        type=str,
        help='Root directory of YOLO dataset (contains images/ and labels/ subdirectories)'
    )
    parser.add_argument(
        'output_dir',
        type=str,
        help='Output directory for Labelme JSON files'
    )
    parser.add_argument(
        '--yaml',
        type=str,
        default=None,
        help='Path to YOLO YAML file (for class names)'
    )
    parser.add_argument(
        '--no-image-data',
        action='store_true',
        help='Do not include image data in JSON files (use relative paths instead)'
    )
    parser.add_argument(
        '--split',
        type=str,
        default='train',
        choices=['train', 'val', 'test'],
        help='Dataset split to convert (default: train)'
    )
    
    args = parser.parse_args()
    
    # Auto-detect YAML file if not provided
    yaml_file = args.yaml
    if not yaml_file:
        yolo_path = Path(args.yolo_dir)
        # Look for YAML files in the dataset directory
        yaml_files = list(yolo_path.glob('*.yaml')) + list(yolo_path.glob('*.yml'))
        if yaml_files:
            yaml_file = str(yaml_files[0])
            print(f"Auto-detected YAML file: {yaml_file}")
    
    convert_yolo_to_labelme(
        yolo_dir=args.yolo_dir,
        output_dir=args.output_dir,
        yaml_file=yaml_file,
        include_image_data=not args.no_image_data,
        split=args.split
    )


if __name__ == '__main__':
    main()

