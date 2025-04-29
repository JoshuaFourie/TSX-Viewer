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
cd tsx-component-renderer
```

2. (Optional) Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Verify Node.js and npm:
```bash
node --version
npm --version
```

4. Run the application:
```bash
python tsx_renderer.py
```

### Troubleshooting

- If you encounter tkinter-related issues, ensure you've installed the tk package for your Python distribution
- For Node.js, make sure it's in your system PATH

## Usage

Run the application:
```bash
python tsx_renderer.py
```

### Key Functions

- **Select TSX File**: Open and preview your React TypeScript components
- **Open in Browser**: View your component in a live webpack development server
- **Export to React App**: Generate a complete, standalone React application with your components

## How It Works

The TSX Component Renderer uses:
- Tkinter for the desktop application UI
- Webpack for development server and compilation
- Python subprocess to manage npm and webpack processes

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

Project Link: https://github.com/JoshuaFourie/TSX-Viewer 