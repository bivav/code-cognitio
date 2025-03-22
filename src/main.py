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
        _, ext = os.path.splitext(file_path)

        # Skip hidden files
        if os.path.basename(file_path).startswith("."):
            continue

        # Use appropriate extractor based on file extension
        if ext in code_extractor.get_supported_extensions():
            logger.info(f"Processing code file: {file_path}")
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

    # Perform search
    results = search_engine.search(
        query=args.query,
        top_k=args.top_k,
        content_filter=args.filter,
        min_score=args.min_score,
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

        # Display content
        print(f"\n{content}\n")
        print("-" * 80)


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

    args = parser.parse_args()

    # Execute command
    if args.command == "build":
        build_index(args)
    elif args.command == "search":
        search(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
