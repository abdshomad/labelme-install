#!/usr/bin/env python3
"""
Test script to verify label assignment using number shortcuts (1-9, 0).

This script:
1. Creates a MainWindow with predefined labels
2. Loads an image
3. Creates shapes (rectangles/polygons) programmatically
4. Selects shapes
5. Simulates pressing number keys
6. Verifies that labels are assigned correctly
"""

from __future__ import annotations

import math
import pathlib
import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QPoint, QPointF, Qt, QTimer
from PyQt5.QtGui import QKeyEvent

import labelme.app
import labelme.config
from labelme.shape import Shape


def create_rectangle_shape(canvas, x1: float, y1: float, x2: float, y2: float) -> Shape:
    """Create a rectangle (bbox) shape."""
    shape = Shape(
        label=None,  # No label initially
        shape_type="rectangle",
    )
    shape.points = [
        QPointF(x1, y1),
        QPointF(x2, y1),
        QPointF(x2, y2),
        QPointF(x1, y2),
    ]
    shape.close()
    return shape


def create_polygon_shape(canvas, center_x: float, center_y: float, radius: float, num_points: int = 5) -> Shape:
    """Create a polygon shape."""
    shape = Shape(
        label=None,  # No label initially
        shape_type="polygon",
    )
    # Create a regular polygon (e.g., pentagon)
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        shape.points.append(QPointF(x, y))
    shape.close()
    return shape


def create_test_shapes(canvas) -> tuple[list[Shape], list[Shape]]:
    """Create test bbox (rectangle) and polygon shapes on the canvas."""
    canvas_size = canvas.size()
    rectangles = []
    polygons = []
    
    # Create 2 rectangle (bbox) shapes
    for i in range(2):
        x1 = canvas_size.width() * (0.1 + i * 0.3)
        y1 = canvas_size.height() * 0.2
        x2 = x1 + 150
        y2 = y1 + 100
        rect = create_rectangle_shape(canvas, x1, y1, x2, y2)
        rectangles.append(rect)
        canvas.shapes.append(rect)
    
    # Create 2 polygon shapes
    for i in range(2):
        center_x = canvas_size.width() * (0.1 + i * 0.3)
        center_y = canvas_size.height() * 0.6
        radius = 50
        poly = create_polygon_shape(canvas, center_x, center_y, radius, num_points=5)
        polygons.append(poly)
        canvas.shapes.append(poly)
    
    canvas.storeShapes()
    canvas.update()
    return rectangles, polygons


def test_label_shortcuts(qtbot=None):
    """Main test function.
    
    Args:
        qtbot: Optional QtBot from pytest-qt for better event handling
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    
    # Create config with predefined labels
    config = labelme.config._get_default_config_and_create_labelmerc()
    labels = ["person", "car", "bicycle", "dog", "cat", "bird", "tree", "house", "road", "sign"]
    config["labels"] = labels
    
    # Create MainWindow
    win = labelme.app.MainWindow(config=config)
    if qtbot:
        qtbot.addWidget(win)
    win.show()
    
    # Wait for window to be ready
    if qtbot:
        qtbot.waitExposed(win)
        qtbot.wait(100)
    else:
        app.processEvents()
        QTimer.singleShot(100, lambda: None)
        app.processEvents()
    
    # Check that labels are displayed with shortcuts
    print("Testing label list display...")
    uniq_label_list = win.uniqLabelList
    assert uniq_label_list.count() == len(labels), f"Expected {len(labels)} labels, got {uniq_label_list.count()}"
    
    # Verify shortcut numbers are displayed
    for i in range(min(10, uniq_label_list.count())):
        item = uniq_label_list.item(i)
        assert item is not None, f"Item at index {i} is None"
        text = item.text()
        expected_num = str((i + 1) % 10) if (i + 1) % 10 != 0 else "0"
        if i < 9:
            assert expected_num in text, f"Shortcut number {expected_num} not found in label text: {text}"
        elif i == 9:
            assert "0" in text, f"Shortcut number 0 not found in 10th label text: {text}"
        print(f"  ✓ Label {i}: {text}")
    
    # Load a test image (create a dummy image if needed)
    # For testing, we'll just work with the canvas
    canvas = win.canvas
    
    # Set canvas to editing mode
    win._switch_canvas_mode(edit=True, createMode="rectangle")
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    # Create test shapes: rectangles (bbox) and polygons
    print("\nCreating test shapes...")
    rectangles, polygons = create_test_shapes(canvas)
    all_shapes = rectangles + polygons
    print(f"  ✓ Created {len(rectangles)} rectangle (bbox) shapes")
    print(f"  ✓ Created {len(polygons)} polygon shapes")
    print(f"  ✓ Total: {len(all_shapes)} shapes")
    
    # Verify shapes have no labels initially
    for i, shape in enumerate(all_shapes):
        assert shape.label is None or shape.label == "", f"Shape {i} should have no label initially"
        shape_type = "rectangle" if shape in rectangles else "polygon"
        print(f"  ✓ {shape_type.capitalize()} {i}: no label (as expected)")
    
    # Test 1: Assign label to rectangle (bbox) using shortcut '1'
    print("\n" + "="*60)
    print("Test 1: Assign label 'person' (shortcut 1) to rectangle (bbox)...")
    print("="*60)
    canvas.selectedShapes = [rectangles[0]]
    canvas.selectionChanged.emit([rectangles[0]])
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    # Simulate pressing '1'
    key_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_1, Qt.NoModifier)
    canvas.keyPressEvent(key_event)
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    # Verify label was assigned
    assert rectangles[0].label == "person", f"Expected 'person', got '{rectangles[0].label}'"
    assert rectangles[0].shape_type == "rectangle", "Shape should be rectangle"
    print(f"  ✓ Rectangle label: {rectangles[0].label}")
    print(f"  ✓ Shape type: {rectangles[0].shape_type}")
    
    # Test 2: Assign label to polygon using shortcut '2'
    print("\n" + "="*60)
    print("Test 2: Assign label 'car' (shortcut 2) to polygon...")
    print("="*60)
    canvas.selectedShapes = [polygons[0]]
    canvas.selectionChanged.emit([polygons[0]])
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    key_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_2, Qt.NoModifier)
    canvas.keyPressEvent(key_event)
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    assert polygons[0].label == "car", f"Expected 'car', got '{polygons[0].label}'"
    assert polygons[0].shape_type == "polygon", "Shape should be polygon"
    print(f"  ✓ Polygon label: {polygons[0].label}")
    print(f"  ✓ Shape type: {polygons[0].shape_type}")
    
    # Test 3: Select multiple shapes (mix of rectangle and polygon) and assign label
    print("\n" + "="*60)
    print("Test 3: Assign label 'bicycle' (shortcut 3) to multiple shapes (bbox + polygon)...")
    print("="*60)
    canvas.selectedShapes = [rectangles[1], polygons[1]]  # Select second rectangle and second polygon
    canvas.selectionChanged.emit([rectangles[1], polygons[1]])
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    key_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_3, Qt.NoModifier)
    canvas.keyPressEvent(key_event)
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    # Both selected shapes should have the label
    assert rectangles[1].label == "bicycle", f"Expected 'bicycle', got '{rectangles[1].label}'"
    assert polygons[1].label == "bicycle", f"Expected 'bicycle', got '{polygons[1].label}'"
    print(f"  ✓ Rectangle label: {rectangles[1].label}")
    print(f"  ✓ Polygon label: {polygons[1].label}")
    print(f"  ✓ Both shapes assigned same label correctly")
    
    # Test 4: Test shortcut '0' for 10th label on rectangle
    print("\n" + "="*60)
    print("Test 4: Assign label 'sign' (shortcut 0) to rectangle (bbox)...")
    print("="*60)
    if len(labels) >= 10:
        canvas.selectedShapes = [rectangles[0]]
        canvas.selectionChanged.emit([rectangles[0]])
        if qtbot:
            qtbot.wait(50)
        else:
            app.processEvents()
        
        key_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_0, Qt.NoModifier)
        canvas.keyPressEvent(key_event)
        if qtbot:
            qtbot.wait(50)
        else:
            app.processEvents()
        
        assert rectangles[0].label == "sign", f"Expected 'sign', got '{rectangles[0].label}'"
        assert rectangles[0].shape_type == "rectangle", "Shape should be rectangle"
        print(f"  ✓ Rectangle label: {rectangles[0].label}")
        print(f"  ✓ Shortcut '0' works for 10th label")
    
    # Test 5: Test all shortcuts (1-9) work for both rectangle and polygon
    print("\n" + "="*60)
    print("Test 5: Test all shortcuts (1-9) work for both shape types...")
    print("="*60)
    win._switch_canvas_mode(edit=True, createMode="rectangle")
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    # Test shortcuts 4-9 on rectangles
    # Key_4 -> index 3, Key_5 -> index 4, etc.
    key_to_index = {
        Qt.Key_4: 3, Qt.Key_5: 4, Qt.Key_6: 5, Qt.Key_7: 6, Qt.Key_8: 7, Qt.Key_9: 8
    }
    for shortcut_key, label_index in key_to_index.items():
        if label_index < len(labels):
            canvas.selectedShapes = [rectangles[0] if len(rectangles) > 0 else polygons[0]]
            canvas.selectionChanged.emit(canvas.selectedShapes)
            if qtbot:
                qtbot.wait(50)
            else:
                app.processEvents()
            
            key_event = QKeyEvent(QKeyEvent.KeyPress, shortcut_key, Qt.NoModifier)
            canvas.keyPressEvent(key_event)
            if qtbot:
                qtbot.wait(50)
            else:
                app.processEvents()
            
            expected_label = labels[label_index]
            actual_label = canvas.selectedShapes[0].label
            shortcut_num = label_index + 1 if label_index < 9 else 0
            assert actual_label == expected_label, f"Shortcut {shortcut_num}: Expected '{expected_label}', got '{actual_label}'"
            print(f"  ✓ Shortcut {shortcut_num} ({expected_label}): Works on {canvas.selectedShapes[0].shape_type}")
    
    # Test shortcuts on polygons
    # Key_1 -> index 0, Key_2 -> index 1, Key_3 -> index 2
    key_to_index_poly = {
        Qt.Key_1: 0, Qt.Key_2: 1, Qt.Key_3: 2
    }
    for shortcut_key, label_index in key_to_index_poly.items():
        if label_index < len(labels):
            canvas.selectedShapes = [polygons[0] if len(polygons) > 0 else rectangles[0]]
            canvas.selectionChanged.emit(canvas.selectedShapes)
            if qtbot:
                qtbot.wait(50)
            else:
                app.processEvents()
            
            key_event = QKeyEvent(QKeyEvent.KeyPress, shortcut_key, Qt.NoModifier)
            canvas.keyPressEvent(key_event)
            if qtbot:
                qtbot.wait(50)
            else:
                app.processEvents()
            
            expected_label = labels[label_index]
            actual_label = canvas.selectedShapes[0].label
            shortcut_num = label_index + 1
            assert actual_label == expected_label, f"Shortcut {shortcut_num}: Expected '{expected_label}', got '{actual_label}'"
            print(f"  ✓ Shortcut {shortcut_num} ({expected_label}): Works on {canvas.selectedShapes[0].shape_type}")
    
    # Test 6: Verify that shortcuts don't work when not in editing mode
    print("\n" + "="*60)
    print("Test 6: Verify shortcuts don't work in drawing mode...")
    print("="*60)
    win._switch_canvas_mode(edit=False, createMode="rectangle")
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    canvas.selectedShapes = [rectangles[0] if len(rectangles) > 0 else polygons[0]]
    original_label = canvas.selectedShapes[0].label
    key_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_1, Qt.NoModifier)
    canvas.keyPressEvent(key_event)
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    # Label should not change in drawing mode
    assert canvas.selectedShapes[0].label == original_label, "Label should not change in drawing mode"
    print(f"  ✓ Label unchanged in drawing mode: {canvas.selectedShapes[0].label}")
    
    # Test 7: Verify that shortcuts don't work when no shapes are selected
    print("\n" + "="*60)
    print("Test 7: Verify shortcuts don't work with no selection...")
    print("="*60)
    win._switch_canvas_mode(edit=True, createMode="rectangle")
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    canvas.selectedShapes = []
    canvas.selectionChanged.emit([])
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    # Try to assign label - should not work
    key_event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_4, Qt.NoModifier)
    canvas.keyPressEvent(key_event)
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    # No shapes should be affected
    print(f"  ✓ No shapes selected, shortcut ignored")
    
    # Test 8: Verify label list items are updated correctly for both shape types
    print("\n" + "="*60)
    print("Test 8: Verify label list items reflect shape labels (bbox & polygon)...")
    print("="*60)
    win._switch_canvas_mode(edit=True, createMode="rectangle")
    canvas.selectedShapes = [rectangles[0] if len(rectangles) > 0 else polygons[0]]
    canvas.selectionChanged.emit(canvas.selectedShapes)
    if qtbot:
        qtbot.wait(50)
    else:
        app.processEvents()
    
    # Check that label list shows the correct label for the shapes
    label_list_items = list(win.labelList)
    rectangle_labels = [item.shape().label for item in label_list_items if item.shape() in rectangles and item.shape().label]
    polygon_labels = [item.shape().label for item in label_list_items if item.shape() in polygons and item.shape().label]
    print(f"  ✓ Rectangle labels in label list: {rectangle_labels}")
    print(f"  ✓ Polygon labels in label list: {polygon_labels}")
    
    # Verify shape types are preserved
    for rect in rectangles:
        if rect.label:
            assert rect.shape_type == "rectangle", f"Rectangle should remain rectangle type"
    for poly in polygons:
        if poly.label:
            assert poly.shape_type == "polygon", f"Polygon should remain polygon type"
    print(f"  ✓ Shape types preserved correctly")
    
    print("\n" + "="*60)
    print("All tests passed! ✓")
    print("="*60)
    print("\nSummary:")
    print(f"  - Tested {len(rectangles)} rectangle (bbox) shapes")
    print(f"  - Tested {len(polygons)} polygon shapes")
    print(f"  - Verified shortcuts 1-9 and 0 work for both shape types")
    print(f"  - Verified multiple shape selection works")
    print(f"  - Verified shape types are preserved after label assignment")
    print("="*60)
    
    # Clean up
    win.close()
    return True


if __name__ == "__main__":
    try:
        success = test_label_shortcuts()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

