from __future__ import annotations

import pathlib
from collections.abc import Generator
from typing import Literal

import pytest
from PyQt5 import QtWidgets
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QKeyEvent
from pytestqt.qtbot import QtBot

import labelme.app
import labelme.config
import labelme.testing


@pytest.fixture(autouse=True)
def _isolated_qtsettings(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    settings_file = tmp_path / "qtsettings.ini"
    settings: QSettings = QSettings(str(settings_file), QSettings.IniFormat)
    monkeypatch.setattr(
        labelme.app.QtCore, "QSettings", lambda *args, **kwargs: settings
    )
    yield


def _show_window_and_wait_for_imagedata(
    qtbot: QtBot, win: labelme.app.MainWindow
) -> None:
    win.show()

    def check_imageData():
        assert hasattr(win, "imageData")
        assert win.imageData is not None

    qtbot.waitUntil(check_imageData)  # wait for loadFile


@pytest.mark.gui
def test_MainWindow_open(qtbot: QtBot) -> None:
    win: labelme.app.MainWindow = labelme.app.MainWindow()
    qtbot.addWidget(win)
    win.show()
    win.close()


@pytest.mark.gui
def test_MainWindow_open_img(qtbot: QtBot, data_path: pathlib.Path) -> None:
    image_file: str = str(data_path / "raw/2011_000003.jpg")
    win: labelme.app.MainWindow = labelme.app.MainWindow(filename=image_file)
    qtbot.addWidget(win)
    _show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    win.close()


@pytest.mark.gui
def test_MainWindow_open_json(qtbot: QtBot, data_path: pathlib.Path) -> None:
    json_files: list[str] = [
        str(data_path / "annotated_with_data/apc2016_obj3.json"),
        str(data_path / "annotated/2011_000003.json"),
    ]
    json_file: str
    for json_file in json_files:
        labelme.testing.assert_labelfile_sanity(json_file)

        win: labelme.app.MainWindow = labelme.app.MainWindow(filename=json_file)
        qtbot.addWidget(win)
        _show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
        win.close()


@pytest.mark.gui
@pytest.mark.parametrize("scenario", ["raw", "annotated", "annotated_nested"])
def test_MainWindow_open_dir(
    qtbot: QtBot,
    scenario: Literal["raw", "annotated", "annotated_nested"],
    data_path: pathlib.Path,
) -> None:
    directory: str
    output_dir: str | None
    if scenario == "annotated_nested":
        directory = str(data_path / "annotated_nested" / "images")
        output_dir = str(data_path / "annotated_nested" / "annotations")
    else:
        directory = str(data_path / scenario)
        output_dir = None

    win: labelme.app.MainWindow = labelme.app.MainWindow(
        filename=directory, output_dir=output_dir
    )
    qtbot.addWidget(win)
    _show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)

    first_image_name: str = "2011_000003.jpg"
    second_image_name: str = "2011_000006.jpg"

    assert win.imagePath
    assert pathlib.Path(win.imagePath).name == first_image_name
    win._open_prev_image()
    qtbot.wait(100)
    assert pathlib.Path(win.imagePath).name == first_image_name

    win._open_next_image()
    qtbot.wait(100)
    assert pathlib.Path(win.imagePath).name == second_image_name
    win._open_prev_image()
    qtbot.wait(100)
    assert pathlib.Path(win.imagePath).name == first_image_name

    assert win.fileListWidget.count() == 3
    expected_check_state = (
        Qt.Checked if scenario.startswith("annotated") else Qt.Unchecked
    )
    for index in range(win.fileListWidget.count()):
        item: QtWidgets.QListWidgetItem | None = win.fileListWidget.item(index)
        assert item
        assert item.checkState() == expected_check_state


@pytest.mark.gui
def test_MainWindow_annotate_jpg(
    qtbot: QtBot, data_path: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    input_file: str = str(data_path / "raw/2011_000003.jpg")
    out_file: str = str(tmp_path / "2011_000003.json")

    config: dict = labelme.config._get_default_config_and_create_labelmerc()
    win: labelme.app.MainWindow = labelme.app.MainWindow(
        config=config,
        filename=input_file,
        output_file=out_file,
    )
    qtbot.addWidget(win)
    _show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)

    label: str = "whole"
    canvas_size: QSize = win.canvas.size()
    points: list[tuple[float, float]] = [
        (canvas_size.width() * 0.25, canvas_size.height() * 0.25),
        (canvas_size.width() * 0.75, canvas_size.height() * 0.25),
        (canvas_size.width() * 0.75, canvas_size.height() * 0.75),
        (canvas_size.width() * 0.25, canvas_size.height() * 0.75),
    ]
    win._switch_canvas_mode(edit=False, createMode="polygon")
    qtbot.wait(100)

    def click(xy: tuple[float, float]) -> None:
        qtbot.mouseMove(win.canvas, pos=QPoint(int(xy[0]), int(xy[1])))
        qtbot.wait(100)
        qtbot.mousePress(win.canvas, Qt.LeftButton, pos=QPoint(int(xy[0]), int(xy[1])))
        qtbot.wait(100)

    [click(xy=xy) for xy in points]

    def interact() -> None:
        qtbot.keyClicks(win.labelDialog.edit, label)
        qtbot.wait(100)
        qtbot.keyClick(win.labelDialog.edit, Qt.Key_Enter)
        qtbot.wait(100)

    QTimer.singleShot(300, interact)

    click(xy=points[0])

    assert len(win.canvas.shapes) == 1
    assert len(win.canvas.shapes[0].points) == 4
    assert win.canvas.shapes[0].label == "whole"
    assert win.canvas.shapes[0].shape_type == "polygon"
    assert win.canvas.shapes[0].group_id is None
    assert win.canvas.shapes[0].mask is None
    assert win.canvas.shapes[0].flags == {}

    win.saveFile()

    labelme.testing.assert_labelfile_sanity(out_file)


@pytest.mark.gui
def test_image_navigation_while_selecting_shape(
    qtbot: QtBot, data_path: pathlib.Path
) -> None:
    win: labelme.app.MainWindow = labelme.app.MainWindow(
        filename=str(data_path / "annotated")
    )
    qtbot.addWidget(win)
    _show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)

    # Incident: https://github.com/wkentaro/labelme/pull/1716 {{
    point = QPoint(250, 200)
    qtbot.mouseMove(win.canvas, pos=point)
    qtbot.mouseClick(win.canvas, Qt.LeftButton, pos=point)
    qtbot.wait(100)

    qtbot.mouseClick(win.fileListWidget, Qt.LeftButton)
    qtbot.wait(100)

    qtbot.keyClick(win.fileListWidget, Qt.Key_Down)
    qtbot.wait(100)
    qtbot.keyClick(win.canvas, Qt.Key_Down)
    qtbot.wait(100)
    # }}

    win.close()


@pytest.mark.gui
def test_navigation_with_n_and_p_keys(qtbot: QtBot, data_path: pathlib.Path) -> None:
    """Test vim-like navigation with n (next) and p (previous) keys."""
    directory: str = str(data_path / "raw")
    win: labelme.app.MainWindow = labelme.app.MainWindow(filename=directory)
    qtbot.addWidget(win)
    _show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)

    # Verify we have 3 images
    assert win.fileListWidget.count() == 3
    
    # Get initial image name
    initial_row = win.fileListWidget.currentRow()
    assert initial_row == 0
    assert win.imagePath
    initial_image_name = pathlib.Path(win.imagePath).name
    assert initial_image_name == "2011_000003.jpg"

    # Test 1: Press 'n' to go to next image (should go to image 1)
    qtbot.keyClick(win, Qt.Key_N)
    qtbot.wait(100)
    assert win.fileListWidget.currentRow() == 1
    assert pathlib.Path(win.imagePath).name == "2011_000006.jpg"

    # Test 2: Press 'p' to go to previous image (should go back to image 0)
    qtbot.keyClick(win, Qt.Key_P)
    qtbot.wait(100)
    assert win.fileListWidget.currentRow() == 0
    assert pathlib.Path(win.imagePath).name == initial_image_name

    # Test 3: Press '2n' to go to next 2 images
    # First press '2'
    key_event_2 = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_2, Qt.NoModifier, "2")
    win.keyPressEvent(key_event_2)
    qtbot.wait(50)
    # Then press 'n'
    qtbot.keyClick(win, Qt.Key_N)
    qtbot.wait(100)
    assert win.fileListWidget.currentRow() == 2
    assert pathlib.Path(win.imagePath).name == "2011_000025.jpg"

    # Test 4: Press 'p' to go back one (should go to image 1)
    qtbot.keyClick(win, Qt.Key_P)
    qtbot.wait(100)
    assert win.fileListWidget.currentRow() == 1
    assert pathlib.Path(win.imagePath).name == "2011_000006.jpg"

    # Test 5: Press '10n' - should go to next 10, but only 1 more available (to image 2)
    # Press '1'
    key_event_1 = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_1, Qt.NoModifier, "1")
    win.keyPressEvent(key_event_1)
    qtbot.wait(50)
    # Press '0'
    key_event_0 = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_0, Qt.NoModifier, "0")
    win.keyPressEvent(key_event_0)
    qtbot.wait(50)
    # Press 'n'
    qtbot.keyClick(win, Qt.Key_N)
    qtbot.wait(100)
    # Should be at last image (row 2)
    assert win.fileListWidget.currentRow() == 2
    assert pathlib.Path(win.imagePath).name == "2011_000025.jpg"

    # Test 6: Press '100p' - should go back 100, but only 2 available (to image 0)
    # Press '1'
    win.keyPressEvent(key_event_1)
    qtbot.wait(50)
    # Press '0'
    win.keyPressEvent(key_event_0)
    qtbot.wait(50)
    # Press '0' again
    win.keyPressEvent(key_event_0)
    qtbot.wait(50)
    # Press 'p'
    qtbot.keyClick(win, Qt.Key_P)
    qtbot.wait(100)
    # Should be at first image (row 0)
    assert win.fileListWidget.currentRow() == 0
    assert pathlib.Path(win.imagePath).name == initial_image_name

    # Test 7: Press 'n' at first image - should go to next
    qtbot.keyClick(win, Qt.Key_N)
    qtbot.wait(100)
    assert win.fileListWidget.currentRow() == 1

    # Test 8: Press 'p' at middle image - should go to previous
    qtbot.keyClick(win, Qt.Key_P)
    qtbot.wait(100)
    assert win.fileListWidget.currentRow() == 0

    win.close()


@pytest.mark.gui
def test_navigation_number_prefix_timeout(qtbot: QtBot, data_path: pathlib.Path) -> None:
    """Test that number prefix times out after 1 second."""
    directory: str = str(data_path / "raw")
    win: labelme.app.MainWindow = labelme.app.MainWindow(filename=directory)
    qtbot.addWidget(win)
    _show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)

    # Press '1' to start building prefix
    key_event_1 = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_1, Qt.NoModifier, "1")
    win.keyPressEvent(key_event_1)
    qtbot.wait(50)
    assert win._nav_number_prefix == "1"

    # Wait for timeout (1 second + small buffer)
    qtbot.wait(1100)
    # Prefix should be cleared
    assert win._nav_number_prefix == ""

    win.close()
