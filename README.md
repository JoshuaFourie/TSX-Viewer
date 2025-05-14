# TSX Component Renderer

## Overview

TSX Component Renderer is a powerful desktop application that helps developers preview, analyze, and export React TypeScript (TSX) components with ease. Built with Python and Tkinter, this tool provides a comprehensive environment for working with React components.

## Features

- 🔍 Render and preview TSX components
- 📋 Code view with syntax highlighting
- 🌐 Integrated webpack development server
- 🚀 One-click export to a full React application
- 🧩 Automatic dependency detection
- 💻 Cross-platform support (Windows, macOS, Linux)

## Prerequisites

- Python 3.8+ with tkinter
  - Windows/macOS: Usually pre-installed
  - Linux: May need to install via package manager
    - Ubuntu/Debian: `sudo apt-get install python3-tk`
    - Fedora: `sudo dnf install python3-tkinter`
    - Arch: `sudo pacman -S tk`
- Node.js 16+ and npm
  - Download from: https://nodejs.org/

## Installation

1. Clone the repository:
```bash
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

__init__.py
main.py               # Main entry point
ui/                   # User interface modules
├── main_window.py    # Main application window
├── component_list.py # Component list management
├── code_editor.py    # Code editing functionality
└── console.py        # Console output
core/                 # Core functionality
├── component.py      # Component class and operations
├── react_export.py   # React export functionality
├── nextjs_export.py  # Next.js export functionality
└── library_export.py # Component library export
utils/                # Utilities
├── file_utils.py     # File operations
└── npm_utils.py      # NPM interaction

Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the repository
Create your feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add some amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

Project Link: https://github.com/JoshuaFourie/TSX-Viewer 