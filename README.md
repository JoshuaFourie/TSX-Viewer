TSX Component Manager
A powerful desktop application for managing, editing, and exporting React TSX/JSX components. Create, modify, and export components as complete React applications, Next.js apps, or reusable component libraries.
Features
Component Management

Multi-Component Projects - Add, edit, and organize multiple components
Project Saving - Save and load your component projects for continued work
Component Operations - Rename, duplicate, and remove components with ease

Advanced Code Editing

Syntax Highlighting - Full React/TSX syntax highlighting
Search & Replace - Powerful text search and replace functionality
Auto-formatting - Format your code with a single click
Auto-completion - Brackets and quote auto-closing
Line Numbers - Visual line reference for easier editing

Powerful Export Options

React Application - Export as complete, ready-to-run React apps
Next.js Application - Export to Next.js with App Router or Pages Router
Component Library - Package components as reusable NPM libraries
Storybook Integration - Optional Storybook setup for component documentation

Installation
Prerequisites

Python 3.8+ with tkinter
Node.js 16+ and npm

Setup
bash# Clone the repository
git clone https://github.com/JoshuaFourie/TSX-Viewer.git
cd TSX-Viewer

# Optional: Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Run the application
python main.py
Usage
Adding Components

Click the "Add Component" button in the header
Select one or more TSX/JSX files
Components appear in the component list panel

Editing Components

Select a component from the list
Use the enhanced code editor with syntax highlighting
Save changes with the "Save" button or Ctrl+S

Managing Projects

Save Project: File > Save Project
Open Project: File > Open Project
Recent Projects: Access recently opened projects from the File menu

Export Options
React Application
Export your components as a complete, functioning React application:

Automatic dependency detection
Tailwind CSS integration
Component gallery with selector
Option to run immediately after export

Next.js Application
Package your components as a Next.js application:

Choose between App Router and Pages Router
TypeScript or JavaScript
Automatic page creation for each component
Navigation between components

Component Library
Create a publishable component library:

Rollup or Webpack bundling
TypeScript definitions
Storybook documentation
Ready for NPM publishing

Development
The application is structured into modules for better maintainability:
tsx_component_manager/
├── __init__.py
├── main.py               # Main entry point
├── ui/                   # User interface modules
│   ├── main_window.py    # Main application window
│   ├── component_list.py # Component list management
│   ├── code_editor.py    # Code editing functionality
│   └── console.py        # Console output
├── core/                 # Core functionality
│   ├── component.py      # Component class and operations
│   ├── react_export.py   # React export functionality
│   ├── nextjs_export.py  # Next.js export functionality
│   └── library_export.py # Component library export
└── utils/                # Utilities
    ├── file_utils.py     # File operations
    └── npm_utils.py      # NPM interaction
Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the repository
Create your feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add some amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request

License
This project is licensed under the MIT License - see the LICENSE file for details.