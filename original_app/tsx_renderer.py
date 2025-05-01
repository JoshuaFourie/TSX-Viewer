import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, messagebox
import os
import subprocess
import sys
import threading
import json
import time
import webbrowser
import tempfile
import shutil
import socket
import re
from pathlib import Path

class TSXRenderer:
    def __init__(self, root):
        self.root = root
        self.root.title("TSX Component Renderer")
        self.root.geometry("1200x800")
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TNotebook", background="#f0f0f0")
        self.style.configure("TNotebook.Tab", padding=[10, 2], font=("Helvetica", 10))
        
        # Main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the header frame
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Header label
        header_label = ttk.Label(header_frame, text="TSX Component Renderer", 
                            font=("Arial", 16))
        header_label.pack(side=tk.LEFT)
        
        # Open file button
        self.open_button = ttk.Button(header_frame, text="Select TSX File", 
                                command=self.open_file)
        self.open_button.pack(side=tk.RIGHT)
        
        # Open in browser button
        self.browser_button = ttk.Button(header_frame, text="Open in Browser", 
                                command=self.open_in_browser)
        self.browser_button.pack(side=tk.RIGHT, padx=10)
        
        # Add Export to React App button
        self.export_button = ttk.Button(header_frame, text="Export to React App", 
                                command=self.export_to_react_app)
        self.export_button.pack(side=tk.RIGHT, padx=10)
        
        # File info label
        self.file_label = ttk.Label(self.main_frame, text="No file selected", 
                            font=("Arial", 10))
        self.file_label.pack(fill=tk.X, pady=(0, 10))
        
        # Create paned window for code and preview
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Code view frame
        self.code_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.code_frame, weight=1)
        
        # Code view label
        code_label = ttk.Label(self.code_frame, text="TSX Code")
        code_label.pack(fill=tk.X)
        
        # Code text widget
        self.code_text = scrolledtext.ScrolledText(self.code_frame, wrap=tk.NONE, 
                                            font=("Courier", 10))
        self.code_text.pack(fill=tk.BOTH, expand=True)
        
        # Preview frame
        self.preview_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.preview_frame, weight=1)
        
        # Preview label
        self.preview_label = ttk.Label(self.preview_frame, text="Component Preview")
        self.preview_label.pack(fill=tk.X)
        
        # Browser frame for preview
        self.browser_frame = ttk.Frame(self.preview_frame)
        self.browser_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a label for the preview instructions
        self.preview_instructions = ttk.Label(self.browser_frame, 
                                    text="Select a TSX file to render it",
                                    font=("Arial", 12))
        self.preview_instructions.pack(expand=True)
        
        # Create a console for webpack output
        self.create_console()
        
        # Status bar
        self.status_bar = ttk.Label(self.main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Initialize variables
        self.server = None
        self.server_thread = None
        self.current_file = None
        self.temp_dir = None
        self.port = 8081  # Static port instead of finding a free one
        self.webpack_ready = False
        self.server_ready_checked = False  # Flag to check if server is ready
        self.dependencies = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "lucide-react": "^0.279.0",  # Add lucide-react dependency
            "tailwindcss": "^3.3.0"      # Add Tailwind CSS
        }
        self.dev_dependencies = {
            "@babel/core": "^7.22.5",
            "@babel/preset-env": "^7.22.5",
            "@babel/preset-react": "^7.22.5",
            "@babel/preset-typescript": "^7.22.5",
            "babel-loader": "^9.1.2",
            "html-webpack-plugin": "^5.5.3",
            "typescript": "^5.1.3",
            "webpack": "^5.88.0",
            "webpack-cli": "^5.1.4",
            "webpack-dev-server": "^4.15.1",
            "css-loader": "^6.8.1",       # For Tailwind
            "postcss": "^8.4.31",         # For Tailwind
            "postcss-loader": "^7.3.3",   # For Tailwind
            "style-loader": "^3.3.3",     # For Tailwind
            "autoprefixer": "^10.4.16"    # For Tailwind
        }
        
        # Check if the port is available
        if not self.is_port_available(self.port):
            messagebox.showwarning(
                "Port Already in Use", 
                f"Port {self.port} is already in use. The application may not function correctly."
            )
        
        # Set up the development environment
        self.setup_development_environment()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Control-o>", lambda event: self.open_file())
        
        # Initialize a list to keep track of opened components
        self.opened_components = []

    # Add a method to track opened components
    def track_component(self, filepath, component_name):
        """Keep track of opened components for React app export"""
        # Check if this component is already tracked
        for path, name in self.opened_components:
            if path == filepath:
                return  # Already tracked
        
        # Add to the tracked components list
        self.opened_components.append((filepath, component_name))
        self.add_to_console(f"Component {component_name} added to export list")

    # Modify the open_file method to call track_component
    def open_file(self):
        """Open a TSX file and render it."""
        filetypes = [
            ("TypeScript React Files", "*.tsx"),
            ("All Files", "*.*")
        ]
        
        filepath = filedialog.askopenfilename(
            title="Select TSX File",
            filetypes=filetypes
        )
        
        if not filepath:
            return
        
        # Check if webpack is ready
        if not self.webpack_ready:
            messagebox.showinfo("Please Wait", "Webpack is still initializing. Please wait until the server is running.")
            return
        
        self.current_file = filepath
        filename = os.path.basename(filepath)
        component_name = filename.split('.')[0]
        self.file_label.config(text=f"Rendering: {filename}")
        
        # Track this component for React app export
        self.track_component(filepath, component_name)
        
        # Read file content
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Update code view
            self.code_text.delete(1.0, tk.END)
            self.code_text.insert(tk.END, content)
            
            # Check for additional dependencies
            self.check_dependencies(content)
            
            # Process the file to make it renderable
            self.process_tsx_file(filepath, content)
            
        except Exception as e:
            self.status_bar.config(text=f"Error opening file: {str(e)}")
            self.add_to_console(f"Error opening file: {str(e)}")
            messagebox.showerror("Error", f"Could not open file: {str(e)}")

    # Enhanced export_to_react_app method
    def export_to_react_app(self):
        """Handle the export to React app button click"""
        # Check if any files have been opened/processed
        if not self.opened_components:
            messagebox.showinfo("Information", "Please open at least one TSX file first.")
            return
        
        # Show a confirmation dialog with list of components
        component_list = "\n".join([f"- {name}" for _, name in self.opened_components])
        result = messagebox.askyesno(
            "Export to React App", 
            f"Create a React application with the following components?\n\n{component_list}\n\n"
            "This will generate a downloadable React app with your components."
        )
        
        if result:
            self.create_react_app(self.opened_components)
    
    def is_port_available(self, port):
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except:
            return False
        
    def open_in_browser(self):
        """Open the preview in a web browser"""
        webbrowser.open(f"http://localhost:{self.port}")
    
    def create_console(self):
        """Create a console window for webpack output"""
        console_frame = ttk.LabelFrame(self.main_frame, text="Webpack Console")
        console_frame.pack(fill=tk.X, expand=False, pady=(10, 0))
        
        self.console_text = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, 
                                               height=6, font=("Courier", 9))
        self.console_text.pack(fill=tk.BOTH, expand=True)
        self.console_text.config(state=tk.DISABLED)
        
    def add_to_console(self, text):
        """Add text to the console window"""
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, text + "\n")
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)
        self.root.update()

    def setup_development_environment(self):
        """Set up the React development environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.status_bar.config(text="Setting up development environment...")
        
        # Create the necessary files for a minimal React app with Tailwind
        self.create_react_app_files()
        
        # Start the development server
        self.start_server()
        
        # Set a timeout to check server status if webpack ready flag isn't set
        self.root.after(10000, self.check_server_startup)

    def check_server_startup(self):
        """Check if server has started even if we missed the signal"""
        if not self.webpack_ready and not self.server_ready_checked:
            self.server_ready_checked = True
            
            # Try to connect to the server to see if it's actually running
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(('localhost', self.port))
                    # If we can connect, the server is running
                    self.webpack_ready = True
                    self.status_bar.config(text=f"Development server running on port {self.port}")
                    self.add_to_console("\nServer detected as running on port 8081")
                    
                    # Notify that server is ready
                    messagebox.showinfo(
                        "Server Ready", 
                        f"Webpack server is running on port {self.port}.\n\n"
                        f"You can open the preview in your browser with the 'Open in Browser' button."
                    )
            except:
                # If we can't connect, server might not be running yet
                self.add_to_console("\nCould not detect server running. Waiting longer...")
                # Try again in 10 seconds
                self.root.after(10000, self.check_server_startup)

    def scan_imports(self, content):
        """Scan the content for import statements to detect dependencies with improved detection"""
        # Regular expression to match import statements
        import_pattern = r"import\s+(?:{[^}]*}|\*\s+as\s+[a-zA-Z_][a-zA-Z0-9_]*|[a-zA-Z_][a-zA-Z0-9_]*)\s+from\s+['\"]([^'\"]+)['\"]"
        matches = re.findall(import_pattern, content)
        
        # Filter out relative imports and React core packages
        external_packages = []
        for match in matches:
            if not match.startswith('.') and match not in ['react', 'react-dom']:
                external_packages.append(match)
        
        # Special handling for lucide-react which is used in many components
        if 'lucide-react' not in external_packages and any(icon in content for icon in 
                                                        ['Server', 'Database', 'Globe', 'Users', 
                                                        'Network', 'Shield', 'Activity']):
            external_packages.append('lucide-react')
        
        return list(set(external_packages))  # Remove duplicates

    def create_react_app_files(self):
        """Create the basic files needed for a React app with Tailwind CSS."""
        # Create package.json
        package_json = {
            "name": "tsx-renderer",
            "version": "1.0.0",
            "description": "TSX Renderer",
            "main": "index.js",
            "scripts": {
                "start": "webpack serve --mode development"
            },
            "dependencies": self.dependencies,
            "devDependencies": self.dev_dependencies
        }
        
        with open(os.path.join(self.temp_dir, "package.json"), "w") as f:
            json.dump(package_json, f, indent=2)
        
        # Create webpack.config.js with CSS support
        webpack_config = r"""
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  entry: './src/index.tsx',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.jsx'],
  },
  module: {
    rules: [
      {
        test: /\.(ts|tsx|js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              '@babel/preset-env',
              '@babel/preset-react',
              '@babel/preset-typescript'
            ]
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader', 'postcss-loader']
      }
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html'
    })
  ],
  devServer: {
    static: {
      directory: path.join(__dirname, 'public'),
    },
    port: """ + str(self.port) + """,
    hot: true,
    open: false
  }
};
"""
        
        with open(os.path.join(self.temp_dir, "webpack.config.js"), "w") as f:
            f.write(webpack_config)
        
        # Create babel.config.js
        babel_config = """
module.exports = {
  presets: [
    '@babel/preset-env',
    '@babel/preset-react',
    '@babel/preset-typescript'
  ]
};
"""
        
        with open(os.path.join(self.temp_dir, "babel.config.js"), "w") as f:
            f.write(babel_config)
        
        # Create postcss.config.js for Tailwind
        postcss_config = """
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  }
}
"""
        
        with open(os.path.join(self.temp_dir, "postcss.config.js"), "w") as f:
            f.write(postcss_config)
        
        # Create tailwind.config.js
        tailwind_config = """
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
        
        with open(os.path.join(self.temp_dir, "tailwind.config.js"), "w") as f:
            f.write(tailwind_config)
        
        # Create tsconfig.json
        tsconfig = """
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
"""
        
        with open(os.path.join(self.temp_dir, "tsconfig.json"), "w") as f:
            f.write(tsconfig)
        
        # Create directory structure
        os.makedirs(os.path.join(self.temp_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "public"), exist_ok=True)
        
        # Create public/index.html
        index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TSX Component Renderer</title>
</head>
<body>
    <div id="root"></div>
</body>
</html>
"""
        
        with open(os.path.join(self.temp_dir, "public", "index.html"), "w") as f:
            f.write(index_html)
        
        # Create src/index.css with Tailwind directives
        index_css = """
@tailwind base;
@tailwind components;
@tailwind utilities;
"""
        
        with open(os.path.join(self.temp_dir, "src", "index.css"), "w") as f:
            f.write(index_css)
        
        # Create src/index.tsx
        index_tsx = """
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
        
        with open(os.path.join(self.temp_dir, "src", "index.tsx"), "w") as f:
            f.write(index_tsx)
        
        # Create initial App.tsx
        app_tsx = """
import React from 'react';

const App: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-center mb-6">TSX Component Renderer</h1>
      <p className="text-center">Select a TSX file to render it.</p>
    </div>
  );
};

export default App;
"""
        
        with open(os.path.join(self.temp_dir, "src", "App.tsx"), "w") as f:
            f.write(app_tsx)
        
        self.status_bar.config(text="Installing dependencies, this may take a few minutes...")
        self.add_to_console("Installing npm dependencies...")
        self.root.update()
        
        # Install dependencies
        try:
            # Use shell=True for Windows to ensure npm is found
            is_windows = os.name == 'nt'
            process = subprocess.Popen(
                "npm install" if is_windows else ["npm", "install"],
                cwd=self.temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=is_windows
            )
            
            # Monitor installation progress
            for line in process.stdout:
                line_str = line.decode('utf-8').strip()
                self.add_to_console(line_str)
            
            process.wait()
            
            if process.returncode == 0:
                self.status_bar.config(text="Dependencies installed successfully")
                self.add_to_console("Dependencies installed successfully")
            else:
                error_output = process.stderr.read().decode('utf-8')
                self.status_bar.config(text="Error installing dependencies")
                self.add_to_console(f"Error installing dependencies: {error_output}")
                
        except Exception as e:
            self.status_bar.config(text=f"Error installing dependencies: {e}")
            self.add_to_console(f"Error installing dependencies: {str(e)}")

    def install_package(self, package_name):
        """Install a specific npm package"""
        self.status_bar.config(text=f"Installing {package_name}...")
        self.add_to_console(f"Installing {package_name}...")
        
        try:
            # Use shell=True for Windows to ensure npm is found
            is_windows = os.name == 'nt'
            process = subprocess.Popen(
                f"npm install {package_name}" if is_windows else ["npm", "install", package_name],
                cwd=self.temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=is_windows
            )
            
            # Monitor installation progress
            for line in process.stdout:
                line_str = line.decode('utf-8').strip()
                self.add_to_console(line_str)
            
            process.wait()
            
            if process.returncode == 0:
                self.status_bar.config(text=f"{package_name} installed successfully")
                self.add_to_console(f"{package_name} installed successfully")
                return True
            else:
                error_output = process.stderr.read().decode('utf-8')
                self.status_bar.config(text=f"Error installing {package_name}")
                self.add_to_console(f"Error installing {package_name}: {error_output}")
                return False
                
        except Exception as e:
            self.status_bar.config(text=f"Error installing {package_name}: {e}")
            self.add_to_console(f"Error installing {package_name}: {str(e)}")
            return False

    def start_server(self):
        """Start the webpack development server."""
        def run_server():
            try:
                self.status_bar.config(text=f"Starting development server on port {self.port}...")
                self.add_to_console(f"Starting webpack development server on port {self.port}...")
                
                # Use shell=True for Windows to ensure npm is found
                is_windows = os.name == 'nt'
                process = subprocess.Popen(
                    "npm start" if is_windows else ["npm", "start"],
                    cwd=self.temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=is_windows
                )
                
                # Process both stdout and stderr
                while True:
                    # Read from stdout
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        line_str = stdout_line.decode('utf-8').strip()
                        self.add_to_console(line_str)
                        
                        # More patterns to detect successful compilation
                        if any(pattern in line_str.lower() for pattern in [
                            "compiled successfully", 
                            "webpack compiled",
                            "on your network",
                            "project is running at",
                            "(name: main"
                        ]):
                            # Wait a bit to ensure server is fully started
                            time.sleep(1)
                            self.status_bar.config(text=f"Development server running on port {self.port}")
                            # Set webpack ready flag
                            self.webpack_ready = True
                            # Notify that server is ready
                            self.root.after(0, lambda: messagebox.showinfo(
                                "Server Ready", 
                                f"Webpack server is running on port {self.port}.\n\n"
                                f"You can open the preview in your browser with the 'Open in Browser' button."
                            ))
                    
                    # Read from stderr
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        line_str = stderr_line.decode('utf-8').strip()
                        self.add_to_console(line_str)
                        
                        # Check for address in use error
                        if "address already in use" in line_str.lower():
                            self.status_bar.config(text=f"Error: Port {self.port} is already in use")
                            self.root.after(0, lambda: messagebox.showerror(
                                "Port Error", 
                                f"Port {self.port} is already in use. Please close any application using this port and restart."
                            ))
                        elif "error" in line_str.lower():
                            self.status_bar.config(text=f"Error in webpack: {line_str}")
                    
                    # Check if process is still running
                    if process.poll() is not None:
                        if process.returncode != 0:
                            self.status_bar.config(text=f"Server stopped with code {process.returncode}")
                        break
                        
                    # If no output, give a small pause
                    if not stdout_line and not stderr_line:
                        time.sleep(0.1)
                        
            except Exception as e:
                self.status_bar.config(text=f"Error starting server: {e}")
                self.add_to_console(f"Error starting server: {str(e)}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

    def open_file(self):
        """Open a TSX file and render it."""
        filetypes = [
            ("TypeScript React Files", "*.tsx"),
            ("All Files", "*.*")
        ]
        
        filepath = filedialog.askopenfilename(
            title="Select TSX File",
            filetypes=filetypes
        )
        
        if not filepath:
            return
        
        # Check if webpack is ready
        if not self.webpack_ready:
            messagebox.showinfo("Please Wait", "Webpack is still initializing. Please wait until the server is running.")
            return
        
        self.current_file = filepath
        filename = os.path.basename(filepath)
        self.file_label.config(text=f"Rendering: {filename}")
        
        # Read file content
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Update code view
            self.code_text.delete(1.0, tk.END)
            self.code_text.insert(tk.END, content)
            
            # Check for additional dependencies
            self.check_dependencies(content)
            
            # Process the file to make it renderable
            self.process_tsx_file(filepath, content)
            
        except Exception as e:
            self.status_bar.config(text=f"Error opening file: {str(e)}")
            self.add_to_console(f"Error opening file: {str(e)}")
            messagebox.showerror("Error", f"Could not open file: {str(e)}")

    def check_dependencies(self, content):
        """Check for dependencies in the content and install if needed"""
        packages = self.scan_imports(content)
        
        if packages:
            self.add_to_console(f"Detected imports: {', '.join(packages)}")
            
            # Check which packages need to be installed
            for package in packages:
                # Skip packages that are already in dependencies
                if package in self.dependencies:
                    continue
                
                # Automatically install essential packages without asking
                essential_packages = ['lucide-react', 'tailwindcss']
                if package in essential_packages:
                    self.add_to_console(f"Installing essential package: {package}")
                    success = self.install_package(package)
                    if success:
                        # Add to dependencies list
                        self.dependencies[package] = "latest"
                    else:
                        messagebox.showwarning("Warning", 
                                            f"Failed to install {package}. Component may not render correctly.")
                else:
                    # Ask user if they want to install non-essential packages
                    if messagebox.askyesno("Install Package", 
                                        f"The component requires '{package}'. Install it?"):
                        success = self.install_package(package)
                        if success:
                            # Add to dependencies list
                            self.dependencies[package] = "latest"
                        else:
                            messagebox.showwarning("Warning", 
                                                f"Failed to install {package}. Component may not render correctly.")

# Enhanced TSX Renderer Fix (Corrected)
# Fixed the f-string syntax error with JSX content

    def process_tsx_file(self, filepath, content):
        """Process TSX file with a minimal HTML approach that avoids all compatibility issues."""
        self.status_bar.config(text="Processing TSX file...")
        self.add_to_console("Processing TSX file...")
        
        # Extract the component name
        component_name = os.path.basename(filepath).split('.')[0]
        self.add_to_console(f"Component name: {component_name}")
        
        try:
            # Create a minimal HTML renderer that doesn't rely on Lucide or complex JSX
            html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TSX Component Viewer - {component_name}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            pre {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                overflow: auto;
                border: 1px solid #e9ecef;
            }}
            h1 {{
                color: #333;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            .icon-placeholder {{
                display: inline-block;
                width: 24px;
                height: 24px;
                background-color: #e2e8f0;
                border-radius: 4px;
                margin-right: 8px;
                vertical-align: middle;
            }}
            .code-section {{
                margin-top: 20px;
            }}
            .component-info {{
                margin-bottom: 20px;
                padding: 15px;
                background-color: #e6f7ff;
                border-radius: 4px;
                border-left: 4px solid #1890ff;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Component Viewer: {component_name}</h1>
            
            <div class="component-info">
                <p><strong>Note:</strong> This is a static view of your component code. Due to compatibility issues with Lucide icons and JSX in the browser, 
                we're displaying the code instead of rendering the actual component.</p>
                <p>To render your component properly, you may need to:</p>
                <ul>
                    <li>Create a standard React application with Create React App</li>
                    <li>Install the necessary dependencies (react, lucide-react, etc.)</li>
                    <li>Import your component into the new application</li>
                </ul>
            </div>
            
            <div class="code-section">
                <h2>Component Code:</h2>
                <pre><code>{content.replace('<', '&lt;').replace('>', '&gt;')}</code></pre>
            </div>
            
            <div class="code-section">
                <h2>How to use this component:</h2>
                <pre><code>
    import React from 'react';
    import {component_name} from './{component_name}';

    function App() {{
    return (
        &lt;div className="container"&gt;
        &lt;h1&gt;My Application&lt;/h1&gt;
        &lt;{component_name} /&gt;
        &lt;/div&gt;
    );
    }}

    export default App;
                </code></pre>
            </div>
        </div>
    </body>
    </html>
    """
            
            # Write the HTML file
            html_path = os.path.join(self.temp_dir, "public", "view.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.add_to_console(f"Wrote view.html to {html_path}")
            
            # Open the HTML file in browser
            self.status_bar.config(text="Opening component viewer...")
            self.viewer_url = f"http://localhost:{self.port}/view.html"
            webbrowser.open(self.viewer_url)
            self.add_to_console(f"Opened component viewer at {self.viewer_url}")
            
            # Also create a downloadable version of the component for the user
            download_path = os.path.join(self.temp_dir, "public", f"{component_name}-download.tsx")
            with open(download_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.add_to_console(f"Created downloadable component at {download_path}")
            self.add_to_console(f"You can download this at: http://localhost:{self.port}/{component_name}-download.tsx")
            
        except Exception as e:
            self.status_bar.config(text=f"Error creating viewer: {str(e)}")
            self.add_to_console(f"Error creating viewer: {str(e)}")
            import traceback
            self.add_to_console(traceback.format_exc())
            messagebox.showerror("Error", f"Could not create component viewer: {str(e)}")

    def setup_development_environment(self):
        """Set up the development environment with a focus on serving static files."""
        self.temp_dir = tempfile.mkdtemp()
        self.status_bar.config(text="Setting up minimal server environment...")
        
        # Create the necessary directories
        os.makedirs(os.path.join(self.temp_dir, "public"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "src"), exist_ok=True)
        
        # Create a minimal webpack.config.js focused on serving static files
        webpack_config = f"""
    const path = require('path');
    const HtmlWebpackPlugin = require('html-webpack-plugin');

    module.exports = {{
    mode: 'development',
    entry: './src/index.js',
    output: {{
        path: path.resolve(__dirname, 'dist'),
        filename: 'bundle.js',
    }},
    devServer: {{
        static: {{
        directory: path.join(__dirname, 'public'),
        }},
        port: {self.port},
        hot: false,
        open: false
    }}
    }};
    """
        
        with open(os.path.join(self.temp_dir, "webpack.config.js"), "w") as f:
            f.write(webpack_config)
        
        # Create a minimal index.js
        with open(os.path.join(self.temp_dir, "src", "index.js"), "w") as f:
            f.write("console.log('Static file server started');")
        
        # Create minimal package.json
        package_json = """
    {
    "name": "tsx-viewer",
    "version": "1.0.0",
    "description": "TSX Component Viewer",
    "main": "index.js",
    "scripts": {
        "start": "webpack serve"
    },
    "devDependencies": {
        "html-webpack-plugin": "^5.5.0",
        "webpack": "^5.75.0",
        "webpack-cli": "^4.10.0",
        "webpack-dev-server": "^4.11.1"
    }
    }
    """
        
        with open(os.path.join(self.temp_dir, "package.json"), "w") as f:
            f.write(package_json)
        
        # Create a welcome index.html
        with open(os.path.join(self.temp_dir, "public", "index.html"), "w") as f:
            f.write("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TSX Component Viewer</title>
    </head>
    <body>
        <h1>TSX Component Viewer</h1>
        <p>Select a TSX file to view it.</p>
    </body>
    </html>
    """)
        
        self.status_bar.config(text="Installing minimal dependencies...")
        self.add_to_console("Installing minimal dependencies for static file server...")
        
        # Install dependencies
        try:
            # Use shell=True for Windows to ensure npm is found
            is_windows = os.name == 'nt'
            process = subprocess.Popen(
                "npm install" if is_windows else ["npm", "install"],
                cwd=self.temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=is_windows
            )
            
            # Monitor installation progress
            for line in process.stdout:
                line_str = line.decode('utf-8').strip()
                self.add_to_console(line_str)
            
            process.wait()
            
            if process.returncode == 0:
                self.status_bar.config(text="Dependencies installed successfully")
                self.add_to_console("Dependencies installed successfully")
            else:
                error_output = process.stderr.read().decode('utf-8')
                self.status_bar.config(text="Error installing dependencies")
                self.add_to_console(f"Error installing dependencies: {error_output}")
                
        except Exception as e:
            self.status_bar.config(text=f"Error installing dependencies: {e}")
            self.add_to_console(f"Error installing dependencies: {str(e)}")
        
        # Start the server
        self.start_server()

    def refresh_webpack_server(self):
        """Refresh the webpack server to ensure changes are picked up"""
        try:
            # Try to trigger a webpack rebuild by touching the index.tsx file
            index_path = os.path.join(self.temp_dir, "src", "index.tsx")
            if os.path.exists(index_path):
                # Read the current content
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Write it back with a comment to trigger a change
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(content + f"\n// Rebuild trigger: {time.time()}")
                
                self.add_to_console("Triggered webpack rebuild")
            
            # Wait a bit longer then open the preview
            self.root.after(3000, self.open_preview)
        except Exception as e:
            self.add_to_console(f"Error refreshing webpack: {str(e)}")
            # Try to open preview anyway
            self.root.after(1000, self.open_preview)
    
    def check_webpack_rebuild(self):
        """Check if webpack has finished rebuilding before opening preview"""
        max_attempts = 10
        self.webpack_rebuild_attempts += 1
        
        if self.webpack_rebuild_attempts <= max_attempts:
            # Try to connect to the server to see if it's responding
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)  # Short timeout for quick check
                    s.connect(('localhost', self.port))
                    # If we can connect, proceed to open preview
                    self.status_bar.config(text="Webpack rebuild complete, opening preview...")
                    self.open_preview()
            except:
                # If we can't connect yet, wait and try again
                delay = 1000  # 1 second delay between attempts
                self.add_to_console(f"Waiting for webpack rebuild... Attempt {self.webpack_rebuild_attempts}/{max_attempts}")
                self.root.after(delay, self.check_webpack_rebuild)
        else:
            # If we've tried too many times, just try to open it anyway
            self.status_bar.config(text="Opening preview (webpack may not be ready yet)...")
            self.add_to_console("Maximum rebuild wait time reached, trying to open preview anyway.")
            self.open_preview()    
    
    def open_preview(self):
        """Open the preview and update status"""
        self.status_bar.config(text="Opening preview in browser...")
        self.open_in_browser()
        
        # Update status
        self.status_bar.config(text="Preview available in browser window")
        self.add_to_console("Preview opened in browser. If it doesn't show correctly, try refreshing after a few seconds.")

    def on_close(self):
        """Clean up before closing the application."""
        # Clean up temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
        
        # Close the application
        self.root.destroy()

    def create_react_app(self, component_files):
        """
        Create a standalone React application with all the selected components.
        
        Args:
            component_files: List of (filepath, component_name) tuples for components to include
        """
        import zipfile
        import os
        import tempfile
        import re
        
        self.status_bar.config(text="Creating React application...")
        self.add_to_console("Creating React application for components...")
        
        try:
            # Create a temporary directory for the React app
            react_app_dir = os.path.join(self.temp_dir, "react-app")
            os.makedirs(react_app_dir, exist_ok=True)
            
            # Create basic project structure
            os.makedirs(os.path.join(react_app_dir, "public"), exist_ok=True)
            os.makedirs(os.path.join(react_app_dir, "src"), exist_ok=True)
            os.makedirs(os.path.join(react_app_dir, "src", "components"), exist_ok=True)
            
            # Add all components to the components directory
            component_names = []
            component_import_names = []  # For storing camelCase import names
            
            for filepath, component_name in component_files:
                # Read the component file
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Convert hyphenated names to camelCase for JavaScript imports
                # e.g., domain-structure-diagram -> DomainStructureDiagram
                camel_case_name = self.to_camel_case(component_name)
                
                # Write to the react app components directory
                component_path = os.path.join(react_app_dir, "src", "components", f"{camel_case_name}.jsx")
                with open(component_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                component_names.append(component_name)
                component_import_names.append((camel_case_name, component_name))
                self.add_to_console(f"Added component: {component_name} as {camel_case_name}")
            
            # Create package.json
            package_json = """
    {
    "name": "tsx-components-viewer",
    "version": "0.1.0",
    "private": true,
    "dependencies": {
        "@testing-library/jest-dom": "^5.16.5",
        "@testing-library/react": "^13.4.0",
        "@testing-library/user-event": "^13.5.0",
        "lucide-react": "^0.279.0",
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "react-scripts": "5.0.1",
        "web-vitals": "^2.1.4"
    },
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
        "postcss": "^8.4.24"
    }
    }
    """
            
            with open(os.path.join(react_app_dir, "package.json"), 'w', encoding='utf-8') as f:
                f.write(package_json)
            
            # Create tailwind.config.js
            tailwind_config = """
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
    """
            
            with open(os.path.join(react_app_dir, "tailwind.config.js"), 'w', encoding='utf-8') as f:
                f.write(tailwind_config)
            
            # Create postcss.config.js
            postcss_config = """
    module.exports = {
    plugins: {
        tailwindcss: {},
        autoprefixer: {},
    }
    }
    """
            
            with open(os.path.join(react_app_dir, "postcss.config.js"), 'w', encoding='utf-8') as f:
                f.write(postcss_config)
            
            # Create index.html
            index_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#000000" />
        <meta
        name="description"
        content="TSX Components Viewer"
        />
        <title>TSX Components Viewer</title>
    </head>
    <body>
        <noscript>You need to enable JavaScript to run this app.</noscript>
        <div id="root"></div>
    </body>
    </html>
    """
            
            with open(os.path.join(react_app_dir, "public", "index.html"), 'w', encoding='utf-8') as f:
                f.write(index_html)
            
            # Create index.css with Tailwind directives
            index_css = """
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
    """
            
            with open(os.path.join(react_app_dir, "src", "index.css"), 'w', encoding='utf-8') as f:
                f.write(index_css)
            
            # Create index.js
            index_js = """
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
    """
            
            with open(os.path.join(react_app_dir, "src", "index.js"), 'w', encoding='utf-8') as f:
                f.write(index_js)
            
            # Create App.js with component gallery using camelCase imports
            # Each import should use the camelCase name
            app_imports = "\n".join([f"import {camel_name} from './components/{camel_name}';" 
                                    for camel_name, _ in component_import_names])
            
            # Use camelCase names for the components object
            app_components_obj = ",\n    ".join([f'"{original_name}": {camel_name}' 
                                            for camel_name, original_name in component_import_names])
            
            # Use original names for display but camelCase names for the components
            app_components_options = "\n          ".join([f'<option key="{original_name}" value="{original_name}">{original_name}</option>' 
                                                    for _, original_name in component_import_names])
            
            # Use the first component's original name as the default
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
            
            with open(os.path.join(react_app_dir, "src", "App.js"), 'w', encoding='utf-8') as f:
                f.write(app_js)
            
            # Create README.md with instructions
            readme_md = f"""
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

    ## Available Scripts

    - `npm start`: Run the app in development mode
    - `npm build`: Build the app for production
    - `npm test`: Run tests
    - `npm eject`: Eject from Create React App
    """
            
            with open(os.path.join(react_app_dir, "README.md"), 'w', encoding='utf-8') as f:
                f.write(readme_md)
            
            # Create .gitignore
            gitignore = """
    # dependencies
    /node_modules
    /.pnp
    .pnp.js

    # testing
    /coverage

    # production
    /build

    # misc
    .DS_Store
    .env.local
    .env.development.local
    .env.test.local
    .env.production.local

    npm-debug.log*
    yarn-debug.log*
    yarn-error.log*
    """
            
            with open(os.path.join(react_app_dir, ".gitignore"), 'w', encoding='utf-8') as f:
                f.write(gitignore)
            
            # Create a ZIP file of the React app
            zip_path = os.path.join(self.temp_dir, "public", "tsx-components-viewer.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, dirs, files in os.walk(react_app_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, react_app_dir)
                        zipf.write(file_path, arcname)
            
            # Create HTML with download link
            download_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>React App Download</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                padding: 20px;
            }}
            h1 {{
                color: #333;
                margin-top: 0;
            }}
            .download-btn {{
                display: inline-block;
                background-color: #4CAF50;
                color: white;
                padding: 12px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .instructions {{
                background-color: #f8f9fa;
                border-left: 4px solid #6c757d;
                padding: 15px;
                margin: 20px 0;
            }}
            code {{
                background-color: #f1f1f1;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }}
            pre {{
                background-color: #f1f1f1;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>React App Generator</h1>
            
            <p>Your React application with the following components has been created:</p>
            <ul>
                {"".join(f"<li><code>{name}</code></li>" for name in component_names)}
            </ul>
            
            <a href="tsx-components-viewer.zip" class="download-btn" download>Download React App</a>
            
            <div class="instructions">
                <h2>Instructions:</h2>
                <ol>
                    <li>Download the ZIP file using the button above</li>
                    <li>Extract the ZIP file to a directory of your choice</li>
                    <li>Open a terminal/command prompt in that directory</li>
                    <li>Run the following commands:</li>
                </ol>
                
                <pre><code>npm install
    npm start</code></pre>
                
                <p>This will install all dependencies and start the development server.</p>
                <p>Once started, open <a href="http://localhost:3000" target="_blank">http://localhost:3000</a> in your browser to view the component gallery.</p>
            </div>
            
            <h2>What's Included:</h2>
            <ul>
                <li>React application setup with Create React App structure</li>
                <li>Tailwind CSS configuration</li>
                <li>Component gallery with dropdown selector</li>
                <li>All your TSX components</li>
            </ul>
            
            <p>The application is ready to run as-is, or you can modify it to suit your needs.</p>
        </div>
    </body>
    </html>
    """
            
            download_path = os.path.join(self.temp_dir, "public", "download-react-app.html")
            with open(download_path, 'w', encoding='utf-8') as f:
                f.write(download_html)
            
            # Open the download page
            self.status_bar.config(text="React application created successfully!")
            self.app_download_url = f"http://localhost:{self.port}/download-react-app.html"
            webbrowser.open(self.app_download_url)
            self.add_to_console(f"React app created and ready for download at: {self.app_download_url}")
            
        except Exception as e:
            self.status_bar.config(text=f"Error creating React app: {str(e)}")
            self.add_to_console(f"Error creating React app: {str(e)}")
            import traceback
            self.add_to_console(traceback.format_exc())
            messagebox.showerror("Error", f"Could not create React app: {str(e)}")

    def to_camel_case(self, name):
        """Convert hyphenated or snake_case names to CamelCase"""
        # Replace hyphens and underscores with spaces
        s = name.replace('-', ' ').replace('_', ' ')
        # Title case each word
        s = s.title()
        # Remove spaces
        s = s.replace(' ', '')
        return s

    def add_export_to_react_button(self):
        """Add an Export to React App button to the UI"""
        # This should be called in your __init__ method after other UI elements are created
        self.export_button = ttk.Button(
            self.main_frame, 
            text="Export to React App", 
            command=self.export_to_react_app
        )
        # Position it appropriately in your UI, for example:
        self.export_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def export_to_react_app(self):
        """Handle the export to React app button click"""
        # Check if any files have been opened/processed
        if not hasattr(self, 'current_file'):
            messagebox.showinfo("Information", "Please open at least one TSX file first.")
            return
        
        # For a more sophisticated implementation, you could maintain a list of opened files
        # For now, we'll just use the current file
        component_name = os.path.basename(self.current_file).split('.')[0]
        
        # Show a confirmation dialog
        result = messagebox.askyesno(
            "Export to React App", 
            f"Create a React application with the component: {component_name}?\n\n"
            "This will generate a downloadable React app with your component."
        )
        
        if result:
            self.create_react_app([(self.current_file, component_name)])


if __name__ == "__main__":
    # Check if Node.js and npm are installed - using a more Windows-friendly approach
    try:
        is_windows = os.name == 'nt'
        node_cmd = "node --version" if is_windows else ["node", "--version"]
        npm_cmd = "npm --version" if is_windows else ["npm", "--version"]
        
        node_version = subprocess.check_output(node_cmd, shell=is_windows).decode().strip()
        npm_version = subprocess.check_output(npm_cmd, shell=is_windows).decode().strip()
        
        print(f"Node.js version: {node_version}")
        print(f"npm version: {npm_version}")
    except Exception as e:
        print(f"Error detecting Node.js and npm: {str(e)}")
        print("Error: Node.js and npm are required to run this application.")
        print("Please install Node.js from https://nodejs.org/")
        sys.exit(1)
    
    root = tk.Tk()
    app = TSXRenderer(root)
    root.mainloop()