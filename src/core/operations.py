"""Core operations for Code Cognitio.

This module provides a unified interface for all operations that can be performed
by both the CLI and MCP server implementations.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from src.core.search_service import SearchService
from src.core.file_processor import FileProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeCognitioOperations:
    """Core operations for Code Cognitio.

    This class provides methods for all the operations that can be performed
    in Code Cognitio, independent of the interface (CLI or MCP server).
    """

    def __init__(
        self,
        data_dir: str = "data/processed",
        model_name: str = "all-MiniLM-L6-v2",
        use_gpu: bool = False,
        use_spacy: bool = False,
    ):
        """Initialize the operations manager.

        Args:
            data_dir: Directory where the search index is stored
            model_name: Name of the embedding model to use
            use_gpu: Whether to use GPU for embedding and search
            use_spacy: Whether to use SpaCy for text processing
        """
        # Initialize core services
        self.search_service = SearchService(
            model_name=model_name, data_dir=data_dir, use_gpu=use_gpu
        )
        self.file_processor = FileProcessor(use_spacy=use_spacy)
        self.data_dir = data_dir
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.use_spacy = use_spacy

        # Default ignore lists
        self.ignore_dirs = [
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

        self.ignore_patterns = [
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

    def search(
        self,
        query: str,
        top_k: int = 5,
        content_filter: Optional[str] = None,
        min_score: float = 0.0,
        type_filter: Optional[str] = None,
        param_type: Optional[str] = None,
        param_name: Optional[str] = None,
        return_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search the code repository for relevant information.

        Args:
            query: The search query
            top_k: Number of results to return
            content_filter: Filter results by content type (code/documentation)
            min_score: Minimum similarity score
            type_filter: Filter by Python type (function/class/method/module)
            param_type: Filter by parameter type
            param_name: Filter by parameter name
            return_type: Filter by return type

        Returns:
            List of search results with similarity scores
        """
        # Build signature filter if specified
        signature_filter = {}
        if param_type:
            signature_filter["param_type"] = param_type
        if return_type:
            signature_filter["return_type"] = return_type
        if param_name:
            signature_filter["param_name"] = param_name

        # Perform search
        return self.search_service.search(
            query=query,
            top_k=top_k,
            content_filter=content_filter,
            min_score=min_score,
            type_filter=type_filter,
            signature_filter=signature_filter if signature_filter else None,
        )

    def build_index(
        self,
        paths: List[str],
        file_types: str = "all",
        exclude_types: str = "",
        ignore_dirs: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build the search index from source files.

        Args:
            paths: List of paths to source files or directories
            file_types: Comma-separated list of file extensions to process, or 'all' for all supported types
            exclude_types: Comma-separated list of file extensions to exclude
            ignore_dirs: List of directories to ignore
            ignore_patterns: List of file patterns to ignore

        Returns:
            Dictionary with status information including total chunks
        """
        # Use instance variables as defaults if parameters are None
        ignore_dirs = ignore_dirs or self.ignore_dirs
        ignore_patterns = ignore_patterns or self.ignore_patterns

        # Parse file type filters
        include_types = file_types.lower().split(",") if file_types != "all" else []

        # Default exclusions + any user-specified exclusions
        default_exclude = [
            "pyc",
            "pyo",
            "DS_Store",
            "git",
            "svn",
            "bzr",
            "hg",
            "idea",
            "vscode",
            "cache",
            "egg-info",
        ]
        user_exclude = exclude_types.lower().split(",") if exclude_types else []
        exclude_types_list = default_exclude + [
            ext for ext in user_exclude if ext and ext not in default_exclude
        ]

        # Get all files
        files = []
        for path in paths:
            if os.path.isfile(path):
                files.append(path)
            elif os.path.isdir(path):
                for root, dirs, filenames in os.walk(path):
                    # Skip directories that shouldn't be indexed
                    dirs[:] = [
                        d
                        for d in dirs
                        if d not in ignore_dirs and not d.startswith(".")
                    ]

                    for filename in filenames:
                        # Skip files that shouldn't be indexed
                        skip = False
                        for pattern in ignore_patterns:
                            if pattern.startswith("*."):
                                ext = pattern[2:]  # Get the extension
                                if filename.endswith(ext):
                                    skip = True
                                    break
                            elif pattern in filename:
                                skip = True
                                break

                        if skip or any(
                            filename.endswith(f".{ext}") for ext in exclude_types_list
                        ):
                            continue

                        file_path = os.path.join(root, filename)
                        files.append(file_path)

        logger.info(f"Found {len(files)} files to process")

        # Process files
        all_chunks = self.file_processor.process_files(
            files, include_types, exclude_types_list
        )

        logger.info(f"Adding {len(all_chunks)} chunks to index...")
        success = self.search_service.build_index(all_chunks)

        return {
            "success": success,
            "total_chunks": len(all_chunks),
            "total_files": len(files),
            "data_dir": self.data_dir,
            "use_gpu": self.use_gpu,
            "use_spacy": self.use_spacy,
        }

    def list_file_types(self) -> Dict[str, Union[List[str], bool]]:
        """List all supported file types.

        Returns:
            Dictionary with code and documentation file extensions
        """
        # Get all supported extensions
        code_extensions = self.file_processor.code_extractor.get_supported_extensions()
        doc_extensions = self.file_processor.doc_extractor.get_supported_extensions()

        # Format the extensions for display
        code_extensions_list = sorted(
            [ext[1:] if ext.startswith(".") else ext for ext in code_extensions]
        )
        doc_extensions_list = sorted(
            [ext[1:] if ext.startswith(".") else ext for ext in doc_extensions]
        )

        return {
            "code": code_extensions_list,
            "documentation": doc_extensions_list,
            "use_spacy": self.use_spacy,
        }

    def get_index_status(self) -> Dict[str, Any]:
        """Get the status of the search index.

        Returns:
            Dictionary with index status information
        """
        status = self.search_service.get_index_status()

        # Parse the status string to extract metadata
        if "Index is ready" in status:
            # Extract size and chunks information
            size_info = status.split("Size: ")[1].split(" MB")[0]
            chunks_info = status.split("Chunks: ")[1].split(",")[0]

            return {
                "status": "ready",
                "size_mb": float(size_info),
                "chunks": int(chunks_info),
                "model": self.model_name,
                "data_dir": self.data_dir,
                "use_gpu": self.use_gpu,
                "message": status,
            }
        elif "No index found" in status:
            return {"status": "not_found", "message": status, "data_dir": self.data_dir}
        else:
            return {"status": "error", "message": status, "data_dir": self.data_dir}

    def format_search_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format search results as a human-readable string.

        Args:
            results: Search results from the search method
            query: The original search query

        Returns:
            Formatted search results as a string
        """
        if not results:
            return "No results found matching your query."

        # Format results as string
        output = []
        output.append(f"Search results for: {query}")
        output.append(f"Found {len(results)} results:")

        for i, result in enumerate(results, 1):
            chunk = result["chunk"]
            score = result["score"]
            content = result["content"]

            output.append(f"Result {i} (Score: {score:.4f}):")
            output.append(f"Type: {chunk.get('type', 'Unknown')}")

            # Display file path if available
            if "file_path" in chunk:
                output.append(f"File: {chunk['file_path']}")

            # Display line numbers if available
            if "lineno" in chunk:
                output.append(f"Line: {chunk['lineno']}")

            # Display document title for documentation chunks
            if (
                chunk.get("content_type") == "documentation"
                and "document_title" in chunk
            ):
                output.append(f"Document: {chunk['document_title']}")

            # Display section title for section chunks
            if chunk.get("type") == "section" and "title" in chunk:
                output.append(f"Section: {chunk['title']}")

            # Display readable name for functions/methods if available
            if "readable_name" in chunk:
                output.append(f"Description: {chunk['readable_name']}")

            # Display patterns if available
            if "patterns" in chunk and chunk["patterns"]:
                output.append(f"Patterns: {', '.join(chunk['patterns'])}")

            # Display key operations for functions
            if "key_operations" in chunk and chunk["key_operations"]:
                output.append(
                    f"Key Operations: {', '.join(chunk['key_operations'][:3])}"
                )

            # Display usage information
            if "usage" in chunk and "common_usage" in chunk.get("usage", {}):
                usage = chunk["usage"]
                if usage.get("common_usage"):
                    output.append(f"Common Usage: {', '.join(usage['common_usage'])}")
                if "call_count" in usage:
                    output.append(f"Called {usage['call_count']} times in this file")

            # Display relationships if available
            if "relationships" in chunk and chunk["relationships"]:
                rel_info = []
                for rel in chunk["relationships"][:3]:  # Limit to 3 relationships
                    rel_info.append(f"{rel['type']} {rel['name']}")
                output.append(f"Relationships: {', '.join(rel_info)}")

            # Display content
            output.append(f"\n{content}\n")
            output.append(f"Location: {chunk['file_path']}")
            output.append("-" * 80)

        return "\n".join(output)

    def format_file_types(self, file_types: Dict[str, List[str]]) -> str:
        """Format file types as a human-readable string.

        Args:
            file_types: Dictionary with code and documentation file extensions

        Returns:
            Formatted file types as a string
        """
        output = []
        output.append("Supported file types:")

        output.append("\nCode files:")
        for ext in file_types["code"]:
            output.append(f"  - {ext}")

        output.append("\nDocumentation files:")
        for ext in file_types["documentation"]:
            output.append(f"  - {ext}")

        return "\n".join(output)
