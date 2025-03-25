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

# Format, lint, test in one step
make ready
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
├── docs/            # Documentation
├── data/            # Data files
├── examples/        # Example code
├── Makefile         # Build and test automation
└── README.md        # This file
```

The project is organized into several key directories:

- `src/`: Contains the core Python code for the semantic search engine
- `tests/`: Contains unit and integration tests
- `docs/`: Contains project documentation
- `data/`: Contains data files used by the project
- `examples/`: Contains example code and usage patterns

## License

[MIT License](LICENSE)
