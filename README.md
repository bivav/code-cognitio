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

```bash
# Clone the repository
git clone https://github.com/yourusername/code-cognitio.git
cd code-cognitio

# Set up a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
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

### Testing

We have a comprehensive test suite covering extractors, processors, and the search engine.

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
```

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

- `src/`: Main package
  - `extractors/`: Code and documentation extraction modules
  - `processors/`: Text processing and chunking
  - `search/`: Search engine implementation
- `tests/`: Test suite
  - `extractors/`: Tests for extractors
  - `processors/`: Tests for text processors
  - `search/`: Tests for search engine
  - `test_integration.py`: End-to-end tests

## License

[MIT License](LICENSE)
