"""
Module for exporting components to React applications
"""
import os
import json
import shutil
import subprocess
import logging
import platform
import threading
import time
from typing import List, Dict, Any, Callable, Optional, Set
import tempfile
import re

from core.component import Component

logger = logging.getLogger(__name__)

class ReactExporter:
    """Class for exporting components to a React application"""
    
    def __init__(self, components: List[Component], progress_callback: Callable[[str], None]):
        """
        Initialize the React exporter
        
        Args:
            components: List of components to export
            progress_callback: Callback function for progress updates
        """
        self.components = components
        self.progress = progress_callback
        self.export_dir = None
        self.app_dir = None
        self.temp_dir = None
        self.all_dependencies = set()
    
    def export(self, export_dir: str, options: Optional[Dict[str, Any]] = None, run_app: bool = False) -> str:
        """
        Export components to a React application
        
        Args:
            export_dir: Directory to export to
            options: Optional export options
            run_app: Whether to run the app after export
            
        Returns:
            Path to the exported application
        """
        options = options or {}
        self.export_dir = export_dir
        self.app_dir = os.path.join(export_dir, options.get('app_name', 'tsx-components-app'))
        
        try:
            # Create app directory
            os.makedirs(self.app_dir, exist_ok=True)
            
            # Set up project structure
            self._create_project_structure()
            
            # Scan dependencies
            self._scan_dependencies()
            
            # Copy components
            self._copy_components()
            
            # Create configuration files
            self._create_configuration_files(options)
            
            # Create app files
            self._create_app_files()
            
            # Install dependencies
            if run_app:
                self._install_dependencies()
                self._run_app()
                
            return self.app_dir
            
        except Exception as e:
            logger.error(f"Error exporting React app: {e}")
            self.progress(f"Error: {str(e)}")
            raise
    
    def _create_project_structure(self):
        """Create the basic project directory structure"""
        self.progress("Creating project structure...")
        
        # Create directories
        os.makedirs(os.path.join(self.app_dir, "public"), exist_ok=True)
        os.makedirs(os.path.join(self.app_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.app_dir, "src", "components"), exist_ok=True)
    
    def _scan_dependencies(self):
        """Scan components for dependencies"""
        self.progress("Scanning components for dependencies...")
        
        for component in self.components:
            deps = component.get_dependencies()
            self.all_dependencies.update(deps)
            
        self.progress(f"Found dependencies: {', '.join(self.all_dependencies) if self.all_dependencies else 'none'}")
    
    def _copy_components(self):
        """Copy components to the app directory"""
        self.progress("Copying components...")
        
        self.component_data = []
        
        for component in self.components:
            # Convert component name to camelCase for JavaScript
            camel_case_name = self._to_camel_case(component.name)
            
            # Determine file extension (.jsx or .tsx)
            extension = ".tsx" if component.extension.lower() == ".tsx" else ".jsx"
            
            # Create the file path
            file_path = os.path.join(self.app_dir, "src", "components", f"{camel_case_name}{extension}")
            
            # Write the component content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(component.content)
            
            # Store component info
            self.component_data.append({
                "originalName": component.name,
                "camelCaseName": camel_case_name,
                "filePath": file_path
            })
            
            self.progress(f"Added component: {component.name}")
    
    def _create_configuration_files(self, options: Dict[str, Any]):
        """Create configuration files for the React app"""
        self.progress("Creating configuration files...")
        
        # Build package.json
        self._create_package_json(options)
        
        # Create index.html
        self._create_index_html(options)
        
        # Create tailwind config if enabled
        if options.get('tailwind', True):
            self._create_tailwind_config()
    
    def _create_package_json(self, options: Dict[str, Any]):
        """Create the package.json file"""
        # Base dependencies
        dependencies = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
        }
        
        # Add UI libraries
        if options.get('tailwind', True):
            dependencies["tailwindcss"] = "^3.3.3"
        
        if options.get('ui_library') == 'mui':
            dependencies["@mui/material"] = "^5.14.5"
            dependencies["@mui/icons-material"] = "^5.14.5"
            dependencies["@emotion/react"] = "^11.11.1"
            dependencies["@emotion/styled"] = "^11.11.0"
        elif options.get('ui_library') == 'chakra':
            dependencies["@chakra-ui/react"] = "^2.8.0"
            dependencies["@emotion/react"] = "^11.11.1"
            dependencies["@emotion/styled"] = "^11.11.0"
            dependencies["framer-motion"] = "^10.16.1"
        
        # Include Lucide if detected or specified
        if 'lucide-react' in self.all_dependencies or options.get('include_lucide', True):
            dependencies["lucide-react"] = "^0.279.0"
        
        # Add other detected dependencies
        for dep in self.all_dependencies:
            if dep not in dependencies and dep not in ["react", "react-dom"]:
                dependencies[dep] = "latest"
        
        # Create the package.json content
        package_json = {
            "name": options.get('app_name', 'tsx-components-app'),
            "version": options.get('version', '0.1.0'),
            "private": True,
            "dependencies": dependencies,
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
                "react-scripts": "5.0.1"
            }
        }
        
        # Add tailwind dev dependencies
        if options.get('tailwind', True):
            package_json["devDependencies"].update({
                "tailwindcss": "^3.3.3",
                "autoprefixer": "^10.4.14", 
                "postcss": "^8.4.24"
            })
        
        # Write to file
        with open(os.path.join(self.app_dir, "package.json"), 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2)
    
    def _create_index_html(self, options: Dict[str, Any]):
        """Create the index.html file"""
        app_name = options.get('app_name', 'TSX Components App')
        
        index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{app_name}" />
    <title>{app_name}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
"""
        
        with open(os.path.join(self.app_dir, "public", "index.html"), 'w', encoding='utf-8') as f:
            f.write(index_html)
    
    def _create_tailwind_config(self):
        """Create Tailwind CSS configuration files"""
        # tailwind.config.js
        tailwind_config = """/** @type {import('tailwindcss').Config} */
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
        
        with open(os.path.join(self.app_dir, "tailwind.config.js"), 'w', encoding='utf-8') as f:
            f.write(tailwind_config)
        
        # postcss.config.js
        postcss_config = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  }
}
"""
        
        with open(os.path.join(self.app_dir, "postcss.config.js"), 'w', encoding='utf-8') as f:
            f.write(postcss_config)
        
        # index.css with Tailwind directives
        index_css = """@tailwind base;
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
        
        with open(os.path.join(self.app_dir, "src", "index.css"), 'w', encoding='utf-8') as f:
            f.write(index_css)
    
    def _create_app_files(self):
        """Create the main application files"""
        self.progress("Creating application files...")
        
        # Create index.js
        index_js = """import React from 'react';
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
        
        with open(os.path.join(self.app_dir, "src", "index.js"), 'w', encoding='utf-8') as f:
            f.write(index_js)
        
        # Create App.js with component gallery
        self._create_app_js()
        
        # Create README.md
        self._create_readme()
    
    def _create_app_js(self):
        """Create the App.js file with a component gallery"""
        self.progress("Creating App.js with component gallery...")
        
        # Prepare imports
        imports = []
        components_obj = []
        dropdown_options = []
        
        for comp in self.component_data:
            # Create import statement
            import_path = f"./components/{comp['camelCaseName']}"
            imports.append(f"import {comp['camelCaseName']} from '{import_path}';")
            
            # Add to components object
            components_obj.append(f'"{comp["originalName"]}": {comp["camelCaseName"]}')
            
            # Add to dropdown options
            dropdown_options.append(
                f'<option key="{comp["originalName"]}" value="{comp["originalName"]}">'
                f'{comp["originalName"]}</option>'
            )
        
        # Default component (first one)
        first_component = self.component_data[0]["originalName"] if self.component_data else ""
        
        # Create the App.js content
        app_js = f"""import React, {{ useState }} from 'react';
{chr(10).join(imports)}

function App() {{
  const [activeComponent, setActiveComponent] = useState('{first_component}');
  
  const components = {{
    {",\\n    ".join(components_obj)}
  }};
  
  const ActiveComponent = components[activeComponent];
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">Component Gallery</h1>
      
      <div className="mb-6">
        <label className="block mb-2 font-semibold">Select a Component:</label>
        <select 
          className="border border-gray-300 rounded px-3 py-2 w-full"
          value={{activeComponent}}
          onChange={{(e) => setActiveComponent(e.target.value)}}
        >
          {chr(10).join(dropdown_options)}
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
        
        with open(os.path.join(self.app_dir, "src", "App.js"), 'w', encoding='utf-8') as f:
            f.write(app_js)
    
    def _create_readme(self):
        """Create the README.md file"""
        component_names = [comp["originalName"] for comp in self.component_data]
        
        readme = f"""# Component Gallery

This is a React application that displays a collection of components.

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

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App
"""
        
        with open(os.path.join(self.app_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme)
    
    def _install_dependencies(self):
        """Install npm dependencies"""
        self.progress("\nInstalling dependencies (this may take a few minutes)...")
        
        # Determine if we're on Windows
        is_windows = platform.system() == 'Windows'
        
        try:
            # Run npm install
            process = subprocess.Popen(
                "npm install" if is_windows else ["npm", "install"],
                cwd=self.app_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=is_windows
            )
            
            # Monitor the installation progress
            while True:
                output = process.stdout.readline()
                if not output and process.poll() is not None:
                    break
                if output:
                    self.progress(output.decode('utf-8').strip())
            
            # Check for errors
            if process.returncode != 0:
                error = process.stderr.read().decode('utf-8')
                self.progress(f"Error during npm install: {error}")
                raise Exception(f"npm install failed with code {process.returncode}")
                
            self.progress("Dependencies installed successfully!")
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            self.progress(f"Error installing dependencies: {str(e)}")
            raise
    
    def _run_app(self):
        """Start the React development server"""
        self.progress("\nStarting development server...")
        
        # Determine if we're on Windows
        is_windows = platform.system() == 'Windows'
        
        try:
            # Run npm start
            process = subprocess.Popen(
                "npm start" if is_windows else ["npm", "start"],
                cwd=self.app_dir,
                shell=is_windows
            )
            
            # Wait a bit to let the server start
            self.progress("Waiting for server to start...")
            time.sleep(5)
            
            self.progress("\nReact application has been exported and started!")
            self.progress(f"Location: {self.app_dir}")
            self.progress("The React development server should open in your browser.")
            self.progress("If not, open http://localhost:3000 manually.")
            
        except Exception as e:
            logger.error(f"Error starting React app: {e}")
            self.progress(f"Error starting app: {str(e)}")
            raise
    
    def _to_camel_case(self, name: str) -> str:
        """Convert a string to camelCase for component names"""
        # Replace hyphens and underscores with spaces
        s = name.replace('-', ' ').replace('_', ' ')
        # Title case each word and join without spaces
        words = s.split()
        if not words:
            return ''
        # First word lowercase, rest capitalized
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])


# Helper function to be called from the main application
def export_react_app(components, progress_callback, export_dir, options=None, run_app=False):
    """
    Export components to a React application
    
    Args:
        components: List of components to export
        progress_callback: Function to report progress
        export_dir: Directory to export to
        options: Export options
        run_app: Whether to run the app after export
    
    Returns:
        Path to the exported application
    """
    exporter = ReactExporter(components, progress_callback)
    return exporter.export(export_dir, options, run_app)