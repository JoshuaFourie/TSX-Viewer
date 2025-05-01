#!/usr/bin/env python3
"""
TSX Component Manager - A tool for managing and exporting React TSX components
"""
import os
import subprocess
import sys
import tkinter as tk
import logging
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
        import tkinter.font as tkfont
        import tkinter.scrolledtext as scrolledtext
        import tkinter.ttk as ttk
        import json
        import subprocess
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False

def main():
    """Main entry point for the application"""
    logger = setup_logging()
    logger.info("Starting TSX Component Manager")
    
    # Check dependencies
    if not check_dependencies():
        print("Please install required dependencies")
        sys.exit(1)
    
    # Check for Node.js
    try:
        is_windows = os.name == 'nt'
        node_cmd = "node --version" if is_windows else ["node", "--version"]
        npm_cmd = "npm --version" if is_windows else ["npm", "--version"]
        
        node_version = subprocess.check_output(node_cmd, shell=is_windows).decode().strip()
        npm_version = subprocess.check_output(npm_cmd, shell=is_windows).decode().strip()
        
        logger.info(f"Node.js version: {node_version}")
        logger.info(f"npm version: {npm_version}")
    except Exception as e:
        logger.error(f"Error detecting Node.js and npm: {str(e)}")
        print("Error: Node.js and npm are required to run this application.")
        print("Please install Node.js from https://nodejs.org/")
        sys.exit(1)
    
    # Start the application
    root = tk.Tk()
    root.title("TSX Component Manager")
    
    # Set icon if available
    try:
        if is_windows:
            root.iconbitmap("resources/icon.ico")
        else:
            # For Linux/Mac
            icon = tk.PhotoImage(file="resources/icon.png")
            root.iconphoto(True, icon)
    except Exception:
        # Icon not found, continue without it
        pass
    
    app = TSXComponentManager(root)
    
    # Center the window
    window_width = 1200
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Start the main loop
    root.mainloop()
    
    logger.info("Application exited")

if __name__ == "__main__":
    main()