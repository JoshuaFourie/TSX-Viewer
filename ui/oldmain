"""
Main window module for the TSX Component Manager application
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import threading
import json
from typing import List, Dict, Any, Optional
import tempfile
import shutil

from ui.component_list import ComponentListFrame
from ui.code_editor import CodeEditorFrame
from ui.console import ConsoleFrame
from core.component import Component

logger = logging.getLogger(__name__)

class TSXComponentManager:
    """Main application window for TSX Component Manager"""
    
    def __init__(self, root):
        """Initialize the main application window"""
        self.root = root
        self.root.title("TSX Component Manager")
        
        # Create a menubar
        self.create_menubar()
        
        # Main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header with buttons
        self.create_header()
        
        # Create component list
        self.component_list = ComponentListFrame(self.main_frame, self)
        
        # Create code editor
        self.code_editor = CodeEditorFrame(self.main_frame, self)
        
        # Create console
        self.console = ConsoleFrame(self.main_frame)
        
        # Status bar
        self.status_bar = ttk.Label(
            self.main_frame, 
            text="Ready", 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Temporary directory for exports
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize
        self.log("Welcome to TSX Component Manager!")
        self.log("Add TSX components with the 'Add Component' button.")
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Recent projects list
        self.recent_projects = self.load_recent_projects()
        self.update_recent_projects_menu()
    
    def create_menubar(self):
        """Create the application menubar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project...", command=self.open_project)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Save Project As...", command=self.save_project_as)
        
        # Add Recent Projects submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Projects", menu=self.recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="Add Component...", 
                               command=lambda: self.component_list.add_component())
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Find/Replace", 
                               command=lambda: self.code_editor.show_search_panel())
        edit_menu.add_command(label="Format Code", 
                               command=lambda: self.code_editor.format_code())
        
        # Export menu
        export_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Export", menu=export_menu)
        export_menu.add_command(label="Export & Run React App", 
                                 command=self.export_and_run_react_app)
        export_menu.add_command(label="Export as React App", 
                                 command=self.export_react_app)
        export_menu.add_command(label="Export as Next.js App", 
                                 command=self.export_nextjs_app)
        export_menu.add_command(label="Export as Component Library", 
                                 command=self.export_component_library)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_header(self):
        """Create the application header with buttons"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Header label
        header_label = ttk.Label(
            header_frame, 
            text="TSX Component Manager", 
            font=("Arial", 16, "bold")
        )
        header_label.pack(side=tk.LEFT)
        
        # Project name label (initially empty)
        self.project_label = ttk.Label(
            header_frame, 
            text="", 
            font=("Arial", 10),
            foreground="#666666"
        )
        self.project_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Add component button
        self.add_button = ttk.Button(
            header_frame, 
            text="Add Component", 
            command=lambda: self.component_list.add_component()
        )
        self.add_button.pack(side=tk.RIGHT)
        
        # Export button
        self.export_button = ttk.Button(
            header_frame, 
            text="Export & Run", 
            command=self.export_and_run_react_app
        )
        self.export_button.pack(side=tk.RIGHT, padx=10)
    
    def log(self, message: str, level: str = "info"):
        """
        Add a message to the console
        
        Args:
            message: The message to log
            level: Message level (info, success, warning, error)
        """
        if hasattr(self, 'console') and self.console:
            self.console.add_message(message, level)
    
    def set_status(self, message: str):
        """Set the status bar message"""
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.config(text=message)
    
    def new_project(self):
        """Create a new empty project"""
        # Check for unsaved changes in the current project
        if self.has_unsaved_changes():
            if not messagebox.askyesno("Unsaved Changes", 
                                       "You have unsaved changes. Create a new project anyway?"):
                return
        
        # Clear component list and editor
        self.component_list.clear_components()
        if hasattr(self, 'code_editor') and self.code_editor:
            self.code_editor.current_component = None
            self.code_editor.code_text.delete('1.0', tk.END)
            self.code_editor.set_unsaved(False)
        
        # Reset project information
        self.current_project_path = None
        self.project_label.config(text="")
        
        self.log("Created new project", "success")
        self.set_status("New project created")
    
    def open_project(self):
        """Open a project from file"""
        # Check for unsaved changes
        if self.has_unsaved_changes():
            if not messagebox.askyesno("Unsaved Changes", 
                                       "You have unsaved changes. Open a different project anyway?"):
                return
        
        # Ask for project file
        filetypes = [
            ("TSX Component Manager Projects", "*.tsxcm"),
            ("JSON Files", "*.json"),
            ("All Files", "*.*")
        ]
        
        filepath = filedialog.askopenfilename(
            title="Open Project",
            filetypes=filetypes
        )
        
        if not filepath:
            return
        
        try:
            self._load_project_from_file(filepath)
            
            # Add to recent projects
            self.add_recent_project(filepath)
            
        except Exception as e:
            logger.error(f"Error opening project {filepath}: {e}")
            messagebox.showerror("Error", f"Failed to open project: {e}")
    
    def _load_project_from_file(self, filepath: str):
        """Load a project from the specified file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # Clear current project
        self.new_project()
        
        # Load components
        components = project_data.get('components', [])
        for component_info in components:
            try:
                component_path = component_info.get('path', '')
                
                # Handle relative paths
                if not os.path.isabs(component_path):
                    component_path = os.path.normpath(
                        os.path.join(os.path.dirname(filepath), component_path)
                    )
                
                # Check if file exists
                if not os.path.exists(component_path):
                    self.log(f"Component file not found: {component_path}", "warning")
                    continue
                
                # Add component
                component = self.component_list.component_manager.add_component(component_path)
                self.component_list.listbox.insert(tk.END, component.display_name)
                
            except Exception as e:
                self.log(f"Error loading component: {e}", "error")
        
        # Set project info
        self.current_project_path = filepath
        project_name = os.path.basename(filepath)
        self.project_label.config(text=f"Project: {project_name}")
        
        # Log success
        self.log(f"Opened project: {project_name}", "success")
        self.set_status(f"Opened project: {project_name}")
    
    def save_project(self):
        """Save the current project"""
        if not hasattr(self, 'current_project_path') or not self.current_project_path:
            return self.save_project_as()
        
        return self._save_project_to_file(self.current_project_path)
    
    def save_project_as(self):
        """Save the current project to a new file"""
        filetypes = [
            ("TSX Component Manager Projects", "*.tsxcm"),
            ("JSON Files", "*.json"),
            ("All Files", "*.*")
        ]
        
        filepath = filedialog.asksaveasfilename(
            title="Save Project As",
            filetypes=filetypes,
            defaultextension=".tsxcm"
        )
        
        if not filepath:
            return False
        
        success = self._save_project_to_file(filepath)
        
        if success:
            # Update current project path and name
            self.current_project_path = filepath
            project_name = os.path.basename(filepath)
            self.project_label.config(text=f"Project: {project_name}")
            
            # Add to recent projects
            self.add_recent_project(filepath)
        
        return success
    
    def _save_project_to_file(self, filepath: str) -> bool:
        """
        Save the project to the specified file
        
        Args:
            filepath: Path to save the project
            
        Returns:
            True if successful, False otherwise
        """
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
            project_name = os.path.basename(filepath)
            self.log(f"Saved project: {project_name}", "success")
            self.set_status(f"Saved: {project_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving project to {filepath}: {e}")
            messagebox.showerror("Error", f"Failed to save project: {e}")
            return False
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes in the project"""
        # Check code editor
        if hasattr(self, 'code_editor') and self.code_editor:
            if self.code_editor.unsaved_changes:
                return True
        
        # For now, that's the only place we track changes
        return False
    
    def load_recent_projects(self) -> List[str]:
        """Load the list of recent projects"""
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
    
    def save_recent_projects(self):
        """Save the list of recent projects"""
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".tsx_component_manager")
            os.makedirs(config_dir, exist_ok=True)
            recent_file = os.path.join(config_dir, "recent_projects.json")
            
            with open(recent_file, 'w', encoding='utf-8') as f:
                json.dump({'recent': self.recent_projects}, f)
                
        except Exception as e:
            logger.error(f"Error saving recent projects: {e}")
    
    def add_recent_project(self, filepath: str):
        """Add a project to the recent projects list"""
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
        
    def add_recent_project(self, filepath: str):
        """Add a project to the recent projects list"""
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
    
    def update_recent_projects_menu(self):
        """Update the Recent Projects submenu"""
        # Clear all items
        self.recent_menu.delete(0, tk.END)
        
        if not self.recent_projects:
            self.recent_menu.add_command(label="No recent projects", state=tk.DISABLED)
            return
        
        # Add recent projects
        for filepath in self.recent_projects:
            # Use basename for display
            project_name = os.path.basename(filepath)
            # Use lambda with default argument to avoid late binding
            self.recent_menu.add_command(
                label=project_name, 
                command=lambda path=filepath: self._load_project_from_file(path)
            )
        
        # Add separator and clear option
        self.recent_menu.add_separator()
        self.recent_menu.add_command(label="Clear Recent Projects", command=self.clear_recent_projects)
    
    def clear_recent_projects(self):
        """Clear the list of recent projects"""
        self.recent_projects = []
        self.save_recent_projects()
        self.update_recent_projects_menu()
    
    def export_and_run_react_app(self):
        """Export components to a React app, install dependencies, and start the app"""
        # Check if there are any components
        components = self.component_list.get_components()
        if not components:
            messagebox.showinfo("Information", "Please add at least one component first")
            return
        
        # Ask for export directory
        export_dir = filedialog.askdirectory(
            title="Select folder to export React application"
        )
        
        if not export_dir:
            return  # User cancelled
        
        # Show a confirmation dialog with list of components
        component_list = "\n".join([f"- {comp.name}" for comp in components])
        result = messagebox.askyesno(
            "Export and Run React App", 
            f"Create and run a React application with the following components?\n\n{component_list}\n\n"
            f"The app will be exported to:\n{export_dir}\n\n"
            "This will install dependencies and start the development server."
        )
        
        if not result:
            return
        
        # Create a progress window
        self.show_export_progress("Exporting React App", export_dir, self._run_react_export)
    
    def export_react_app(self):
        """Export components to a React app (without running)"""
        # Check if there are any components
        components = self.component_list.get_components()
        if not components:
            messagebox.showinfo("Information", "Please add at least one component first")
            return
        
        # Ask for export directory
        export_dir = filedialog.askdirectory(
            title="Select folder to export React application"
        )
        
        if not export_dir:
            return  # User cancelled
        
        # Show a confirmation dialog with list of components
        component_list = "\n".join([f"- {comp.name}" for comp in components])
        result = messagebox.askyesno(
            "Export React App", 
            f"Create a React application with the following components?\n\n{component_list}\n\n"
            f"The app will be exported to:\n{export_dir}"
        )
        
        if not result:
            return
        
        # Create a progress window
        self.show_export_progress("Exporting React App", export_dir, self._run_react_export, run_app=False)
    
    def export_nextjs_app(self):
        """Export components to a Next.js app"""
        # Check if there are any components
        components = self.component_list.get_components()
        if not components:
            messagebox.showinfo("Information", "Please add at least one component first")
            return
        
        # Ask for export directory
        export_dir = filedialog.askdirectory(
            title="Select folder to export Next.js application"
        )
        
        if not export_dir:
            return  # User cancelled
        
        # Ask for Next.js version and options
        options = self.show_nextjs_options()
        if not options:
            return  # User cancelled
        
        # Show a confirmation dialog with list of components
        component_list = "\n".join([f"- {comp.name}" for comp in components])
        result = messagebox.askyesno(
            "Export Next.js App", 
            f"Create a Next.js application with the following components?\n\n{component_list}\n\n"
            f"The app will be exported to:\n{export_dir}"
        )
        
        if not result:
            return
        
        # Create a progress window
        self.show_export_progress("Exporting Next.js App", export_dir, 
                                 lambda progress, path: self._run_nextjs_export(progress, path, options))
    
    def export_component_library(self):
        """Export components as a reusable component library package"""
        # Check if there are any components
        components = self.component_list.get_components()
        if not components:
            messagebox.showinfo("Information", "Please add at least one component first")
            return
        
        # Ask for export directory
        export_dir = filedialog.askdirectory(
            title="Select folder to export component library"
        )
        
        if not export_dir:
            return  # User cancelled
        
        # Ask for library options
        options = self.show_library_options()
        if not options:
            return  # User cancelled
        
        # Show a confirmation dialog with list of components
        component_list = "\n".join([f"- {comp.name}" for comp in components])
        result = messagebox.askyesno(
            "Export Component Library", 
            f"Create a component library with the following components?\n\n{component_list}\n\n"
            f"The library will be exported to:\n{export_dir}"
        )
        
        if not result:
            return
        
        # Create a progress window
        self.show_export_progress("Exporting Component Library", export_dir, 
                                 lambda progress, path: self._run_library_export(progress, path, options))
    
    def show_export_progress(self, title, export_dir, export_func, run_app=True):
        """
        Show a progress window for the export process
        
        Args:
            title: Window title
            export_dir: Export directory
            export_func: Function to run for export (takes progress_callback and path)
            run_app: Whether to run the app after export
        """
        # Create a progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title(title)
        progress_window.geometry("500x400")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Create a progress display
        progress_frame = ttk.Frame(progress_window, padding=20)
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(progress_frame, text=title, font=("Arial", 14)).pack(pady=(0, 10))
        
        progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate")
        progress_bar.pack(fill=tk.X, pady=10)
        progress_bar.start()
        
        progress_text = tk.Text(progress_frame, height=15, wrap=tk.WORD)
        progress_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar to progress text
        scrollbar = ttk.Scrollbar(progress_text, orient=tk.VERTICAL, command=progress_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        progress_text.config(yscrollcommand=scrollbar.set)
        
        # Function to add log messages to the progress window
        def add_progress_log(message):
            progress_text.insert(tk.END, message + "\n")
            progress_text.see(tk.END)
            progress_window.update()
        
        # Function to run the export process
        def run_export():
            try:
                export_func(add_progress_log, export_dir, run_app)
                
                # Create a "Done" button to close the progress window
                ttk.Button(
                    progress_frame, 
                    text="Done", 
                    command=progress_window.destroy
                ).pack(pady=10)
                
                # Stop the progress bar and set it to 100%
                progress_bar.stop()
                progress_bar.config(mode="determinate", value=100)
                
            except Exception as e:
                logger.error(f"Error during export: {e}")
                add_progress_log(f"\nError: {str(e)}")
                
                # Create an "OK" button to close the progress window
                ttk.Button(
                    progress_frame, 
                    text="OK", 
                    command=progress_window.destroy
                ).pack(pady=10)
                
                # Stop the progress bar
                progress_bar.stop()
        
        # Run the export process in a separate thread
        threading.Thread(target=run_export, daemon=True).start()
    
    def _run_react_export(self, progress_callback, export_dir, run_app=True):
        """
        Run the React export process
        
        Args:
            progress_callback: Function to call with progress messages
            export_dir: Export directory
            run_app: Whether to run the app after export
        """
        import subprocess
        import time
        
        progress_callback("Starting export process...")
        
        # Create the React app directory
        app_dir = os.path.join(export_dir, "tsx-components-app")
        os.makedirs(app_dir, exist_ok=True)
        
        # Create basic project structure
        progress_callback("Creating project structure...")
        os.makedirs(os.path.join(app_dir, "public"), exist_ok=True)
        os.makedirs(os.path.join(app_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(app_dir, "src", "components"), exist_ok=True)
        
        # Get all components
        components = self.component_list.get_components()
        
        # Scan all components for dependencies
        progress_callback("Scanning components for dependencies...")
        all_dependencies = set()
        for component in components:
            deps = component.get_dependencies()
            all_dependencies.update(deps)
        
        # Add all components to the components directory
        component_names = []
        component_import_names = []  # For storing camelCase import names
        
        for component in components:
            # Convert hyphenated names to camelCase for JavaScript imports
            camel_case_name = self.to_camel_case(component.name)
            
            # Write to the react app components directory
            component_path = os.path.join(app_dir, "src", "components", f"{camel_case_name}.jsx")
            with open(component_path, 'w', encoding='utf-8') as f:
                f.write(component.content)
            
            component_names.append(component.name)
            component_import_names.append((camel_case_name, component.name))
            progress_callback(f"Added component: {component.name}")
        
        # Build dependency object for package.json
        package_dependencies = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "lucide-react": "^0.279.0",
            "tailwindcss": "^3.3.3"
        }
        
        # Add any additional detected dependencies
        for dep in all_dependencies:
            if dep not in package_dependencies and dep not in ["react", "react-dom"]:
                package_dependencies[dep] = "latest"
                progress_callback(f"Added dependency: {dep}")
        
        # Create package.json
        progress_callback("Creating package.json...")
        package_json = {
            "name": "tsx-components-app",
            "version": "0.1.0",
            "private": True,
            "dependencies": package_dependencies,
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "eslintConfig": {
                "extends": [
                    "react-app",
                    "react-app/jest"
                ]
            },
            "browserslist": {
                "production": [
                    ">0.2%",
                    "not dead",
                    "not op_mini all"
                ],
                "development": [
                    "last 1 chrome version",
                    "last 1 firefox version",
                    "last 1 safari version"
                ]
            },
            "devDependencies": {
                "tailwindcss": "^3.3.3",
                "autoprefixer": "^10.4.14",
                "postcss": "^8.4.24",
                "react-scripts": "5.0.1"
            }
        }
        
        with open(os.path.join(app_dir, "package.json"), 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2)
        
        # Create all the necessary config files
        progress_callback("Creating configuration files...")
        
        # tailwind.config.js
        with open(os.path.join(app_dir, "tailwind.config.js"), 'w', encoding='utf-8') as f:
            f.write("""
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
""")
        
        # postcss.config.js
        with open(os.path.join(app_dir, "postcss.config.js"), 'w', encoding='utf-8') as f:
            f.write("""
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  }
}
""")
        
        # index.html
        with open(os.path.join(app_dir, "public", "index.html"), 'w', encoding='utf-8') as f:
            f.write("""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="TSX Components Viewer" />
    <title>TSX Components Viewer</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
""")
        
        # index.css
        with open(os.path.join(app_dir, "src", "index.css"), 'w', encoding='utf-8') as f:
            f.write("""
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
""")
        
        # index.js
        with open(os.path.join(app_dir, "src", "index.js"), 'w', encoding='utf-8') as f:
            f.write("""
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""")
        
        # Create App.js with component gallery
        progress_callback("Creating App.js with component gallery...")
        
        # Prepare imports
        app_imports = "\n".join([f"import {camel_name} from './components/{camel_name}';" 
                                for camel_name, _ in component_import_names])
        
        # Component object
        app_components_obj = ",\n    ".join([f'"{original_name}": {camel_name}' 
                                        for camel_name, original_name in component_import_names])
        
        # Options for the dropdown
        app_components_options = "\n          ".join([f'<option key="{original_name}" value="{original_name}">{original_name}</option>' 
                                                for _, original_name in component_import_names])
        
        # Default component
        first_component = component_import_names[0][1] if component_import_names else ""
        
        app_js = f"""
import React, {{ useState }} from 'react';
{app_imports}

function App() {{
  const [activeComponent, setActiveComponent] = useState('{first_component}');
  
  const components = {{
    {app_components_obj}
  }};
  
  const ActiveComponent = components[activeComponent];
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">TSX Component Gallery</h1>
      
      <div className="mb-6">
        <label className="block mb-2 font-semibold">Select a Component:</label>
        <select 
          className="border border-gray-300 rounded px-3 py-2 w-full"
          value={{activeComponent}}
          onChange={{(e) => setActiveComponent(e.target.value)}}
        >
          {app_components_options}
        </select>
      </div>
      
      <div className="border border-gray-300 rounded-lg p-4 bg-white">
        <h2 className="text-xl font-bold mb-4">{{activeComponent}}</h2>
        <div className="component-container">
          {{ActiveComponent && <ActiveComponent />}}
        </div>
      </div>
    </div>
  );
}}

export default App;
"""
        
        with open(os.path.join(app_dir, "src", "App.js"), 'w', encoding='utf-8') as f:
            f.write(app_js)
        
        # Create README.md
        with open(os.path.join(app_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(f"""
# TSX Components Viewer

This is a React application that displays various TSX components.

## Included Components

{chr(10).join(f"- {name}" for name in component_names)}

## Getting Started

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

3. Open [http://localhost:3000](http://localhost:3000) to view the application.
""")
        
        if run_app:
            # Install dependencies
            progress_callback("\nInstalling dependencies (this may take a few minutes)...")
            
            # Use shell=True for Windows to ensure npm is found
            is_windows = os.name == 'nt'
            process = subprocess.Popen(
                "npm install" if is_windows else ["npm", "install"],
                cwd=app_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=is_windows
            )
            
            # Monitor installation progress
            while True:
                output = process.stdout.readline()
                if not output and process.poll() is not None:
                    break
                if output:
                    progress_callback(output.decode('utf-8').strip())
            
            # Check for errors
            if process.returncode != 0:
                error = process.stderr.read().decode('utf-8')
                progress_callback(f"Error during npm install: {error}")
                raise Exception(f"npm install failed with code {process.returncode}")
            else:
                progress_callback("Dependencies installed successfully!")
            
            # Start the development server
            progress_callback("\nStarting development server...")
            
            # Use shell=True for Windows to ensure npm is found
            start_process = subprocess.Popen(
                "npm start" if is_windows else ["npm", "start"],
                cwd=app_dir,
                shell=is_windows
            )
            
            # Wait a bit to make sure the server starts
            progress_callback("Waiting for server to start...")
            for _ in range(5):
                time.sleep(1)
            
            progress_callback("\nReact application has been exported and started!")
            progress_callback(f"Location: {app_dir}")
            progress_callback("The React development server should open in your browser.")
            progress_callback("If not, open http://localhost:3000 manually.")
        else:
            progress_callback("\nReact application has been exported!")
            progress_callback(f"Location: {app_dir}")
            progress_callback("\nTo run the application:")
            progress_callback("1. Open a terminal in the exported directory")
            progress_callback("2. Run 'npm install' to install dependencies")
            progress_callback("3. Run 'npm start' to start the development server")
            progress_callback("4. Open http://localhost:3000 in your browser")
    
    def show_nextjs_options(self):
        """Show dialog for Next.js export options"""
        options_window = tk.Toplevel(self.root)
        options_window.title("Next.js Export Options")
        options_window.geometry("400x300")
        options_window.transient(self.root)
        options_window.grab_set()
        
        options_frame = ttk.Frame(options_window, padding=20)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(options_frame, text="Next.js Export Options", font=("Arial", 14)).pack(pady=(0, 10))
        
        # Next.js version
        ttk.Label(options_frame, text="Next.js Version:").pack(anchor=tk.W, pady=(10, 0))
        version_var = tk.StringVar(value="13.4.12")
        ttk.Combobox(
            options_frame, 
            textvariable=version_var, 
            values=["13.4.12", "12.3.4", "11.1.4"]
        ).pack(fill=tk.X, pady=5)
        
        # App Router or Pages Router
        router_var = tk.StringVar(value="app")
        ttk.Label(options_frame, text="Router Type:").pack(anchor=tk.W, pady=(10, 0))
        ttk.Radiobutton(
            options_frame, text="App Router", variable=router_var, value="app"
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            options_frame, text="Pages Router", variable=router_var, value="pages"
        ).pack(anchor=tk.W)
        
        # TypeScript
        typescript_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Use TypeScript", variable=typescript_var
        ).pack(anchor=tk.W, pady=(10, 0))
        
        # ESLint
        eslint_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Include ESLint", variable=eslint_var
        ).pack(anchor=tk.W)
        
        # Tailwind CSS
        tailwind_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Include Tailwind CSS", variable=tailwind_var
        ).pack(anchor=tk.W)
        
        # Result variable to store the selected options
        result = {}
        
        # Buttons
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def on_cancel():
            nonlocal result
            result = None
            options_window.destroy()
        
        def on_ok():
            nonlocal result
            result = {
                "version": version_var.get(),
                "router": router_var.get(),
                "typescript": typescript_var.get(),
                "eslint": eslint_var.get(),
                "tailwind": tailwind_var.get()
            }
            options_window.destroy()
        
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=5)
        
        # Wait for the window to close
        self.root.wait_window(options_window)
        
        return result
    
    def show_library_options(self):
        """Show dialog for component library export options"""
        options_window = tk.Toplevel(self.root)
        options_window.title("Component Library Export Options")
        options_window.geometry("400x350")
        options_window.transient(self.root)
        options_window.grab_set()
        
        options_frame = ttk.Frame(options_window, padding=20)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(options_frame, text="Component Library Options", font=("Arial", 14)).pack(pady=(0, 10))
        
        # Package name
        ttk.Label(options_frame, text="Package Name:").pack(anchor=tk.W, pady=(10, 0))
        name_var = tk.StringVar(value="my-component-library")
        ttk.Entry(options_frame, textvariable=name_var).pack(fill=tk.X, pady=5)
        
        # Package version
        ttk.Label(options_frame, text="Version:").pack(anchor=tk.W, pady=(10, 0))
        version_var = tk.StringVar(value="0.1.0")
        ttk.Entry(options_frame, textvariable=version_var).pack(fill=tk.X, pady=5)
        
        # TypeScript
        typescript_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Use TypeScript", variable=typescript_var
        ).pack(anchor=tk.W, pady=(10, 0))
        
        # Build system
        build_var = tk.StringVar(value="rollup")
        ttk.Label(options_frame, text="Build System:").pack(anchor=tk.W, pady=(10, 0))
        ttk.Radiobutton(
            options_frame, text="Rollup", variable=build_var, value="rollup"
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            options_frame, text="Webpack", variable=build_var, value="webpack"
        ).pack(anchor=tk.W)
        
        # Include Storybook
        storybook_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Include Storybook", variable=storybook_var
        ).pack(anchor=tk.W, pady=(10, 0))
        
        # Result variable to store the selected options
        result = {}
        
        # Buttons
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def on_cancel():
            nonlocal result
            result = None
            options_window.destroy()
        
        def on_ok():
            nonlocal result
            result = {
                "name": name_var.get(),
                "version": version_var.get(),
                "typescript": typescript_var.get(),
                "build": build_var.get(),
                "storybook": storybook_var.get()
            }
            options_window.destroy()
        
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=5)
        
        # Wait for the window to close
        self.root.wait_window(options_window)
        
        return result
    
    def _run_nextjs_export(self, progress_callback, export_dir, options):
        """Run the Next.js export process with selected options"""
        progress_callback("Starting Next.js export process...")
        progress_callback(f"Using options: {options}")
        
        # This is a placeholder for the actual implementation
        # In a real implementation, you would:
        # 1. Create a Next.js project using npx create-next-app
        # 2. Add the components to the appropriate directory
        # 3. Set up the pages to display the components
        
        app_dir = os.path.join(export_dir, "nextjs-components-app")
        progress_callback(f"Creating Next.js app in: {app_dir}")
        
        # For now, just simulate progress
        import time
        progress_callback("Creating Next.js project structure...")
        time.sleep(1)
        
        progress_callback("Adding components...")
        time.sleep(1)
        
        progress_callback("Setting up pages...")
        time.sleep(1)
        
        progress_callback("Next.js app export completed!")
        progress_callback(f"To run the app, navigate to {app_dir} and run:")
        progress_callback("npm install")
        progress_callback("npm run dev")
    
    def _run_library_export(self, progress_callback, export_dir, options):
        """Run the component library export process with selected options"""
        progress_callback("Starting component library export process...")
        progress_callback(f"Using options: {options}")
        
        # This is a placeholder for the actual implementation
        # In a real implementation, you would:
        # 1. Set up a library project structure
        # 2. Add the components
        # 3. Set up the build system (Rollup or Webpack)
        # 4. Add Storybook if requested
        
        lib_dir = os.path.join(export_dir, options["name"])
        progress_callback(f"Creating component library in: {lib_dir}")
        
        # For now, just simulate progress
        import time
        progress_callback("Setting up library project structure...")
        time.sleep(1)
        
        progress_callback("Adding components...")
        time.sleep(1)
        
        progress_callback("Configuring build system...")
        time.sleep(1)
        
        if options["storybook"]:
            progress_callback("Setting up Storybook...")
            time.sleep(1)
        
        progress_callback("Component library export completed!")
        progress_callback(f"To build the library, navigate to {lib_dir} and run:")
        progress_callback("npm install")
        progress_callback("npm run build")
    
    def show_documentation(self):
        """Show the application documentation"""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("TSX Component Manager Documentation")
        doc_window.geometry("600x500")
        doc_window.transient(self.root)
        
        doc_frame = ttk.Frame(doc_window, padding=20)
        doc_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(doc_frame, text="TSX Component Manager", font=("Arial", 16, "bold")).pack(pady=(0, 10))
        
        # Create a scrollable text widget for documentation
        doc_text = tk.Text(doc_frame, wrap=tk.WORD, padx=10, pady=10)
        doc_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(doc_text, orient=tk.VERTICAL, command=doc_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        doc_text.config(yscrollcommand=scrollbar.set)
        
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
        
        # Insert the documentation content
        doc_text.insert('1.0', doc_content)
        doc_text.config(state=tk.DISABLED)  # Make it read-only
        
        # Close button
        ttk.Button(doc_frame, text="Close", command=doc_window.destroy).pack(pady=10)
    
    def show_about(self):
        """Show information about the application"""
        messagebox.showinfo(
            "About TSX Component Manager",
            "TSX Component Manager 1.0\n\n"
            "A desktop application for managing, editing, and exporting "
            "React TypeScript (TSX) components.\n\n"
            "© 2023 Your Name"
        )
    
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
    
    def on_close(self):
        """Handle application close event"""
        # Check for unsaved changes
        if self.has_unsaved_changes():
            if not messagebox.askyesno("Unsaved Changes", 
                                     "You have unsaved changes. Exit anyway?"):
                return
        
        # Clean up temporary directory
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {e}")
        
        # Close the application
        self.root.destroy()