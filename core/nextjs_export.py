"""
Module for exporting components to Next.js applications
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

class NextJSExporter:
    """Class for exporting components to a Next.js application"""
    
    def __init__(self, components: List[Component], progress_callback: Callable[[str], None]):
        """
        Initialize the Next.js exporter
        
        Args:
            components: List of components to export
            progress_callback: Callback function for progress updates
        """
        self.components = components
        self.progress = progress_callback
        self.export_dir = None
        self.app_dir = None
        self.all_dependencies = set()
    
    def export(self, export_dir: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Export components to a Next.js application
        
        Args:
            export_dir: Directory to export to
            options: Export options including Next.js version, router type, etc.
            
        Returns:
            Path to the exported application
        """
        options = options or {}
        self.export_dir = export_dir
        self.app_dir = os.path.join(export_dir, options.get('app_name', 'nextjs-components-app'))
        
        try:
            # Validate options
            self._validate_options(options)
            
            # Use npx create-next-app to create the Next.js application
            self._create_nextjs_app(options)
            
            # Scan dependencies
            self._scan_dependencies()
            
            # Copy components
            self._copy_components(options)
            
            # Create pages or app routes based on router type
            self._create_routes(options)
            
            # Create layout and theme files
            self._create_layout_files(options)
            
            # Update package.json with additional dependencies
            self._update_package_json(options)
            
            # Create README
            self._create_readme()
            
            return self.app_dir
            
        except Exception as e:
            logger.error(f"Error exporting Next.js app: {e}")
            self.progress(f"Error: {str(e)}")
            raise
    
    def _validate_options(self, options: Dict[str, Any]):
        """Validate export options"""
        # Set defaults for missing options
        if 'version' not in options:
            options['version'] = '13.4.12'
        
        if 'router' not in options:
            options['router'] = 'app'
        
        if 'typescript' not in options:
            options['typescript'] = True
        
        if 'tailwind' not in options:
            options['tailwind'] = True
    
    def _create_nextjs_app(self, options: Dict[str, Any]):
        """Create a new Next.js application using npx create-next-app"""
        self.progress("Creating Next.js application...")
        
        # Build the command for creating a Next.js app
        cmd_parts = ["npx", "create-next-app@latest", self.app_dir]
        
        # Add options
        if options.get('typescript', True):
            cmd_parts.append("--typescript")
        else:
            cmd_parts.append("--no-typescript")
        
        if options.get('eslint', True):
            cmd_parts.append("--eslint")
        else:
            cmd_parts.append("--no-eslint")
        
        if options.get('tailwind', True):
            cmd_parts.append("--tailwind")
        else:
            cmd_parts.append("--no-tailwind")
        
        # Specify app router or pages router
        if options.get('router') == 'app':
            cmd_parts.append("--app")
        else:
            cmd_parts.append("--no-app")
        
        # Create the Next.js app
        self.progress(f"Running command: {' '.join(cmd_parts)}")
        
        # Determine if we're on Windows
        is_windows = platform.system() == 'Windows'
        
        try:
            # Use shell=True on Windows to ensure npx is found
            process = subprocess.Popen(
                ' '.join(cmd_parts) if is_windows else cmd_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=is_windows
            )
            
            # Monitor the process
            while True:
                output = process.stdout.readline()
                if not output and process.poll() is not None:
                    break
                if output:
                    self.progress(output.decode('utf-8').strip())
            
            # Check for errors
            if process.returncode != 0:
                error = process.stderr.read().decode('utf-8')
                self.progress(f"Error creating Next.js app: {error}")
                raise Exception(f"create-next-app failed with code {process.returncode}")
            
            self.progress("Next.js application created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating Next.js app: {e}")
            self.progress(f"Error creating Next.js app: {str(e)}")
            raise
    
    def _scan_dependencies(self):
        """Scan components for dependencies"""
        self.progress("Scanning components for dependencies...")
        
        for component in self.components:
            deps = component.get_dependencies()
            self.all_dependencies.update(deps)
            
        self.progress(f"Found dependencies: {', '.join(self.all_dependencies) if self.all_dependencies else 'none'}")
    
    def _copy_components(self, options: Dict[str, Any]):
        """Copy components to the app directory"""
        self.progress("Copying components...")
        
        # Determine the components directory based on project structure
        if options.get('router') == 'app':
            components_dir = os.path.join(self.app_dir, "components")
        else:
            components_dir = os.path.join(self.app_dir, "components")
        
        # Create directory if it doesn't exist
        os.makedirs(components_dir, exist_ok=True)
        
        self.component_data = []
        extension = ".tsx" if options.get('typescript', True) else ".jsx"
        
        for component in self.components:
            # Convert component name to camelCase for JavaScript
            camel_case_name = self._to_camel_case(component.name)
            
            # Create the file path
            file_path = os.path.join(components_dir, f"{camel_case_name}{extension}")
            
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
    
    def _create_routes(self, options: Dict[str, Any]):
        """Create routes for the components"""
        self.progress("Creating routes...")
        
        # Handle different router types
        if options.get('router') == 'app':
            self._create_app_router_routes(options)
        else:
            self._create_pages_router_routes(options)
    
    def _create_app_router_routes(self, options: Dict[str, Any]):
        """Create routes using the App Router"""
        extension = ".tsx" if options.get('typescript', True) else ".jsx"
        
        # Create the app directory if it doesn't exist
        app_dir = os.path.join(self.app_dir, "app")
        os.makedirs(app_dir, exist_ok=True)
        
        # Create a route for each component
        for component_info in self.component_data:
            route_dir = os.path.join(app_dir, component_info["originalName"].lower())
            os.makedirs(route_dir, exist_ok=True)
            
            # Create page.tsx file
            page_content = self._create_component_page_content(component_info, options, True)
            page_path = os.path.join(route_dir, f"page{extension}")
            
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(page_content)
        
        # Update the main page to list all components
        self._create_app_index_page(options)
    
    def _create_pages_router_routes(self, options: Dict[str, Any]):
        """Create routes using the Pages Router"""
        extension = ".tsx" if options.get('typescript', True) else ".jsx"
        
        # Create the pages directory if it doesn't exist
        pages_dir = os.path.join(self.app_dir, "pages")
        os.makedirs(pages_dir, exist_ok=True)
        
        # Create a page for each component
        for component_info in self.component_data:
            page_content = self._create_component_page_content(component_info, options, False)
            page_path = os.path.join(pages_dir, f"{component_info['originalName'].toLowerCase()}{extension}")
            
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(page_content)
        
        # Update the index page to list all components
        self._create_pages_index_page(options)
    
    def _create_component_page_content(self, component_info, options, is_app_router):
        """Create the content for a component page"""
        # Different imports for App Router vs Pages Router
        use_typescript = options.get('typescript', True)
        
        if is_app_router:
            imports = [
                f"import {component_info['camelCaseName']} from '@/components/{component_info['camelCaseName']}'",
                "import Link from 'next/link'"
            ]
            
            # TypeScript type for app router
            ts_type = "export default function Page()" if use_typescript else "export default function Page()"
            
        else:
            imports = [
                f"import {component_info['camelCaseName']} from '../components/{component_info['camelCaseName']}'",
                "import Link from 'next/link'",
                "import Head from 'next/head'"
            ]
            
            # TypeScript type for pages router
            ts_type = "export default function ComponentPage()" if use_typescript else "export default function ComponentPage()"
        
        # Create the page content
        page_content = f"""
{chr(10).join(imports)}

{ts_type} {{
  return (
    <div className="container mx-auto px-4 py-8">
      <Link href="/" className="text-blue-500 hover:underline mb-4 inline-block">
        ← Back to all components
      </Link>
      
      <h1 className="text-3xl font-bold mb-6">{component_info['originalName']}</h1>
      
      <div className="border border-gray-300 rounded-lg p-6 bg-white">
        <{component_info['camelCaseName']} />
      </div>
    </div>
  )
}}
"""
        
        return page_content
    
    def _create_app_index_page(self, options):
        """Create the index page for App Router"""
        extension = ".tsx" if options.get('typescript', True) else ".jsx"
        
        # Get the list of components
        component_links = []
        for component_info in self.component_data:
            component_links.append(
                f'<li key="{component_info["originalName"]}" className="mb-2">\n'
                f'  <Link href="/{component_info["originalName"].lower()}" '
                f'className="text-blue-500 hover:underline">\n'
                f'    {component_info["originalName"]}\n'
                f'  </Link>\n'
                f'</li>'
            )
        
        # Create the page content
        index_content = f"""
import Link from 'next/link'

export default function Home() {{
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Component Gallery</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Available Components</h2>
        
        <ul className="list-disc pl-6">
          {chr(10).join(component_links)}
        </ul>
      </div>
    </div>
  )
}}
"""
        
        # Write to file
        page_path = os.path.join(self.app_dir, "app", f"page{extension}")
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
    
    def _create_pages_index_page(self, options):
        """Create the index page for Pages Router"""
        extension = ".tsx" if options.get('typescript', True) else ".jsx"
        
        # Get the list of components
        component_links = []
        for component_info in self.component_data:
            component_links.append(
                f'<li key="{component_info["originalName"]}" className="mb-2">\n'
                f'  <Link href="/{component_info["originalName"].toLowerCase()}">\n'
                f'    <a className="text-blue-500 hover:underline">{component_info["originalName"]}</a>\n'
                f'  </Link>\n'
                f'</li>'
            )
        
        # Create the page content
        index_content = f"""
import Head from 'next/head'
import Link from 'next/link'

export default function Home() {{
  return (
    <div className="container mx-auto px-4 py-8">
      <Head>
        <title>Component Gallery</title>
        <meta name="description" content="Gallery of components" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <h1 className="text-3xl font-bold mb-6">Component Gallery</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Available Components</h2>
        
        <ul className="list-disc pl-6">
          {chr(10).join(component_links)}
        </ul>
      </div>
    </div>
  )
}}
"""
        
        # Write to file
        page_path = os.path.join(self.app_dir, "pages", f"index{extension}")
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
    
    def _create_layout_files(self, options):
        """Create layout files for the application"""
        self.progress("Creating layout files...")
        
        # Only needed for App Router
        if options.get('router') == 'app':
            extension = ".tsx" if options.get('typescript', True) else ".jsx"
            
            # Create layout file
            layout_content = """
import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Component Gallery',
  description: 'A gallery of React components',
}

export default function RootLayout({
  children,
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
"""
            
            # Write to file
            layout_path = os.path.join(self.app_dir, "app", f"layout{extension}")
            with open(layout_path, 'w', encoding='utf-8') as f:
                f.write(layout_content)
    
    def _update_package_json(self, options):
        """Update package.json with additional dependencies"""
        self.progress("Updating package.json...")
        
        # Read existing package.json
        package_json_path = os.path.join(self.app_dir, "package.json")
        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        # Add component dependencies
        for dep in self.all_dependencies:
            if dep not in package_data.get('dependencies', {}):
                package_data.setdefault('dependencies', {})[dep] = "latest"
                self.progress(f"Added dependency: {dep}")
        
        # Write updated package.json
        with open(package_json_path, 'w', encoding='utf-8') as f:
            json.dump(package_data, f, indent=2)
    
    def _create_readme(self):
        """Create a README.md file"""
        component_names = [comp["originalName"] for comp in self.component_data]
        
        readme = f"""# Next.js Component Gallery

A gallery of React components built with Next.js.

## Included Components

{chr(10).join(f"- {name}" for name in component_names)}

## Getting Started

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) to view the application.

## Available Scripts

- `npm run dev` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm start` - Runs the built app in production mode
- `npm run lint` - Lints the codebase
"""
        
        with open(os.path.join(self.app_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme)
    
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
def export_nextjs_app(components, progress_callback, export_dir, options=None):
    """
    Export components to a Next.js application
    
    Args:
        components: List of components to export
        progress_callback: Function to report progress
        export_dir: Directory to export to
        options: Export options
    
    Returns:
        Path to the exported application
    """
    exporter = NextJSExporter(components, progress_callback)
    return exporter.export(export_dir, options)