"""Command-line interface for Code Cognitio."""

import os
import sys
import argparse
import json
import logging
from typing import List, Dict, Any, Optional

from src.core.search_service import SearchService
from src.core.file_processor import FileProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def build_index(args):
    """Build the search index from source files."""
    search_service = SearchService(
        model_name=args.model, data_dir=args.data_dir, use_gpu=args.gpu
    )

    # Initialize file processor
    file_processor = FileProcessor(use_spacy=args.spacy)

    # Parse file type filters
    include_types = args.file_types.lower().split(",") if args.file_types else []
    exclude_types = args.exclude_types.lower().split(",") if args.exclude_types else []

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
    all_chunks = file_processor.process_files(files, include_types, exclude_types)

    logger.info(f"Adding {len(all_chunks)} chunks to index...")
    search_service.build_index(all_chunks)

    logger.info(f"Index build complete. Total chunks: {len(all_chunks)}")


def search(args):
    """Search the index for relevant information."""
    search_service = SearchService(
        model_name=args.model, data_dir=args.data_dir, use_gpu=args.gpu
    )

    # Build signature filter if specified
    signature_filter = {}
    if args.param_type:
        signature_filter["param_type"] = args.param_type
    if args.return_type:
        signature_filter["return_type"] = args.return_type
    if args.param_name:
        signature_filter["param_name"] = args.param_name

    # Perform search
    results = search_service.search(
        query=args.query,
        top_k=args.top_k,
        content_filter=args.filter,
        min_score=args.min_score,
        type_filter=args.type,
        signature_filter=signature_filter if signature_filter else None,
    )

    if not results:
        if args.json:
            print(json.dumps([]))
        else:
            print("No results found matching your query.")
        return

    # Output results
    if args.json:
        # Output JSON results for programmatic consumption (used by VS Code extension)
        print(json.dumps(results))
    else:
        # Pretty print results for CLI users
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
            if (
                chunk.get("content_type") == "documentation"
                and "document_title" in chunk
            ):
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


def list_file_types(args):
    """List all supported file types."""
    file_processor = FileProcessor()

    # Get all supported extensions
    code_extensions = file_processor.code_extractor.get_supported_extensions()
    doc_extensions = file_processor.doc_extractor.get_supported_extensions()

    # Format the extensions for display
    code_extensions_list = sorted(
        [ext[1:] if ext.startswith(".") else ext for ext in code_extensions]
    )
    doc_extensions_list = sorted(
        [ext[1:] if ext.startswith(".") else ext for ext in doc_extensions]
    )

    # Create a result dictionary
    result = {"code": code_extensions_list, "documentation": doc_extensions_list}

    if args.json:
        # Output JSON for programmatic consumption
        print(json.dumps(result))
    else:
        # Pretty print for CLI users
        print("\nSupported file types:\n")

        print("Code files:")
        for ext in code_extensions_list:
            print(f"  .{ext}")

        print("\nDocumentation files:")
        for ext in doc_extensions_list:
            print(f"  .{ext}")


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
        help="Comma-separated list of file extensions to exclude",
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
