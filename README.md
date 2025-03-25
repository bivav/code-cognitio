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
   git clone https://github.com/bivav/code-cognitio.git
   cd code-cognitio
   ```

2. Create a virtual environment:

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   # Install uv first (if not already installed)
   curl -fsSL https://get.uv.dev | sh
   # Then use uv to install dependencies from pyproject.toml
   uv sync
   ```

## Usage

Code Cognitio provides several CLI commands for building and searching through your code index.

### Global Options

These options can be used with any command:

```bash
--data-dir PATH     # Directory to store processed data (default: data/processed)
--model NAME        # Name of the embedding model to use (default: all-MiniLM-L6-v2)
--gpu               # Use GPU for embedding and search
--json              # Output results in JSON format
```

### Building the Index

Build a searchable index from your source code:

```bash
python -m src.main build [paths...] [options]

# Options:
--file-types=TYPES      # Comma-separated list of file extensions to process (default: all)
--exclude-types=TYPES   # Comma-separated list of file extensions to exclude
--spacy                 # Use SpaCy for text processing

# Examples:
# Index a single directory
python -m src.main build ./src

# Index multiple paths with specific file types
python -m src.main build ./src ./docs --file-types=py,js,ts

# Index with exclusions and GPU acceleration
python -m src.main build ./project --exclude-types=css,html --gpu
```

### Searching the Index

Search through your indexed code:

```bash
python -m src.main search "your query" [options]

# Options:
--top-k N           # Number of results to return (default: 5)
--filter TYPE       # Filter by content type (code or documentation)
--min-score FLOAT   # Minimum similarity score (default: 0.0)
--type TYPE         # Filter by Python type (function, class, method, module)
--param-type TYPE   # Filter by parameter type
--param-name NAME   # Filter by parameter name
--return-type TYPE  # Filter by return type

# Examples:
# Basic search
python -m src.main search "how to implement authentication"

# Search with filters
python -m src.main search "database connection" --type=function --top-k=10

# Search for specific parameter usage
python -m src.main search "user authentication" --param-type=str --return-type=bool
```

### Listing Supported File Types

List all file types that Code Cognitio can process:

```bash
python -m src.main list-file-types
```

This will display all supported extensions for both code files and documentation files.

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

# Run specific test categories (WIP)
make test-extractors
make test-processors
make test-search
make test-integration

# Generate test coverage report
make coverage
make coverage-html

# Format, lint, test in one step
make ready
```

### Testing

There is a comprehensive test suite covering extractors, processors, and the search engine.

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
├── src/             # Main Python source code
├── tests/           # Test files
├── docs/            # Documentation
├── data/            # Data files
├── examples/        # Example code for testing
├── pyproject.toml   # Project dependencies and configuration
└── Makefile         # Build and test automation
```

The project is organized into several key directories:

- `src/`: Contains the core Python source code for the semantic search engine
- `tests/`: Contains unit and integration tests
- `docs/`: Contains project documentation
- `data/`: Contains data files used by the project
- `examples/`: Contains example code and usage patterns

## License

[MIT License](LICENSE)
