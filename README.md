# Code Cognitio

A powerful semantic search system for code repositories that uses FAISS vector similarity and advanced text processing to enable natural language searching of code and documentation.

## Features

- **FAISS Vector Search**: Efficient similarity search using Facebook AI's FAISS library
- **Multiple Index Types**: Separate indices for code and documentation
- **Content Filtering**: Filter search results by content type
- **Lemmatization**: Improved text processing with both NLTK and spaCy support
- **Language Support**: Extracts information from Python code and documentation files (Markdown, RST)
- **Extensible Architecture**: Designed to be easily extended with additional extractors and processors

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/code-cognitio.git
cd code-cognitio

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

### Requirements

- Python 3.8+
- FAISS for efficient vector similarity
- sentence-transformers for high-quality embeddings
- NLTK and/or spaCy for text processing

## Usage

### Building the Search Index

```bash
# Index a specific file or directory
python -m src.main build path/to/your/code

# Index multiple paths with spaCy for better text processing
python -m src.main build --spacy path/to/code path/to/docs

# Use GPU for faster processing (if available)
python -m src.main build --gpu path/to/your/code
```

### Searching

```bash
# Basic search
python -m src.main search "How to use the DataProcessor class"

# Filter by content type (code or documentation)
python -m src.main search "How to remove duplicates" --filter code

# Set the number of results to return
python -m src.main search "configuration options" --top-k 10

# Set a minimum similarity score threshold
python -m src.main search "error handling" --min-score 0.5
```

## Architecture

The system consists of the following components:

1. **Extractors**: Parse files to extract meaningful chunks
   - `PythonExtractor`: Extracts functions, classes, and docstrings from Python files
   - `MarkdownExtractor`: Extracts sections from Markdown files
   - `RSTExtractor`: Extracts sections from reStructuredText files

2. **Text Processor**: Cleans and normalizes text for indexing
   - Supports lemmatization using spaCy or NLTK
   - Removes stop words and normalizes text

3. **Search Engine**: Indexes and searches content
   - Uses FAISS for efficient vector similarity search
   - Supports multiple indices for different content types
   - Normalizes embeddings for cosine similarity

## Extending the System

### Adding a New File Format

To add support for a new file format:

1. Create a new extractor class in `src/extractors/`
2. Register the extractor in `CodeExtractor` or `DocExtractor`

### Adding a New Search Backend

To add a new search backend:

1. Create a new search engine class in `src/search/`
2. Implement the same interface as `FaissSearchEngine`
3. Update `SearchEngine` to use the new backend

## License

This project is licensed under the MIT License - see the LICENSE file for details.
