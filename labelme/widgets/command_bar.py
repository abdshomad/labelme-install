from __future__ import annotations

import re
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt


class CommandBar(QtWidgets.QLineEdit):
    """Vim-like command bar for navigation commands."""
    
    commandExecuted = QtCore.pyqtSignal(int, str)  # count, direction
    commandCancelled = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Enter command (e.g., 10h or 10l)")
        self.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
                font-family: monospace;
            }
        """)
        
        # Set initial text to show the colon prompt
        self.setText(":")
        
        # Connect signals
        self.returnPressed.connect(self._on_return_pressed)
        self.textChanged.connect(self._on_text_changed)
    
    def _on_text_changed(self, text: str) -> None:
        """Ensure the colon is always present at the start."""
        if not text.startswith(":"):
            # If user deletes the colon, restore it
            cursor_pos = self.cursorPosition()
            self.setText(":" + text.lstrip(":"))
            # Restore cursor position
            self.setCursorPosition(min(cursor_pos + 1, len(self.text())))
    
    def _on_return_pressed(self) -> None:
        """Parse and execute the command."""
        text = self.text().strip()
        if len(text) <= 1:  # Only ":" or empty
            self.commandCancelled.emit()
            return
        
        # Remove the leading colon and parse
        command = text[1:].strip()
        
        # Parse command: [N]h or [N]l
        # Pattern: optional whitespace, optional number, optional whitespace, h or l, optional whitespace
        pattern = r'^\s*(\d+)?\s*([hl])\s*$'
        match = re.match(pattern, command)
        
        if match:
            count_str, direction = match.groups()
            count = int(count_str) if count_str else 1
            self.commandExecuted.emit(count, direction)
        else:
            # Invalid command, just cancel
            self.commandCancelled.emit()
    
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Handle key presses, especially Escape."""
        if event.key() == Qt.Key_Escape:
            self.commandCancelled.emit()
            event.accept()
            return
        
        # Allow normal text editing
        super().keyPressEvent(event)
    
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Focus the input when shown."""
        super().showEvent(event)
        self.setFocus()
        # Move cursor to end so user types after the colon
        self.setCursorPosition(len(self.text()))
    
    def activate(self) -> None:
        """Activate the command bar."""
        self.setText(":")
        self.show()
        self.setFocus()
        # Move cursor to end so user types after the colon
        self.setCursorPosition(len(self.text()))

