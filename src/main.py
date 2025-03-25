"""Command-line interface for Code Cognitio."""

import os
import argparse
import logging

from src.core.operations import CodeCognitioOperations

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_IGNORE_DIRS = [
    ".git",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "venv",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".coverage",
    "htmlcov",
]

DEFAULT_IGNORE_PATTERNS = [
    ".git",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.class",
    "*.log",
]


def build_index(args):
    """Build the search index from source files."""
    operations = CodeCognitioOperations(
        model_name=args.model,
        data_dir=args.data_dir,
        use_gpu=args.gpu,
        use_spacy=args.spacy,
    )

    # Build the index using the operations class
    result = operations.build_index(
        paths=args.paths,
        file_types=args.file_types,
        exclude_types=args.exclude_types,
        ignore_dirs=DEFAULT_IGNORE_DIRS,
        ignore_patterns=DEFAULT_IGNORE_PATTERNS,
    )

    logger.info(f"Index build complete. Total chunks: {result['total_chunks']}")


def search(args):
    """Search the index for relevant information."""
    operations = CodeCognitioOperations(
        model_name=args.model, data_dir=args.data_dir, use_gpu=args.gpu
    )

    # Perform search using the operations class
    results = operations.search(
        query=args.query,
        top_k=args.top_k,
        content_filter=args.filter,
        min_score=args.min_score,
        type_filter=args.type,
        param_type=args.param_type,
        param_name=args.param_name,
        return_type=args.return_type,
    )

    if not results:
        print("No results found matching your query.")
        return

    # Format the results using the operations class
    formatted_results = operations.format_search_results(results, args.query)
    print(formatted_results)


def list_file_types(args):
    """List all supported file types."""
    operations = CodeCognitioOperations()

    # Get and format the file types using the operations class
    file_types = operations.list_file_types()
    formatted_types = operations.format_file_types(file_types)
    print(formatted_types)


def main():
    """Entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description="Semantic search system for code repositories."
    )

    # Add global arguments
    parser.add_argument(
        "--data-dir",
        help="Directory to store processed data",
        default="data/processed",
    )
    parser.add_argument(
        "--model",
        help="Name of the embedding model to use",
        default="all-MiniLM-L6-v2",
    )
    parser.add_argument(
        "--gpu", help="Use GPU for embedding and search", action="store_true"
    )
    parser.add_argument(
        "--json", help="Output results in JSON format", action="store_true"
    )

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    subparsers.required = True

    # Build command
    build_parser = subparsers.add_parser("build", help="Build search index")
    build_parser.add_argument(
        "paths", nargs="+", help="Paths to source files or directories"
    )
    build_parser.add_argument(
        "--file-types",
        help="Comma-separated list of file extensions to process, or 'all' for all supported types",
        default="all",
    )
    build_parser.add_argument(
        "--exclude-types",
        help="Comma-separated list of file extensions to exclude (in addition to defaults like pyc, DS_Store, git, etc.)",
        default="",
    )
    build_parser.add_argument(
        "--spacy", help="Use SpaCy for text processing", action="store_true"
    )
    build_parser.set_defaults(func=build_index)

    # Search command
    search_parser = subparsers.add_parser("search", help="Search the index")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--top-k", help="Number of results to return", type=int, default=5
    )
    search_parser.add_argument(
        "--filter",
        help="Filter results by content type",
        choices=["code", "documentation"],
    )
    search_parser.add_argument(
        "--min-score", help="Minimum similarity score", type=float, default=0.0
    )
    search_parser.add_argument(
        "--type",
        help="Filter by Python type",
        choices=["function", "class", "method", "module"],
    )
    search_parser.add_argument("--param-type", help="Filter by parameter type")
    search_parser.add_argument("--param-name", help="Filter by parameter name")
    search_parser.add_argument("--return-type", help="Filter by return type")
    search_parser.set_defaults(func=search)

    # List file types command
    list_types_parser = subparsers.add_parser(
        "list-file-types", help="List supported file types"
    )
    list_types_parser.set_defaults(func=list_file_types)

    # Parse arguments and execute the appropriate command
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
