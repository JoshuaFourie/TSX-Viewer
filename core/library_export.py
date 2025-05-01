"""
Module for exporting components as a reusable component library
"""
import os
import json
import shutil
import subprocess
import logging
import platform
import time
from typing import List, Dict, Any, Callable, Optional, Set
import re

from core.component import Component

logger = logging.getLogger(__name__)

class LibraryExporter:
    """Class for exporting components as a reusable library"""
    
    def __init__(self, components: List[Component], progress_callback: Callable[[str], None]):
        """
        Initialize the library exporter
        
        Args:
            components: List of components to export
            progress_callback: Callback function for progress updates
        """
        self.components = components
        self.progress = progress_callback
        self.export_dir = None
        self.lib_dir = None
        self.all_dependencies = set()
    
    def export(self, export_dir: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Export components as a library
        
        Args:
            export_dir: Directory to export to
            options: Library options including name, version, etc.
            
        Returns:
            Path to the exported library
        """
        options = options or {}
        self.export_dir = export_dir
        self.lib_dir = os.path.join(export_dir, options.get('name', 'component-library'))
        
        try:
            # Validate options
            self._validate_options(options)
            
            # Create the library directory structure
            self._create_library_structure(options)
            
            # Scan dependencies
            self._scan_dependencies()
            
            # Copy and process components
            self._process_components(options)
            
            # Create package files
            self._create_package_files(options)
            
            # Create build configuration
            self._create_build_config(options)
            
            # Create index files
            self._create_index_files(options)
            
            # Set up Storybook
            if options.get('storybook', False):
                self._setup_storybook(options)
            
            return self.lib_dir
            
        except Exception as e:
            logger.error(f"Error exporting component library: {e}")
            self.progress(f"Error: {str(e)}")
            raise
    
    def _validate_options(self, options: Dict[str, Any]):
        """Validate export options"""
        # Set defaults for missing options
        if 'name' not in options:
            options['name'] = 'component-library'
        
        if 'version' not in options:
            options['version'] = '0.1.0'
        
        if 'typescript' not in options:
            options['typescript'] = True
        
        if 'build' not in options:
            options['build'] = 'rollup'
        
        if 'storybook' not in options:
            options['storybook'] = True
    
    def _create_library_structure(self, options: Dict[str, Any]):
        """Create the library directory structure"""
        self.progress("Creating library directory structure...")
        
        # Create main directories
        os.makedirs(self.lib_dir, exist_ok=True)
        os.makedirs(os.path.join(self.lib_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.lib_dir, "src", "components"), exist_ok=True)
        
        if options.get('storybook', False):
            os.makedirs(os.path.join(self.lib_dir, "stories"), exist_ok=True)
    
    def _scan_dependencies(self):
        """Scan components for dependencies"""
        self.progress("Scanning components for dependencies...")
        
        for component in self.components:
            deps = component.get_dependencies()
            self.all_dependencies.update(deps)
            
        self.progress(f"Found dependencies: {', '.join(self.all_dependencies) if self.all_dependencies else 'none'}")
    
    def _process_components(self, options: Dict[str, Any]):
        """Process and copy components to the library"""
        self.progress("Processing components...")
        
        self.component_data = []
        extension = ".tsx" if options.get('typescript', True) else ".jsx"
        
        for component in self.components:
            # Convert component name to camelCase for JavaScript
            camel_case_name = self._to_camel_case(component.name)
            
            # Create the file path
            file_path = os.path.join(self.lib_dir, "src", "components", f"{camel_case_name}{extension}")
            
            # Process the component content
            processed_content = self._process_component_content(component.content, options)
            
            # Write the component content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            # Store component info
            self.component_data.append({
                "originalName": component.name,
                "camelCaseName": camel_case_name,
                "filePath": file_path
            })
            
            # Create type definition file if using TypeScript
            if options.get('typescript', True):
                self._create_type_definition(component, camel_case_name)
            
            # Create story file if using Storybook
            if options.get('storybook', False):
                self._create_story_file(component, camel_case_name, options)
            
            self.progress(f"Added component: {component.name}")
    
    def _process_component_content(self, content: str, options: Dict[str, Any]) -> str:
        """
        Process component content for use in the library
        
        Args:
            content: Original component content
            options: Export options
            
        Returns:
            Processed component content
        """
        # Add library exports and imports
        # This is a simplified example - a real implementation would do more sophisticated processing
        
        # Look for existing imports
        import_section_end = content.find('\n\n')
        if import_section_end == -1:  # No double newline found
            import_section_end = content.find('\n')  # Try single newline
        
        if import_section_end > 0:
            # Split content into imports and component code
            imports = content[:import_section_end].strip()
            component_code = content[import_section_end:].strip()
            
            # Process imports if needed (e.g., adjust paths)
            processed_imports = imports
            
            # Return combined content
            return f"{processed_imports}\n\n{component_code}"
        
        # If we couldn't find imports, return the original content
        return content
    
    def _create_type_definition(self, component: Component, camel_case_name: str):
        """Create TypeScript type definition file for a component"""
        # This is a simplified placeholder implementation
        # A real implementation would analyze the component props and generate proper types
        
        type_def_content = """import { ReactNode } from 'react';

export interface ${ComponentName}Props {
  /** Optional children content */
  children?: ReactNode;
  /** Optional CSS class name */
  className?: string;
  /** Optional component style */
  style?: React.CSSProperties;
}

/**
 * ${ComponentName} component
 */
export declare function ${ComponentName}(props: ${ComponentName}Props): JSX.Element;
"""
        
        # Replace placeholders
        type_def_content = type_def_content.replace("${ComponentName}", camel_case_name)
        
        # Create the file
        type_def_path = os.path.join(self.lib_dir, "src", "components", f"{camel_case_name}.d.ts")
        with open(type_def_path, 'w', encoding='utf-8') as f:
            f.write(type_def_content)
    
    def _create_story_file(self, component: Component, camel_case_name: str, options: Dict[str, Any]):
        """Create a Storybook story file for a component"""
        extension = ".tsx" if options.get('typescript', True) else ".jsx"
        
        # Create a basic story
        story_content = f"""import React from 'react';
import {{ {camel_case_name} }} from '../src/components/{camel_case_name}';

export default {{
  title: 'Components/{camel_case_name}',
  component: {camel_case_name},
  parameters: {{
    layout: 'centered',
  }},
  tags: ['autodocs'],
}};

export const Default = () => (
  <{camel_case_name} />
);

export const WithCustomProps = () => (
  <{camel_case_name} className="custom-class" />
);
"""
        
        # Create the file
        story_path = os.path.join(self.lib_dir, "stories", f"{camel_case_name}.stories{extension}")
        with open(story_path, 'w', encoding='utf-8') as f:
            f.write(story_content)
    
    def _create_package_files(self, options: Dict[str, Any]):
        """Create package.json and related files"""
        self.progress("Creating package files...")
        
        # Create package.json
        self._create_package_json(options)
        
        # Create .gitignore
        gitignore_content = """# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# production
/dist
/build
/lib

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
        
        with open(os.path.join(self.lib_dir, ".gitignore"), 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        
        # Create README
        self._create_readme(options)
        
        # Create TypeScript configuration if applicable
        if options.get('typescript', True):
            self._create_typescript_config(options)
    
    def _create_package_json(self, options: Dict[str, Any]):
        """Create the package.json file"""
        package_name = options.get('name', 'component-library')
        version = options.get('version', '0.1.0')
        build_tool = options.get('build', 'rollup')
        use_typescript = options.get('typescript', True)
        use_storybook = options.get('storybook', False)
        
        # Determine main and types fields
        main_field = "dist/index.js"
        module_field = "dist/index.esm.js"
        types_field = "dist/index.d.ts" if use_typescript else None
        
        # Base dependencies
        dependencies = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        }
        
        # Add component dependencies
        for dep in self.all_dependencies:
            if dep not in dependencies and dep not in ["react", "react-dom"]:
                dependencies[dep] = "latest"
        
        # Dev dependencies based on build tool
        dev_dependencies = {
            "@types/react": "^18.2.15",
            "@types/react-dom": "^18.2.7",
        }
        
        # Add build tool dependencies
        if build_tool == 'rollup':
            dev_dependencies.update({
                "rollup": "^3.26.0",
                "@rollup/plugin-node-resolve": "^15.1.0",
                "@rollup/plugin-commonjs": "^25.0.2",
                "@rollup/plugin-babel": "^6.0.3",
                "@rollup/plugin-typescript": "^11.1.2" if use_typescript else None,
                "rollup-plugin-peer-deps-external": "^2.2.4",
                "rollup-plugin-terser": "^7.0.2",
            })
        else:  # webpack
            dev_dependencies.update({
                "webpack": "^5.88.1",
                "webpack-cli": "^5.1.4",
                "babel-loader": "^9.1.2",
                "ts-loader": "^9.4.4" if use_typescript else None,
            })
        
        # Filter out None values
        dev_dependencies = {k: v for k, v in dev_dependencies.items() if v is not None}
        
        # Add Babel dependencies
        dev_dependencies.update({
            "@babel/core": "^7.22.5",
            "@babel/preset-env": "^7.22.5",
            "@babel/preset-react": "^7.22.5",
            "@babel/preset-typescript": "^7.22.5" if use_typescript else None,
        })
        
        # Add Storybook dependencies if needed
        if use_storybook:
            dev_dependencies.update({
                "storybook": "^7.0.24",
                "@storybook/react": "^7.0.24",
                "@storybook/react-webpack5": "^7.0.24",
                "@storybook/blocks": "^7.0.24",
                "@storybook/addon-links": "^7.0.24",
                "@storybook/addon-essentials": "^7.0.24",
            })
        
        # Filter out None values again
        dev_dependencies = {k: v for k, v in dev_dependencies.items() if v is not None}
        
        # Create the package.json content
        package_json = {
            "name": package_name,
            "version": version,
            "description": "A library of React components",
            "main": main_field,
            "module": module_field,
            "types": types_field,
            "files": [
                "dist"
            ],
            "scripts": {
                "build": f"{'rollup -c' if build_tool == 'rollup' else 'webpack --mode production'}",
                "storybook": "storybook dev -p 6006" if use_storybook else None,
                "build-storybook": "storybook build" if use_storybook else None,
            },
            "keywords": [
                "react",
                "component",
                "library",
                "ui"
            ],
            "author": "",
            "license": "MIT",
            "dependencies": dependencies,
            "devDependencies": dev_dependencies,
            "peerDependencies": {
                "react": "^17.0.0 || ^18.0.0",
                "react-dom": "^17.0.0 || ^18.0.0"
            }
        }
        
        # Remove None values
        package_json["scripts"] = {k: v for k, v in package_json["scripts"].items() if v is not None}
        if types_field is None:
            del package_json["types"]
        
        # Write to file
        with open(os.path.join(self.lib_dir, "package.json"), 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2)
    
    def _create_typescript_config(self, options: Dict[str, Any]):
        """Create TypeScript configuration files"""
        # Create tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": True,
                "skipLibCheck": True,
                "esModuleInterop": True,
                "allowSyntheticDefaultImports": True,
                "strict": True,
                "forceConsistentCasingInFileNames": True,
                "module": "esnext",
                "moduleResolution": "node",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "react-jsx",
                "declaration": True,
                "declarationDir": "dist",
                "outDir": "dist"
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist", "**/*.stories.*"]
        }
        
        with open(os.path.join(self.lib_dir, "tsconfig.json"), 'w', encoding='utf-8') as f:
            json.dump(tsconfig, f, indent=2)
    
    def _create_build_config(self, options: Dict[str, Any]):
        """Create build configuration files based on the selected build tool"""
        build_tool = options.get('build', 'rollup')
        use_typescript = options.get('typescript', True)
        
        if build_tool == 'rollup':
            self._create_rollup_config(options)
        else:  # webpack
            self._create_webpack_config(options)
    
    def _create_rollup_config(self, options: Dict[str, Any]):
        """Create Rollup configuration file"""
        use_typescript = options.get('typescript', True)
        
        # Modified to avoid Pylance error with terser
        rollup_config = f"""import resolve from '@rollup/plugin-node-resolve';
    import commonjs from '@rollup/plugin-commonjs';
    import babel from '@rollup/plugin-babel';
    {f"import typescript from '@rollup/plugin-typescript';" if use_typescript else ""}
    import {{ terser }} from 'rollup-plugin-terser';  # noqa: F821
    import peerDepsExternal from 'rollup-plugin-peer-deps-external';
    import pkg from './package.json';

    export default {{
    input: 'src/index.{f"ts" if use_typescript else "js"}',
    output: [
        {{
        file: pkg.main,
        format: 'cjs',
        sourcemap: true,
        }},
        {{
        file: pkg.module,
        format: 'esm',
        sourcemap: true,
        }},
    ],
    plugins: [
        peerDepsExternal(),
        resolve(),
        commonjs(),
        {f"typescript({{}})," if use_typescript else ""}
        babel({{
        babelHelpers: 'bundled',
        exclude: 'node_modules/**',
        presets: [
            '@babel/preset-env',
            '@babel/preset-react',
            {f"'@babel/preset-typescript'," if use_typescript else ""}
        ],
        }}),
        terser(),
    ],
    external: Object.keys(pkg.peerDependencies || {{}})
    }};
    """
        
        with open(os.path.join(self.lib_dir, "rollup.config.js"), 'w', encoding='utf-8') as f:
            f.write(rollup_config)
    
    def _create_webpack_config(self, options: Dict[str, Any]):
        """Create Webpack configuration file"""
        use_typescript = options.get('typescript', True)
        
        webpack_config = f"""const path = require('path');

module.exports = {{
  mode: 'production',
  entry: './src/index.{f"ts" if use_typescript else "js"}',
  output: {{
    path: path.resolve(__dirname, 'dist'),
    filename: 'index.js',
    libraryTarget: 'umd',
    library: '{options.get("name", "component-library")}',
    umdNamedDefine: true,
    globalObject: 'this',
  }},
  resolve: {{
    extensions: ['.js', '.jsx'{f", '.ts', '.tsx'" if use_typescript else ""}],
  }},
  module: {{
    rules: [
      {f"""{{
        test: /\\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      }},""" if use_typescript else ""}
      {{
        test: /\\.jsx?$/,
        exclude: /node_modules/,
        use: {{
          loader: 'babel-loader',
          options: {{
            presets: [
              '@babel/preset-env',
              '@babel/preset-react',
              {f"'@babel/preset-typescript'," if use_typescript else ""}
            ],
          }},
        }},
      }},
    ],
  }},
  externals: {{
    react: 'React',
    'react-dom': 'ReactDOM',
  }},
}};
"""
        
        with open(os.path.join(self.lib_dir, "webpack.config.js"), 'w', encoding='utf-8') as f:
            f.write(webpack_config)
    
    def _create_index_files(self, options: Dict[str, Any]):
        """Create index files to export all components"""
        self.progress("Creating index files...")
        
        extension = ".ts" if options.get('typescript', True) else ".js"
        
        # Create index file in src directory
        index_content = []
        
        # Export each component
        for component_info in self.component_data:
            index_content.append(f"export {{ default as {component_info['camelCaseName']} }} from './components/{component_info['camelCaseName']}';")
        
        # Write to file
        with open(os.path.join(self.lib_dir, "src", f"index{extension}"), 'w', encoding='utf-8') as f:
            f.write("\n".join(index_content))
    
    def _setup_storybook(self, options: Dict[str, Any]):
        """Set up Storybook for the component library"""
        self.progress("Setting up Storybook...")
        
        # Create .storybook directory
        storybook_dir = os.path.join(self.lib_dir, ".storybook")
        os.makedirs(storybook_dir, exist_ok=True)
        
        # Create main.js
        main_js = f"""
module.exports = {{
  stories: ['../stories/**/*.stories.{f"tsx" if options.get("typescript", True) else "jsx"}'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
  ],
  framework: {{
    name: '@storybook/react-webpack5',
    options: {{}}
  }},
  docs: {{
    autodocs: true
  }}
}};
"""
        
        with open(os.path.join(storybook_dir, "main.js"), 'w', encoding='utf-8') as f:
            f.write(main_js)
        
        # Create preview.js
        preview_js = """
export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
};
"""
        
        with open(os.path.join(storybook_dir, "preview.js"), 'w', encoding='utf-8') as f:
            f.write(preview_js)
    
    def _create_readme(self, options: Dict[str, Any]):
        """Create a README.md file"""
        package_name = options.get('name', 'component-library')
        component_names = [comp["originalName"] for comp in self.component_data]
        
        readme = f"""# {package_name}

A library of reusable React components.

## Installation

```bash
npm install {package_name}
# or
yarn add {package_name}
```

## Components

{chr(10).join(f"- {name}" for name in component_names)}

## Usage

```jsx
import {{ {", ".join(comp["camelCaseName"] for comp in self.component_data)} }} from '{package_name}';

function App() {{
  return (
    <div>
      <{self.component_data[0]["camelCaseName"] if self.component_data else "Component"} />
    </div>
  );
}}
```

## Development

1. Clone the repository
2. Install dependencies: `npm install`
3. Build the library: `npm run build`
{f"4. Run Storybook: `npm run storybook`" if options.get("storybook", False) else ""}

## License

MIT
"""
        
        with open(os.path.join(self.lib_dir, "README.md"), 'w', encoding='utf-8') as f:
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
def export_component_library(components, progress_callback, export_dir, options=None):
    """
    Export components as a reusable library
    
    Args:
        components: List of components to export
        progress_callback: Function to report progress
        export_dir: Directory to export to
        options: Library options
    
    Returns:
        Path to the exported library
    """
    exporter = LibraryExporter(components, progress_callback)
    return exporter.export(export_dir, options)