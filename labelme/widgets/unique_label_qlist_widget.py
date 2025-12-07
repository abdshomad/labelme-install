import html
import re
from typing import Optional

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from .label_list_widget import HTMLDelegate


class _EscapableQListWidget(QtWidgets.QListWidget):
    def keyPressEvent(self, keyEvent: QtGui.QKeyEvent) -> None:  # type: ignore
        super().keyPressEvent(keyEvent)
        if keyEvent.key() == Qt.Key_Escape:
            self.clearSelection()


class UniqueLabelQListWidget(_EscapableQListWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setItemDelegate(HTMLDelegate(parent=self))

    def mousePressEvent(self, mouseEvent: QtGui.QMouseEvent) -> None:  # type: ignore
        super().mousePressEvent(mouseEvent)
        if not self.indexAt(mouseEvent.pos()).isValid():
            self.clearSelection()

    def find_label_item(self, label: str) -> Optional[QtWidgets.QListWidgetItem]:
        for row in range(self.count()):
            item = self.item(row)
            if item and item.data(Qt.UserRole) == label:
                return item
        return None

    def add_label_item(self, label: str, color: tuple[int, int, int], index: Optional[int] = None) -> None:
        if self.find_label_item(label):
            raise ValueError(f"Item for label '{label}' already exists")

        item = QtWidgets.QListWidgetItem()
        item.setData(Qt.UserRole, label)  # for find_label_item
        
        # If index is not provided, use current count
        if index is None:
            index = self.count()
        
        # Format shortcut number: 1-9 for indices 0-8, 0 for index 9 (10th label)
        # Index 0 -> "1", Index 1 -> "2", ..., Index 8 -> "9", Index 9 -> "0"
        if index < 9:
            shortcut_text = str(index + 1)
        elif index == 9:
            shortcut_text = "0"
        else:
            shortcut_text = ""
        
        # Display format: "1. label_name ●" or just "label_name ●" if no shortcut
        if shortcut_text:
            item.setText(
                f"{shortcut_text}. {html.escape(label)} "
                f"<font color='#{color[0]:02x}{color[1]:02x}{color[2]:02x}'>●</font>"
            )
        else:
            item.setText(
                f"{html.escape(label)} "
                f"<font color='#{color[0]:02x}{color[1]:02x}{color[2]:02x}'>●</font>"
            )
        self.addItem(item)
    
    def refresh_label_numbers(self) -> None:
        """Refresh the shortcut numbers for all labels based on their current order."""
        for i in range(self.count()):
            item = self.item(i)
            if item:
                label = item.data(Qt.UserRole)
                current_text = item.text()
                
                # Extract color from HTML if present (handle both single and double quotes)
                color_match = None
                # Try single quotes first
                match = re.search(r"color=['\"]#([0-9a-fA-F]{6})['\"]", current_text)
                if match:
                    hex_color = match.group(1)
                    color_match = (
                        int(hex_color[0:2], 16),
                        int(hex_color[2:4], 16),
                        int(hex_color[4:6], 16),
                    )
                
                # Format shortcut number: 1-9 for indices 0-8, 0 for index 9 (10th label)
                # Index 0 -> "1", Index 1 -> "2", ..., Index 8 -> "9", Index 9 -> "0"
                if i < 9:
                    shortcut_text = str(i + 1)
                elif i == 9:
                    shortcut_text = "0"
                else:
                    shortcut_text = ""
                
                # Rebuild text with updated shortcut number
                if color_match:
                    if shortcut_text:
                        item.setText(
                            f"{shortcut_text}. {html.escape(label)} "
                            f"<font color='#{color_match[0]:02x}{color_match[1]:02x}{color_match[2]:02x}'>●</font>"
                        )
                    else:
                        item.setText(
                            f"{html.escape(label)} "
                            f"<font color='#{color_match[0]:02x}{color_match[1]:02x}{color_match[2]:02x}'>●</font>"
                        )
                else:
                    # Fallback: if we can't extract color, just update the number prefix
                    # Remove existing number prefix if present (e.g., "1. " or "0. ")
                    text_without_prefix = re.sub(r'^\d+\.\s*', '', current_text)
                    if shortcut_text:
                        item.setText(f"{shortcut_text}. {text_without_prefix}")
                    else:
                        item.setText(text_without_prefix)
