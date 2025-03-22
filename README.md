# Code Cognitio

A semantic search system for code repositories.

## Overview

Code Cognitio extracts, processes, and indexes code from various programming languages to create a semantic search engine. It allows you to find relevant code snippets and documentation by searching for concepts rather than just exact text matches.

## Features

- Extract code structure from multiple languages (Python, JavaScript, TypeScript)
- Parse documentation files (Markdown, reStructuredText)
- Process text with advanced NLP techniques
- Build and query semantic search indexes

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/code-cognitio.git
   cd code-cognitio
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   # Install uv first
   pip install uv
   # Then use uv to install requirements
   uv pip install -r requirements.txt
   ```

## Usage

```bash
# Build an index from source files
python -m src.main build path/to/repo --file-types=py,js,md

# Search the index
python -m src.main search "how to implement auth"
```

### VS Code Extension

Code Cognitio includes a standalone VS Code extension that provides an integrated semantic search experience in your development environment:

- **Completely standalone** - no need for Python in your workspace
- Automatic setup of its own Python environment
- Persistent index storage across workspaces
- Build search index directly from VS Code
- Search using natural language queries with advanced filtering
- View and navigate to results in a dedicated panel

### Installation for VS Code

1. Download the latest `.vsix` file from the [releases page](https://github.com/bivav/code-cognitio/releases)
2. Install in VS Code:
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Click on the "..." (More Actions) button
   - Select "Install from VSIX..."
   - Choose the downloaded `.vsix` file

### Usage in VS Code

- **Build Index**: Use the "Code Cognitio: Build Search Index" command to index your workspace
- **Search**: Use the "Code Cognitio: Search Code" command to search your codebase
- **View Results**: Results appear in the Code Cognitio panel in the Activity Bar

For more details, see [VS Code Extension Documentation](docs/vscode_extension.md).

## Development

### Setup

```bash
# Install development dependencies
make dev
```

### Common Development Commands

We've added several helpful commands to the Makefile to streamline development:

```bash
# Run all tests
make test

# Run specific test categories
make test-extractors
make test-processors
make test-search
make test-integration

# Generate test coverage report
make coverage
make coverage-html  # HTML report in htmlcov/

# Format, lint, test, and package everything in one step
make ready

# Extension-specific commands
make copy-python-src    # Copy Python source into the extension
make extension-compile  # Compile the TypeScript code
make extension-package  # Package the extension as a VSIX file
make extension-setup    # Set up the extension's Python environment
make extension-test     # Run a simple test of the extension
make extension-clean    # Clean extension build artifacts
```

### Testing

We have a comprehensive test suite covering extractors, processors, and the search engine.

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type checking
make typecheck
```

## Project Structure

```bash
code-cognitio/
├── src/              # Main Python source code
├── tests/            # Test files
├── extension/        # VS Code Extension
│   ├── src/          # TypeScript source for the extension
│   ├── python/       # Bundled Python code used by the extension
│   └── out/          # Compiled JavaScript files
├── Makefile          # Build and test automation
└── README.md         # This file
```

The project is organized into several key directories:

- `src/`: Contains the core Python code for the semantic search engine
- `tests/`: Contains unit and integration tests
- `extension/`: Contains the VS Code extension code
  - `extension/src/`: TypeScript source code for the extension
  - `extension/python/`: Bundled Python code that allows the extension to run independently of the workspace
  - `extension/out/`: Compiled JavaScript output

### Why the Extension Bundles Python Code

The VS Code extension includes a copy of the Python code from the main source tree that is automatically copied during the packaging process. This approach:

- Maintains a single source of truth (the main `src/` directory)
- Automatically includes the latest code when the extension is packaged
- Allows the extension to run independently once installed
- Ensures users don't need to install anything in their workspace

**For developers:**

- Edit only the code in the main `src/` directory
- The build process copies this code into the extension package
- No manual syncing is required

This architecture ensures consistent functionality while avoiding code duplication during development.

## License

[MIT License](LICENSE)
