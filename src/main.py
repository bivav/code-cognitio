"""Main CLI interface for the semantic search system."""

import os
import sys
import argparse
import json
import logging
from typing import List, Dict, Any, Optional

from src.extractors.code_extractor import CodeExtractor
from src.extractors.doc_extractor import DocExtractor
from src.processors.text_processor import TextProcessor
from src.search.search_engine import SearchEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def build_index(args):
    """Build the search index from source files."""
    search_engine = SearchEngine(
        model_name=args.model, data_dir=args.data_dir, use_gpu=args.gpu
    )

    # Initialize extractors
    code_extractor = CodeExtractor()
    doc_extractor = DocExtractor()

    # Initialize text processor with specified options
    text_processor = TextProcessor(use_spacy=args.spacy)

    # Parse file type filters
    include_types = args.file_types.lower().split(",") if args.file_types else []
    exclude_types = args.exclude_types.lower().split(",") if args.exclude_types else []

    process_all_types = args.file_types == "all"

    # Get supported file extensions
    supported_extensions = set()
    for ext, extractor in code_extractor.extractors.items():
        if ext.startswith("."):  # Only consider extensions, not special filenames
            ext_without_dot = ext[1:]  # Remove the leading dot
            if process_all_types:
                if ext_without_dot not in exclude_types:
                    supported_extensions.add(ext)
            elif ext_without_dot in include_types:
                supported_extensions.add(ext)

    # Add doc extractor extensions if needed
    doc_extensions = doc_extractor.get_supported_extensions()
    if process_all_types:
        for ext in doc_extensions:
            ext_without_dot = ext[1:] if ext.startswith(".") else ext
            if ext_without_dot not in exclude_types:
                supported_extensions.add(ext)
    elif "md" in include_types or "markdown" in include_types:
        supported_extensions.add(".md")
    elif "rst" in include_types:
        supported_extensions.add(".rst")

    logger.info(f"Processing file types: {', '.join(sorted(supported_extensions))}")

    # Get all files
    files = []
    for path in args.paths:
        if os.path.isfile(path):
            files.append(path)
        elif os.path.isdir(path):
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    files.append(file_path)

    logger.info(f"Found {len(files)} files to process")

    # Process files
    all_chunks = []
    for file_path in files:
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()  # Normalize extension

        # Skip hidden files
        if os.path.basename(file_path).startswith("."):
            continue

        # Skip files that don't match our filters
        if (
            not process_all_types
            and ext not in supported_extensions
            and filename not in code_extractor.file_patterns
        ):
            logger.info(f"Skipping {file_path} due to file type filters")
            continue

        # Use appropriate extractor based on file extension
        if ext in code_extractor.get_supported_extensions():
            logger.info(f"Processing code file: {file_path}")
            try:
                chunks = code_extractor.extract_from_file(file_path)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                continue
        elif filename in code_extractor.file_patterns:
            logger.info(f"Processing special file: {file_path}")
            try:
                chunks = code_extractor.extract_from_file(file_path)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                continue
        elif ext in doc_extractor.get_supported_extensions():
            logger.info(f"Processing documentation file: {file_path}")
            try:
                chunks = doc_extractor.extract_from_file(file_path)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                continue
        else:
            # Skip files with unsupported extensions
            logger.info(f"Skipping unsupported file type: {file_path}")
            continue

        # Process chunks with text processor
        processed_chunks = []
        for chunk in chunks:
            try:
                processed_chunk = text_processor.process_chunk(chunk)
                processed_chunks.append(processed_chunk)
            except Exception as e:
                logger.error(f"Error processing chunk: {str(e)}")
                continue

        all_chunks.extend(processed_chunks)
        logger.info(f"Extracted {len(processed_chunks)} chunks from {file_path}")

    logger.info(f"Adding {len(all_chunks)} chunks to index...")
    search_engine.add_chunks(all_chunks)

    logger.info("Building index...")
    search_engine.build_index()

    logger.info(f"Index build complete. Total chunks: {len(all_chunks)}")


def search(args):
    """Search the index for relevant information."""
    search_engine = SearchEngine(
        model_name=args.model, data_dir=args.data_dir, use_gpu=args.gpu
    )

    # Load the index
    if not search_engine.load_index():
        logger.warning("Failed to load search index. Please build the index first.")
        print("No index found. Please build the index first using the 'build' command.")
        return

    # Build signature filter if specified
    signature_filter = {}
    if args.param_type:
        signature_filter["param_type"] = args.param_type
    if args.return_type:
        signature_filter["return_type"] = args.return_type
    if args.param_name:
        signature_filter["param_name"] = args.param_name

    # Perform search
    results = search_engine.search(
        query=args.query,
        top_k=args.top_k,
        content_filter=args.filter,
        min_score=args.min_score,
        type_filter=args.type,
        signature_filter=signature_filter if signature_filter else None,
    )

    if not results:
        print("No results found matching your query.")
        return

    # Display results
    print(f"\nSearch results for: {args.query}\n")
    print(f"Found {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        chunk = result["chunk"]
        score = result["score"]
        content = result["content"]

        print(f"Result {i} (Score: {score:.4f}):")
        print(f"Type: {chunk.get('type', 'Unknown')}")

        # Display file path if available
        if "file_path" in chunk:
            print(f"File: {chunk['file_path']}")

        # Display line numbers if available
        if "lineno" in chunk:
            print(f"Line: {chunk['lineno']}")

        # Display document title for documentation chunks
        if chunk.get("content_type") == "documentation" and "document_title" in chunk:
            print(f"Document: {chunk['document_title']}")

        # Display section title for section chunks
        if chunk.get("type") == "section" and "title" in chunk:
            print(f"Section: {chunk['title']}")

        # Display readable name for functions/methods if available
        if "readable_name" in chunk:
            print(f"Description: {chunk['readable_name']}")

        # Display patterns if available
        if "patterns" in chunk and chunk["patterns"]:
            print(f"Patterns: {', '.join(chunk['patterns'])}")

        # Display key operations for functions
        if "key_operations" in chunk and chunk["key_operations"]:
            print(f"Key Operations: {', '.join(chunk['key_operations'][:3])}")

        # Display usage information
        if "usage" in chunk and "common_usage" in chunk.get("usage", {}):
            usage = chunk["usage"]
            if usage.get("common_usage"):
                print(f"Common Usage: {', '.join(usage['common_usage'])}")
            if "call_count" in usage:
                print(f"Called {usage['call_count']} times in this file")

        # Display relationships if available
        if "relationships" in chunk and chunk["relationships"]:
            rel_info = []
            for rel in chunk["relationships"][:3]:  # Limit to 3 relationships
                rel_info.append(f"{rel['type']} {rel['name']}")
            print(f"Relationships: {', '.join(rel_info)}")

        # Display content
        print(f"\n{content}\n")
        print(f"Location: {chunk['file_path']}")
        print("-" * 80)


def list_file_types():
    """List all supported file types."""
    code_extractor = CodeExtractor()
    doc_extractor = DocExtractor()

    supported_extensions = {}

    # Get code extractors
    for ext, extractor in code_extractor.extractors.items():
        if ext.startswith("."):
            ext_without_dot = ext[1:]
            extractor_type = type(extractor).__name__
            supported_extensions[ext_without_dot] = extractor_type

    # Get special file patterns
    for filename, extractor in code_extractor.file_patterns.items():
        extractor_type = type(extractor).__name__
        supported_extensions[filename] = extractor_type

    # Get doc extensions
    for ext in doc_extractor.get_supported_extensions():
        ext_without_dot = ext[1:] if ext.startswith(".") else ext
        supported_extensions[ext_without_dot] = "DocExtractor"

    # Print results
    print("\nSupported file types:\n")
    print(f"{'Extension':<15} {'Extractor':<25}")
    print("-" * 40)

    for ext, extractor in sorted(supported_extensions.items()):
        print(f"{ext:<15} {extractor:<25}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Semantic Code Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--model", type=str, default="all-MiniLM-L6-v2", help="Embedding model to use"
    )
    common_parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Directory to store/load processed data",
    )
    common_parser.add_argument(
        "--gpu",
        action="store_true",
        help="Use GPU for embedding and search if available",
    )

    # Build command
    build_parser = subparsers.add_parser(
        "build", parents=[common_parser], help="Build search index from source files"
    )
    build_parser.add_argument(
        "paths", nargs="+", help="Paths to files or directories to index"
    )
    build_parser.add_argument(
        "--spacy",
        action="store_true",
        help="Use spaCy for text processing (more accurate but slower)",
    )
    build_parser.add_argument(
        "--file-types",
        type=str,
        default="all",
        help="Comma-separated list of file types to process (e.g., py,js,dockerfile). Use 'all' for all supported types",
    )
    build_parser.add_argument(
        "--exclude-types",
        type=str,
        default="",
        help="Comma-separated list of file types to exclude (e.g., js,jsx)",
    )

    # List file types command
    subparsers.add_parser("list-file-types", help="List all supported file types")

    # Search command
    search_parser = subparsers.add_parser(
        "search", parents=[common_parser], help="Search the index"
    )
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument(
        "--top-k", type=int, default=5, help="Number of results to return"
    )
    search_parser.add_argument(
        "--filter",
        type=str,
        choices=["code", "documentation"],
        help="Filter results by content type",
    )
    search_parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum similarity score threshold",
    )
    # Add new search filters
    search_parser.add_argument(
        "--type",
        type=str,
        choices=["function", "method", "class", "module"],
        help="Filter results by code object type",
    )
    search_parser.add_argument(
        "--param-type",
        type=str,
        help="Filter by parameter type (e.g., 'str', 'int', 'List')",
    )
    search_parser.add_argument(
        "--return-type",
        type=str,
        help="Filter by return type (e.g., 'bool', 'Dict', 'None')",
    )
    search_parser.add_argument(
        "--param-name",
        type=str,
        help="Filter by parameter name (e.g., 'id', 'name', 'data')",
    )

    args = parser.parse_args()

    # Execute command
    if args.command == "build":
        build_index(args)
    elif args.command == "search":
        search(args)
    elif args.command == "list-file-types":
        list_file_types()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
