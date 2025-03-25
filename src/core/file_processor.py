"""Core file processing functionality for Code Cognitio."""

import os
import logging
from typing import List, Dict, Any, Set, Optional

from src.extractors.code_extractor import CodeExtractor
from src.extractors.doc_extractor import DocExtractor
from src.processors.text_processor import TextProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileProcessor:
    """Service class for processing files for semantic search."""

    def __init__(
        self,
        use_spacy: bool = False,
    ):
        """
        Initialize the file processor.

        Args:
            use_spacy: Whether to use SpaCy for text processing
        """
        # Initialize extractors
        self.code_extractor = CodeExtractor()
        self.doc_extractor = DocExtractor()

        # Initialize text processor
        self.text_processor = TextProcessor(use_spacy=use_spacy)

        logger.info("Initialized FileProcessor")

    def get_supported_extensions(
        self,
        include_types: Optional[List[str]] = None,
        exclude_types: Optional[List[str]] = None,
    ) -> Set[str]:
        """
        Get the list of supported file extensions based on filters.

        Args:
            include_types: List of file types to include
            exclude_types: List of file types to exclude

        Returns:
            Set of supported file extensions with leading dots
        """
        include_types = include_types or []
        exclude_types = exclude_types or []
        process_all_types = not include_types or "all" in include_types

        # Get supported file extensions
        supported_extensions = set()
        for ext, extractor in self.code_extractor.extractors.items():
            if ext.startswith("."):  # Only consider extensions, not special filenames
                ext_without_dot = ext[1:]  # Remove the leading dot
                if process_all_types:
                    if ext_without_dot not in exclude_types:
                        supported_extensions.add(ext)
                elif ext_without_dot in include_types:
                    supported_extensions.add(ext)

        # Add doc extractor extensions if needed
        doc_extensions = self.doc_extractor.get_supported_extensions()
        if process_all_types:
            for ext in doc_extensions:
                ext_without_dot = ext[1:] if ext.startswith(".") else ext
                if ext_without_dot not in exclude_types:
                    supported_extensions.add(ext)
        elif "md" in include_types or "markdown" in include_types:
            supported_extensions.add(".md")
        elif "rst" in include_types:
            supported_extensions.add(".rst")

        return supported_extensions

    def process_files(
        self,
        file_paths: List[str],
        include_types: Optional[List[str]] = None,
        exclude_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process files and return a list of processed chunks.

        Args:
            file_paths: List of file paths to process
            include_types: List of file types to include
            exclude_types: List of file types to exclude

        Returns:
            List of processed chunks from the files
        """
        include_types = include_types or []
        exclude_types = exclude_types or []

        supported_extensions = self.get_supported_extensions(
            include_types, exclude_types
        )
        process_all_types = not include_types or "all" in include_types

        logger.info(f"Processing file types: {', '.join(sorted(supported_extensions))}")
        logger.info(f"Found {len(file_paths)} files to process")

        # Process files
        all_chunks = []
        for file_path in file_paths:
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
                and filename not in self.code_extractor.file_patterns
            ):
                logger.info(f"Skipping {file_path} due to file type filters")
                continue

            # Use appropriate extractor based on file extension
            try:
                chunks = self._extract_chunks(file_path, ext, filename)

                if not chunks:
                    logger.info(f"No chunks extracted from: {file_path}")
                    continue

                # Process chunks with text processor
                processed_chunks = []
                for chunk in chunks:
                    try:
                        processed_chunk = self.text_processor.process_chunk(chunk)
                        processed_chunks.append(processed_chunk)
                    except Exception as e:
                        logger.error(f"Error processing chunk: {str(e)}")
                        continue

                all_chunks.extend(processed_chunks)
                logger.info(
                    f"Extracted {len(processed_chunks)} chunks from {file_path}"
                )

            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                continue

        logger.info(f"Processed {len(all_chunks)} chunks in total")
        return all_chunks

    def _extract_chunks(
        self, file_path: str, ext: str, filename: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Extract chunks from a file using the appropriate extractor.

        Args:
            file_path: Path to the file
            ext: File extension
            filename: File name

        Returns:
            List of extracted chunks or None if extraction failed
        """
        if ext in self.code_extractor.get_supported_extensions():
            logger.info(f"Processing code file: {file_path}")
            return self.code_extractor.extract_from_file(file_path)
        elif filename in self.code_extractor.file_patterns:
            logger.info(f"Processing special file: {file_path}")
            return self.code_extractor.extract_from_file(file_path)
        elif ext in self.doc_extractor.get_supported_extensions():
            logger.info(f"Processing documentation file: {file_path}")
            return self.doc_extractor.extract_from_file(file_path)
        else:
            # Skip files with unsupported extensions
            logger.info(f"Skipping unsupported file type: {file_path}")
            return None
