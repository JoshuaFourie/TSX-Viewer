"""
Modern console module with collapsible panel
"""
import sys
import datetime
from typing import Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLabel, QPushButton, QFrame, QApplication, QMainWindow
)
from PyQt6.QtGui import QTextCursor, QColor, QFont
from PyQt6.QtCore import Qt

class ConsoleWidget(QWidget):
    """Modern console widget with advanced logging capabilities"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure message styles
        self.message_styles: Dict[str, Dict[str, Any]] = {
            "info": {"color": "#4B5563", "font_weight": QFont.Weight.Normal},
            "success": {"color": "#10B981", "font_weight": QFont.Weight.Bold},
            "warning": {"color": "#F59E0B", "font_weight": QFont.Weight.Bold},
            "error": {"color": "#EF4444", "font_weight": QFont.Weight.Bold}
        }
        
        # Maximum number of log messages
        self.max_messages = 1000
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header with controls
        header = QFrame()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)
        
        # Title label
        self.title_label = QLabel("Console")
        header_layout.addWidget(self.title_label)
        
        # Message count
        self.message_count_label = QLabel("0")
        header_layout.addWidget(self.message_count_label)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_messages)
        header_layout.addWidget(clear_btn)
        
        layout.addWidget(header)
        
        # Console text area
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        layout.addWidget(self.console_text)
        
        # Initialize message list
        self.messages = []
    
    def add_message(self, message: str, level: str = "info"):
        """
        Add a message to the console
        
        Args:
            message: The message text to add
            level: Message level (info, success, warning, error)
        """
        # Default to info level if invalid
        if level not in self.message_styles:
            level = "info"
        
        # Create timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        
        # Add to messages list
        self.messages.append({
            "message": full_message,
            "level": level
        })
        
        # Limit number of messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        
        # Update message count
        self.message_count_label.setText(str(len(self.messages)))
        
        # Update console text
        self._update_console_text()
    
    def _update_console_text(self):
        """Update the console text widget with all messages"""
        # Clear existing text
        self.console_text.clear()
        
        # Add all messages with styling
        for msg in self.messages:
            style = self.message_styles.get(msg['level'], self.message_styles['info'])
            
            # Set text color and format
            color = QColor(style['color'])
            cursor = self.console_text.textCursor()
            format = cursor.charFormat()
            format.setForeground(color)
            format.setFontWeight(style['font_weight'])
            
            cursor.mergeCharFormat(format)
            cursor.insertText(msg['message'] + "\n")
    
    def clear_messages(self):
        """Clear all console messages"""
        self.messages.clear()
        self.console_text.clear()
        self.message_count_label.setText("0")
        
        # Add a system message about clearing
        self.add_message("Console cleared", "info")

# Standalone application for testing
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Console Widget")
        
        # Create central widget and console
        central_widget = ConsoleWidget()
        self.setCentralWidget(central_widget)
        
        # Add some test messages
        central_widget.add_message("Application started", "info")
        central_widget.add_message("Important operation successful", "success")
        central_widget.add_message("Warning: Potential issue detected", "warning")
        central_widget.add_message("Critical error occurred", "error")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec())