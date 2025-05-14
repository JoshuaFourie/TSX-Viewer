#!/usr/bin/env python3
"""
TSX Component Manager - A tool for managing and exporting React TSX components
"""
import os
import subprocess
import sys
import logging

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

# Import the PyQt6 version of main window
from ui.main_window import TSXComponentManager

def setup_logging():
    """Set up logging for the application"""
    log_dir = os.path.join(os.path.expanduser("~"), ".tsx_component_manager")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "app.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("TSXComponentManager")
    return logger

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        # Check PyQt6 dependencies
        import PyQt6
        
        # Check for Pillow (optional)
        try:
            from PIL import Image
            print("Pillow is installed")
        except ImportError:
            print("Warning: Pillow is not installed. Some UI features might not work properly.")
            print("Install it using: pip install pillow")
        
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install PyQt6 using: pip install PyQt6")
        return False

def check_node_dependencies():
    """Check Node.js and npm dependencies"""
    try:
        is_windows = os.name == 'nt'
        node_cmd = "node --version" if is_windows else ["node", "--version"]
        npm_cmd = "npm --version" if is_windows else ["npm", "--version"]
        
        node_version = subprocess.check_output(node_cmd, shell=is_windows).decode().strip()
        npm_version = subprocess.check_output(npm_cmd, shell=is_windows).decode().strip()
        
        return node_version, npm_version
    except Exception as e:
        return None, None

def main():
    """Main entry point for the application"""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting TSX Component Manager")
    
    # Check PyQt6 dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Node.js dependencies
    node_version, npm_version = check_node_dependencies()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create main window
    window = TSXComponentManager()
    
    # Set window icon
    try:
        icon_path = "resources/icon.png"
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            window.setWindowIcon(app_icon)
    except Exception as e:
        logger.warning(f"Could not set application icon: {e}")
    
    # Check Node.js dependencies and show warning if not found
    if not (node_version and npm_version):
        QMessageBox.warning(
            window, 
            "Dependencies Missing", 
            "Node.js and/or npm not found. Some export features will be disabled.\n\n"
            "Please install Node.js from https://nodejs.org/",
            QMessageBox.Ok
        )
    else:
        logger.info(f"Node.js version: {node_version}")
        logger.info(f"npm version: {npm_version}")
    
    # Show the window
    window.show()
    
    # Center the window
    frame_geometry = window.frameGeometry()
    screen_center = app.primaryScreen().availableGeometry().center()
    frame_geometry.moveCenter(screen_center)
    window.move(frame_geometry.topLeft())
    
    # Start the event loop
    exit_code = app.exec()
    
    logger.info("Application exited")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()