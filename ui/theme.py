"""
Theme management module for the PyQt6 application
"""
import os
import json
import sys
from typing import Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, 
    QLabel, QFrame, QStyle, QVBoxLayout
)
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt

class ModernTheme:
    """Modern theme constants and color palettes"""
    
    # Light theme color palette
    LIGHT: Dict[str, str] = {
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F5F7FA",
        "bg_tertiary": "#E6ECF5",
        "fg_primary": "#1F2937",
        "fg_secondary": "#4B5563",
        "fg_tertiary": "#9CA3AF",
        "accent": "#3459DB",
        "accent_hover": "#2C4CBF",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "border": "#E5E7EB",
        "input_bg": "#FFFFFF",
        "code_bg": "#F3F4F6",
        "code_fg": "#1F2937"
    }
    
    # Dark theme color palette
    DARK: Dict[str, str] = {
        "bg_primary": "#1F2937",
        "bg_secondary": "#111827",
        "bg_tertiary": "#0A101F",
        "fg_primary": "#F9FAFB",
        "fg_secondary": "#E5E7EB",
        "fg_tertiary": "#9CA3AF",
        "accent": "#4F6AE5",
        "accent_hover": "#5D76F0",
        "success": "#34D399",
        "warning": "#FBBF24",
        "error": "#F87171",
        "border": "#374151",
        "input_bg": "#2C3441",
        "code_bg": "#1A202C",
        "code_fg": "#E5E7EB"
    }

class ThemeManager:
    """Manages application theme and styling"""
    
    def __init__(self, app: QApplication):
        """Initialize theme manager"""
        self.app = app
        self.theme_mode = "light"  # Default theme
        
        # Load saved theme preference
        self.load_theme_preference()
        
        # Apply initial theme
        self.apply_theme()
    
    def apply_theme(self):
        """Apply the current theme to the entire application"""
        colors = ModernTheme.LIGHT if self.is_light_mode() else ModernTheme.DARK
        
        # Global stylesheet
        stylesheet = f"""
        QWidget {{
            background-color: {colors['bg_primary']};
            color: {colors['fg_primary']};
            font-family: Arial, sans-serif;
        }}
        
        QPushButton {{
            background-color: {colors['accent']};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
        }}
        
        QLabel {{
            color: {colors['fg_primary']};
        }}
        
        QFrame {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
        }}
        
        QTextEdit, QLineEdit {{
            background-color: {colors['input_bg']};
            color: {colors['fg_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
        }}
        """
        
        # Apply stylesheet
        self.app.setStyleSheet(stylesheet)
    
    def is_light_mode(self) -> bool:
        """Check if light mode is active"""
        return self.theme_mode == "light"
    
    def set_light_mode(self):
        """Switch to light mode"""
        if not self.is_light_mode():
            self.theme_mode = "light"
            self.apply_theme()
            self.save_theme_preference()
    
    def set_dark_mode(self):
        """Switch to dark mode"""
        if self.is_light_mode():
            self.theme_mode = "dark"
            self.apply_theme()
            self.save_theme_preference()
    
    def load_theme_preference(self):
        """Load saved theme preference"""
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".tsx_component_manager")
            theme_file = os.path.join(config_dir, "theme_preference.json")
            
            if os.path.exists(theme_file):
                with open(theme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.theme_mode = data.get('theme', 'light')
        except Exception as e:
            print(f"Error loading theme preference: {e}")
            # Use default theme (light)
    
    def save_theme_preference(self):
        """Save current theme preference"""
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".tsx_component_manager")
            os.makedirs(config_dir, exist_ok=True)
            theme_file = os.path.join(config_dir, "theme_preference.json")
            
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump({'theme': self.theme_mode}, f)
                
        except Exception as e:
            print(f"Error saving theme preference: {e}")

# Example usage
if __name__ == '__main__':
    app = QApplication(sys.argv)
    theme_manager = ThemeManager(app)
    
    # Create a sample window to demonstrate theme
    window = QWidget()
    layout = QVBoxLayout()
    
    label = QLabel("Theme Demo")
    layout.addWidget(label)
    
    btn_light = QPushButton("Light Mode")
    btn_light.clicked.connect(theme_manager.set_light_mode)
    layout.addWidget(btn_light)
    
    btn_dark = QPushButton("Dark Mode")
    btn_dark.clicked.connect(theme_manager.set_dark_mode)
    layout.addWidget(btn_dark)
    
    window.setLayout(layout)
    window.show()
    
    sys.exit(app.exec())