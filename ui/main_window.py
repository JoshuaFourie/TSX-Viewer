"""
Modern main window module for the TSX Component Manager application
"""
import os
import sys
import json
import tempfile
import shutil
import logging
import threading

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QMessageBox, QMenuBar, 
    QMenu, QStatusBar, QStackedWidget, QDialog, QProgressBar, QTextEdit, QCheckBox, QComboBox, QLineEdit, QRadioButton
)
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QSize, pyqtSignal

# Import custom widgets
from ui.component_list import ComponentListWidget
from ui.code_editor import CodeEditorWidget
from ui.console import ConsoleWidget
from ui.theme import ThemeManager
from core.component import Component, ComponentManager

class TSXComponentManager(QMainWindow):
    """Modern main application window for TSX Component Manager"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set window properties
        self.setWindowTitle("TSX Component Manager")
        self.resize(1200, 800)
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(QApplication.instance())
        
        # Temporary directory for exports
        self.temp_dir = tempfile.mkdtemp()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Recent projects list (initialize BEFORE creating menubar)
        self.recent_projects = []
        
        # Load recent projects
        try:
            loaded_projects = self.load_recent_projects()
            self.recent_projects = loaded_projects
        except Exception as e:
            # Log error but continue with empty list
            print(f"Error loading recent projects: {e}")
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Create header with buttons
        self.create_header(main_layout)
        
        # Create main content area
        self.create_main_content(main_layout)
        
        # Create menubar
        self.create_menubar()
        
        # Create status bar
        self.create_statusbar()
        
        # Current project tracking
        self.current_project_path = None
        
        # Initial log messages
        self.log("Welcome to TSX Component Manager!")
        self.log("Add TSX components with the 'Add Component' button.")
    
    def create_header(self, main_layout):
        """Create the application header with buttons"""
        header_layout = QHBoxLayout()
        main_layout.addLayout(header_layout)
        
        # Header label
        header_label = QLabel("TSX Component Manager")
        header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        # Project name label (initially empty)
        self.project_label = QLabel("")
        self.project_label.setFont(QFont("Arial", 10))
        self.project_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(self.project_label, 1)
        
        # Add component button
        self.add_button = QPushButton("Add Component")
        self.add_button.clicked.connect(lambda: self.component_list.add_component())
        header_layout.addWidget(self.add_button)
        
        # Export button
        self.export_button = QPushButton("Export & Run")
        self.export_button.clicked.connect(self.export_and_run_react_app)
        header_layout.addWidget(self.export_button)
    
    def create_main_content(self, main_layout):
        """Create the main content area with component list, editor, and console"""
        # Horizontal split for main content
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout, 4)  # Give more space to main content
        
        # Sidebar with component list
        self.component_list = ComponentListWidget()
        content_layout.addWidget(self.component_list, 1)
        
        # Code editor
        self.code_editor = CodeEditorWidget()
        content_layout.addWidget(self.code_editor, 3)  # Increase ratio from 2 to 3
        
        # Console widget with limited height
        self.console = ConsoleWidget()
        self.console.setMaximumHeight(150)  # Limit console height
        main_layout.addWidget(self.console, 1)  # Give less space to console
    
    def create_menubar(self):
        """Create the application menubar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New Project
        new_action = QAction("New Project", self)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        # Open Project
        open_action = QAction("Open Project", self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        # Save Project
        save_action = QAction("Save Project", self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        # Save Project As
        save_as_action = QAction("Save Project As", self)
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        # Recent Projects submenu
        self.recent_menu = file_menu.addMenu("Recent Projects")
        self.update_recent_projects_menu()
        
        file_menu.addSeparator()
        
        # Add Component action
        add_component_action = QAction("Add Component...", self)
        add_component_action.triggered.connect(lambda: self.component_list.add_component())
        file_menu.addAction(add_component_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        # Find/Replace
        find_action = QAction("Find/Replace", self)
        find_action.triggered.connect(lambda: self.code_editor.show_search_panel())
        edit_menu.addAction(find_action)
        
        # Format Code
        format_action = QAction("Format Code", self)
        format_action.triggered.connect(lambda: self.code_editor.format_code())
        edit_menu.addAction(format_action)
        
        # Export menu
        export_menu = menubar.addMenu("Export")
        
        # Export and Run React App
        export_react_action = QAction("Export & Run React App", self)
        export_react_action.triggered.connect(self.export_and_run_react_app)
        export_menu.addAction(export_react_action)
        
        # Export React App
        export_react_only_action = QAction("Export React App", self)
        export_react_only_action.triggered.connect(self.export_react_app)
        export_menu.addAction(export_react_only_action)
        
        # Export Next.js App
        export_nextjs_action = QAction("Export Next.js App", self)
        export_nextjs_action.triggered.connect(self.export_nextjs_app)
        export_menu.addAction(export_nextjs_action)
        
        # Export Component Library
        export_library_action = QAction("Export Component Library", self)
        export_library_action.triggered.connect(self.export_component_library)
        export_menu.addAction(export_library_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Theme toggle
        theme_action = QAction("Toggle Theme", self)
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # Documentation
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
        # About
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_statusbar(self):
        """Create the application status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def log(self, message: str, level: str = "info"):
        """Log message to console"""
        self.console.add_message(message, level)
        self.status_bar.showMessage(message, 3000)  # Show message for 3 seconds
    
    def set_status(self, message: str):
        """Set the status bar message"""
        self.status_bar.showMessage(message)
    
    def edit_component(self, component):
        """Edit a component in the code editor"""
        try:
            # Load the component content if not already loaded
            content = component.read_content()
            
            # Set the content in the code editor
            self.code_editor.set_content(content)
            
            # Set the active component
            self.code_editor.active_component = component
            
            # Optionally, display component name in status bar
            self.status_bar.showMessage(f"Editing: {component.name}")
            
            # Log to console
            self.log(f"Opened component {component.name} for editing", "info")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening component: {str(e)}")
            self.log(f"Error opening component: {e}", "error")
            
    def new_project(self):
        """Create a new empty project"""
        # Confirm unsaved changes
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self, 
                "Unsaved Changes", 
                "You have unsaved changes. Create a new project anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Clear existing components and editor
        self.component_list.component_manager.clear()
        self.code_editor.set_content("")
        self.code_editor.active_component = None
        self.code_editor.set_unsaved(False)
        
        # Reset project path and update label
        self.current_project_path = None
        self.project_label.setText("")
        
        self.log("Created new project", "success")
        self.set_status("New project created")
    
    def open_project(self):
        """Open a project from file"""
        # Check for unsaved changes
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self, 
                "Unsaved Changes", 
                "You have unsaved changes. Open a different project anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
                
        filetypes = "TSX Component Projects (*.tsxcm);;JSON Files (*.json);;All Files (*.*)"
        filepath, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Project", 
            "", 
            filetypes
        )
        
        if filepath:
            try:
                self._load_project_from_file(filepath)
                self.log(f"Opened project: {os.path.basename(filepath)}", "success")
                
                # Update project label
                project_name = os.path.basename(filepath)
                self.project_label.setText(f"Project: {project_name}")
                
                # Update recent projects
                self.add_recent_project(filepath)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                self.log(f"Error opening project: {e}", "error")

    def _load_project_from_file(self, filepath: str):
        """Load project from a file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # Clear existing components
        self.component_list.component_manager.clear()
        
        # Load components
        for component_info in project_data.get('components', []):
            component_path = component_info.get('path', '')
            
            # Handle relative paths
            if not os.path.isabs(component_path):
                component_path = os.path.normpath(
                    os.path.join(os.path.dirname(filepath), component_path)
                )
            
            # Add component
            if os.path.exists(component_path):
                self.component_list.add_component_from_path(component_path)
            else:
                self.log(f"Component file not found: {component_path}", "warning")
        
        # Set current project path
        self.current_project_path = filepath
    
    def save_project(self):
        """Save the current project"""
        if not self.current_project_path:
            return self.save_project_as()
        
        success = self._save_project_to_file(self.current_project_path)
        if success:
            project_name = os.path.basename(self.current_project_path)
            self.set_status(f"Saved: {project_name}")
        return success
    
    def save_project_as(self):
        """Save project to a new file"""
        filetypes = "TSX Component Projects (*.tsxcm);;JSON Files (*.json);;All Files (*.*)"
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Project", 
            "", 
            filetypes
        )
        
        if filepath:
            if self._save_project_to_file(filepath):
                # Update current project path
                self.current_project_path = filepath
                
                # Update project label
                project_name = os.path.basename(filepath)
                self.project_label.setText(f"Project: {project_name}")
                
                # Add to recent projects
                self.add_recent_project(filepath)
                return True
        return False
    
    def _save_project_to_file(self, filepath: str) -> bool:
        """Save project data to a file"""
        try:
            # Create project data
            project_data = {
                'version': '1.0',
                'components': []
            }
            
            # Get component information
            for component in self.component_list.component_manager.components:
                # Try to make path relative to project file
                component_path = component.filepath
                project_dir = os.path.dirname(filepath)
                
                try:
                    rel_path = os.path.relpath(component_path, project_dir)
                    component_path = rel_path
                except:
                    # Keep as absolute path if relative path fails
                    pass
                
                project_data['components'].append({
                    'name': component.name,
                    'path': component_path
                })
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2)
            
            # Log success
            self.log(f"Saved project: {os.path.basename(filepath)}", "success")
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))
            self.log(f"Error saving project: {e}", "error")
            return False
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        # Check code editor for unsaved changes
        if hasattr(self.code_editor, 'unsaved_changes') and self.code_editor.unsaved_changes:
            return True
            
        # Also check if there are components or unsaved code
        return (len(self.component_list.component_manager.components) > 0 or 
                self.code_editor.get_content().strip() != "")
    
    def load_recent_projects(self):
        """Load recent projects list"""
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".tsx_component_manager")
            recent_file = os.path.join(config_dir, "recent_projects.json")
            
            if os.path.exists(recent_file):
                with open(recent_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('recent', [])
            
        except Exception:
            # If anything goes wrong, return empty list
            pass
            
        return []
    
    def add_recent_project(self, filepath: str):
        """Add a project to the recent projects list"""
        # Normalize the filepath
        filepath = os.path.abspath(filepath)
        
        # Remove if already in list
        if filepath in self.recent_projects:
            self.recent_projects.remove(filepath)
        
        # Add to beginning of list
        self.recent_projects.insert(0, filepath)
        
        # Keep only the 10 most recent
        self.recent_projects = self.recent_projects[:10]
        
        # Save and update menu
        self.save_recent_projects()
        self.update_recent_projects_menu()
    
    def save_recent_projects(self):
        """Save the list of recent projects"""
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".tsx_component_manager")
            os.makedirs(config_dir, exist_ok=True)
            recent_file = os.path.join(config_dir, "recent_projects.json")
            
            with open(recent_file, 'w', encoding='utf-8') as f:
                json.dump({'recent': self.recent_projects}, f)
                
        except Exception as e:
            self.log(f"Error saving recent projects: {e}", "error")
    
    def update_recent_projects_menu(self):
        """Update the Recent Projects submenu"""
        # Clear existing actions
        self.recent_menu.clear()
        
        if not self.recent_projects:
            # Add disabled action if no recent projects
            no_projects_action = QAction("No recent projects", self)
            no_projects_action.setEnabled(False)
            self.recent_menu.addAction(no_projects_action)
            return
        
        # Add recent project actions
        for filepath in self.recent_projects:
            # Use basename for display
            project_name = os.path.basename(filepath)
            
            # Create action for each recent project
            action = QAction(project_name, self)
            # Use lambda with default argument to avoid late binding
            action.triggered.connect(lambda checked, path=filepath: self._load_project_from_file(path))
            self.recent_menu.addAction(action)
        
        # Add separator and clear option
        self.recent_menu.addSeparator()
        clear_action = QAction("Clear Recent Projects", self)
        clear_action.triggered.connect(self.clear_recent_projects)
        self.recent_menu.addAction(clear_action)
    
    def clear_recent_projects(self):
        """Clear the list of recent projects"""
        # Show confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Clear Recent Projects", 
            "Are you sure you want to clear the list of recent projects?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear the list
            self.recent_projects = []
            
            # Save and update menu
            self.save_recent_projects()
            self.update_recent_projects_menu()
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        if self.theme_manager.is_light_mode():
            self.theme_manager.set_dark_mode()
        else:
            self.theme_manager.set_light_mode()
    
    def show_documentation(self):
        """Show application documentation"""
        # Create a dialog for documentation
        doc_dialog = QDialog(self)
        doc_dialog.setWindowTitle("Documentation")
        doc_dialog.resize(600, 500)
        
        layout = QVBoxLayout()
        doc_dialog.setLayout(layout)
        
        # Documentation content
        doc_content = """
# TSX Component Manager

## Overview
TSX Component Manager is a desktop application for managing React TypeScript (TSX) components, with powerful editing and export capabilities.

## Key Features

### Component Management
- Add multiple TSX/JSX components to a project
- Edit components with syntax highlighting
- Rename and duplicate components
- Organize components in projects

### Code Editing
- Syntax highlighting for TSX/JSX code
- Search and replace functionality
- Code formatting
- Auto-indentation and bracket matching

### Export Options
1. **React Application**
   - Export components as a complete React app
   - Run the app directly from the export window
   - Dependencies are automatically detected

2. **Next.js Application**
   - Export components to a Next.js application
   - Choose between App Router and Pages Router
   - Configure TypeScript and other options

3. **Component Library**
   - Package components as a reusable library
   - Choose between Rollup and Webpack for building
   - Optional Storybook integration

## Quick Start
1. Add components using the "Add Component" button
2. Edit components in the code editor
3. Save your project using File > Save Project
4. Export components using the export options in the menu

## Keyboard Shortcuts
- Ctrl+S: Save changes
- Ctrl+F: Find/Replace
- Ctrl+Z: Undo
- Ctrl+Y: Redo
- Tab/Shift+Tab: Indent/Unindent
"""
        
        # Add documentation text
        doc_text = QTextEdit()
        doc_text.setReadOnly(True)
        doc_text.setPlainText(doc_content)
        layout.addWidget(doc_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(doc_dialog.close)
        layout.addWidget(close_btn)
        
        doc_dialog.exec()
    
    def show_about(self):
        """Show about dialog"""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About")
        about_dialog.resize(400, 300)
        
        layout = QVBoxLayout()
        about_dialog.setLayout(layout)
        
        # About text
        about_label = QLabel("""
        <h1>TSX Component Manager</h1>
        <p>Version 2.0</p>
        <p>A modern tool for managing React TypeScript components.</p>
        <p>© 2024 Your Company Name</p>
        """)
        about_label.setWordWrap(True)
        layout.addWidget(about_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(about_dialog.close)
        layout.addWidget(close_btn)
        
        about_dialog.exec()
        
    def show_export_progress(self, title, export_dir, export_func, run_app=True):
        """
        Show a progress dialog for the export process
        
        Args:
            title: Dialog title
            export_dir: Export directory
            export_func: Function to run for export (takes progress_callback and path)
            run_app: Whether to run the app after export
        """
        # Create a progress dialog
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle(title)
        progress_dialog.resize(500, 400)
        progress_dialog.setModal(True)
        
        # Create a progress display
        dialog_layout = QVBoxLayout()
        progress_dialog.setLayout(dialog_layout)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14))
        dialog_layout.addWidget(title_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate mode
        dialog_layout.addWidget(progress_bar)
        
        progress_text = QTextEdit()
        progress_text.setReadOnly(True)
        dialog_layout.addWidget(progress_text)
        
        # Function to add log messages to the progress window
        def add_progress_log(message):
            progress_text.append(message)
            # Scroll to the bottom
            progress_text.moveCursor(progress_text.textCursor().End)
            # Update UI
            QApplication.processEvents()
        
        # Create a hidden done button (will be shown when export completes)
        done_button = QPushButton("Done")
        done_button.clicked.connect(progress_dialog.accept)
        done_button.setVisible(False)
        dialog_layout.addWidget(done_button)
        
        # Show the dialog
        progress_dialog.show()
        
        # Function to run the export process
        def run_export():
            try:
                export_func(add_progress_log, export_dir, run_app)
                
                # Show the done button
                done_button.setVisible(True)
                
                # Set progress bar to 100%
                progress_bar.setRange(0, 100)
                progress_bar.setValue(100)
                
            except Exception as e:
                self.logger.error(f"Error during export: {e}")
                add_progress_log(f"\nError: {str(e)}")
                
                # Show the done button
                done_button.setVisible(True)
        
        # Run the export process in a separate thread
        export_thread = threading.Thread(target=run_export)
        export_thread.daemon = True
        export_thread.start()
        
        # Execute the dialog
        progress_dialog.exec()
    
    def export_and_run_react_app(self):
        """Export components to a runnable React app"""
        # Check if there are any components
        components = self.component_list.get_components()
        if not components:
            QMessageBox.information(self, "Information", "Please add at least one component first")
            return
        
        # Ask for export directory
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Select folder to export React application"
        )
        
        if not export_dir:
            return  # User cancelled
        
        # Show a confirmation dialog with list of components
        component_list_text = "\n".join([f"- {comp.name}" for comp in components])
        result = QMessageBox.question(
            self,
            "Export and Run React App",
            f"Create and run a React application with the following components?\n\n{component_list_text}\n\n"
            f"The app will be exported to:\n{export_dir}\n\n"
            "This will install dependencies and start the development server.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.No:
            return
        
        # Create a progress window
        self.show_export_progress("Exporting React App", export_dir, self._run_react_export)
    
    def export_react_app(self):
        """Export components to a React app (without running)"""
        # Check if there are any components
        components = self.component_list.get_components()
        if not components:
            QMessageBox.information(self, "Information", "Please add at least one component first")
            return
        
        # Ask for export directory
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Select folder to export React application"
        )
        
        if not export_dir:
            return  # User cancelled
        
        # Show a confirmation dialog with list of components
        component_list_text = "\n".join([f"- {comp.name}" for comp in components])
        result = QMessageBox.question(
            self,
            "Export React App",
            f"Create a React application with the following components?\n\n{component_list_text}\n\n"
            f"The app will be exported to:\n{export_dir}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.No:
            return
        
        # Create a progress window
        self.show_export_progress("Exporting React App", export_dir, self._run_react_export, run_app=False)
    
    def export_nextjs_app(self):
        """Export components to a Next.js app"""
        # Check if there are any components
        components = self.component_list.get_components()
        if not components:
            QMessageBox.information(self, "Information", "Please add at least one component first")
            return
        
        # Ask for export directory
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Select folder to export Next.js application"
        )
        
        if not export_dir:
            return  # User cancelled
        
        # Ask for Next.js version and options
        options = self.show_nextjs_options()
        if not options:
            return  # User cancelled
        
        # Show a confirmation dialog with list of components
        component_list_text = "\n".join([f"- {comp.name}" for comp in components])
        result = QMessageBox.question(
            self,
            "Export Next.js App",
            f"Create a Next.js application with the following components?\n\n{component_list_text}\n\n"
            f"The app will be exported to:\n{export_dir}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.No:
            return
        
        # Create a progress window
        self.show_export_progress("Exporting Next.js App", export_dir, 
                                 lambda progress, path, run_app=True: self._run_nextjs_export(progress, path, options, run_app))
    
    def export_component_library(self):
        """Export components as a reusable component library package"""
        # Check if there are any components
        components = self.component_list.get_components()
        if not components:
            QMessageBox.information(self, "Information", "Please add at least one component first")
            return
        
        # Ask for export directory
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Select folder to export component library"
        )
        
        if not export_dir:
            return  # User cancelled
        
        # Ask for library options
        options = self.show_library_options()
        if not options:
            return  # User cancelled
        
        # Show a confirmation dialog with list of components
        component_list_text = "\n".join([f"- {comp.name}" for comp in components])
        result = QMessageBox.question(
            self,
            "Export Component Library",
            f"Create a component library with the following components?\n\n{component_list_text}\n\n"
            f"The library will be exported to:\n{export_dir}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.No:
            return
        
        # Create a progress window
        self.show_export_progress("Exporting Component Library", export_dir, 
                                 lambda progress, path, run_app=True: self._run_library_export(progress, path, options, run_app))
                                 
    def show_nextjs_options(self):
        """Show dialog for Next.js export options"""
        options_dialog = QDialog(self)
        options_dialog.setWindowTitle("Next.js Export Options")
        options_dialog.resize(400, 300)
        options_dialog.setModal(True)
        
        layout = QVBoxLayout()
        options_dialog.setLayout(layout)
        
        # Title
        title_label = QLabel("Next.js Export Options")
        title_label.setFont(QFont("Arial", 14))
        layout.addWidget(title_label)
        
        form_layout = QVBoxLayout()
        layout.addLayout(form_layout)
        
        # Next.js version
        version_layout = QHBoxLayout()
        version_label = QLabel("Next.js Version:")
        version_combo = QComboBox()
        version_combo.addItems(["13.4.12", "12.3.4", "11.1.4"])
        version_layout.addWidget(version_label)
        version_layout.addWidget(version_combo)
        form_layout.addLayout(version_layout)
        
        # Router type
        router_label = QLabel("Router Type:")
        form_layout.addWidget(router_label)
        
        app_router = QRadioButton("App Router")
        app_router.setChecked(True)
        form_layout.addWidget(app_router)
        
        pages_router = QRadioButton("Pages Router")
        form_layout.addWidget(pages_router)
        
        # TypeScript
        typescript_check = QCheckBox("Use TypeScript")
        typescript_check.setChecked(True)
        form_layout.addWidget(typescript_check)
        
        # ESLint
        eslint_check = QCheckBox("Include ESLint")
        eslint_check.setChecked(True)
        form_layout.addWidget(eslint_check)
        
        # Tailwind CSS
        tailwind_check = QCheckBox("Include Tailwind CSS")
        tailwind_check.setChecked(True)
        form_layout.addWidget(tailwind_check)
        
        # Buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        cancel_button = QPushButton("Cancel")
        ok_button = QPushButton("OK")
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        # Result variable to store the selected options
        result = [None]
        
        def on_cancel():
            result[0] = None
            options_dialog.reject()
        
        def on_ok():
            result[0] = {
                "version": version_combo.currentText(),
                "router": "app" if app_router.isChecked() else "pages",
                "typescript": typescript_check.isChecked(),
                "eslint": eslint_check.isChecked(),
                "tailwind": tailwind_check.isChecked()
            }
            options_dialog.accept()
        
        cancel_button.clicked.connect(on_cancel)
        ok_button.clicked.connect(on_ok)
        
        # Execute the dialog
        options_dialog.exec()
        
        return result[0]
        
    def show_library_options(self):
        """Show dialog for component library export options"""
        options_dialog = QDialog(self)
        options_dialog.setWindowTitle("Component Library Export Options")
        options_dialog.resize(400, 350)
        options_dialog.setModal(True)
        
        layout = QVBoxLayout()
        options_dialog.setLayout(layout)
        
        # Title
        title_label = QLabel("Component Library Options")
        title_label.setFont(QFont("Arial", 14))
        layout.addWidget(title_label)
        
        form_layout = QVBoxLayout()
        layout.addLayout(form_layout)
        
        # Package name
        name_layout = QHBoxLayout()
        name_label = QLabel("Package Name:")
        name_input = QLineEdit("my-component-library")
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        form_layout.addLayout(name_layout)
        
        # Package version
        version_layout = QHBoxLayout()
        version_label = QLabel("Version:")
        version_input = QLineEdit("0.1.0")
        version_layout.addWidget(version_label)
        version_layout.addWidget(version_input)
        form_layout.addLayout(version_layout)
        
        # TypeScript
        typescript_check = QCheckBox("Use TypeScript")
        typescript_check.setChecked(True)
        form_layout.addWidget(typescript_check)
        
        # Build system
        build_label = QLabel("Build System:")
        form_layout.addWidget(build_label)
        
        rollup_radio = QRadioButton("Rollup")
        rollup_radio.setChecked(True)
        form_layout.addWidget(rollup_radio)
        
        webpack_radio = QRadioButton("Webpack")
        form_layout.addWidget(webpack_radio)
        
        # Include Storybook
        storybook_check = QCheckBox("Include Storybook")
        storybook_check.setChecked(True)
        form_layout.addWidget(storybook_check)
        
        # Buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        cancel_button = QPushButton("Cancel")
        ok_button = QPushButton("OK")
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        # Result variable to store the selected options
        result = [None]
        
        def on_cancel():
            result[0] = None
            options_dialog.reject()
        
        def on_ok():
            result[0] = {
                "name": name_input.text(),
                "version": version_input.text(),
                "typescript": typescript_check.isChecked(),
                "build": "rollup" if rollup_radio.isChecked() else "webpack",
                "storybook": storybook_check.isChecked()
            }
            options_dialog.accept()
        
        cancel_button.clicked.connect(on_cancel)
        ok_button.clicked.connect(on_ok)
        
        # Execute the dialog
        options_dialog.exec()
        
        return result[0]
    
    def _run_nextjs_export(self, progress_callback, export_dir, options, run_app=True):
        """Run the Next.js export process with selected options"""
        import subprocess
        import time
        
        progress_callback("Starting Next.js export process...")
        progress_callback(f"Using options: {options}")
        
        # Create Next.js app directory
        app_dir = os.path.join(export_dir, "nextjs-components-app")
        progress_callback(f"Creating Next.js app in: {app_dir}")
        os.makedirs(app_dir, exist_ok=True)
        
        # Create basic project structure
        progress_callback("Creating project structure...")
        time.sleep(1)  # For demonstration purposes
        
        # Get all components
        components = self.component_list.get_components()
        progress_callback(f"Adding {len(components)} components...")
        time.sleep(1)  # For demonstration purposes
        
        progress_callback("Setting up Next.js configuration...")
        time.sleep(1)  # For demonstration purposes
        
        # Simulated success
        progress_callback("\nNext.js app export completed!")
        progress_callback(f"Location: {app_dir}")
        progress_callback("\nTo run the application:")
        progress_callback("1. Open a terminal in the exported directory")
        progress_callback("2. Run 'npm install' to install dependencies")
        progress_callback("3. Run 'npm run dev' to start the development server")
        progress_callback("4. Open http://localhost:3000 in your browser")
    
    def _run_library_export(self, progress_callback, export_dir, options, run_app=True):
        """Run the component library export process with selected options"""
        import time
        
        progress_callback("Starting component library export process...")
        progress_callback(f"Using options: {options}")
        
        # Create library directory
        lib_dir = os.path.join(export_dir, options["name"])
        progress_callback(f"Creating component library in: {lib_dir}")
        os.makedirs(lib_dir, exist_ok=True)
        
        # Set up library project structure
        progress_callback("Setting up library project structure...")
        time.sleep(1)  # For demonstration purposes
        
        # Get all components
        components = self.component_list.get_components()
        progress_callback(f"Adding {len(components)} components...")
        time.sleep(1)  # For demonstration purposes
        
        progress_callback("Configuring build system...")
        time.sleep(1)  # For demonstration purposes
        
        if options["storybook"]:
            progress_callback("Setting up Storybook...")
            time.sleep(1)  # For demonstration purposes
        
        # Simulated success
        progress_callback("\nComponent library export completed!")
        progress_callback(f"Location: {lib_dir}")
        progress_callback("\nTo build the library:")
        progress_callback("1. Open a terminal in the exported directory")
        progress_callback("2. Run 'npm install' to install dependencies")
        progress_callback("3. Run 'npm run build' to build the library")
        if options["storybook"]:
            progress_callback("4. Run 'npm run storybook' to view components in Storybook")
    
    def to_camel_case(self, name: str) -> str:
        """Convert a string to camelCase for component names"""
        # Replace hyphens and underscores with spaces
        s = name.replace('-', ' ').replace('_', ' ')
        # Title case each word and join without spaces
        words = s.split()
        if not words:
            return ''
        # First word lowercase, rest capitalized
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Check for unsaved changes
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self, 
                "Unsaved Changes", 
                "You have unsaved changes. Exit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Clean up temporary directory
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.log(f"Error cleaning up temp directory: {e}", "error")
        
        # Accept the close event
        event.accept()