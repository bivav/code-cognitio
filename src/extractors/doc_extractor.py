"""Module for documentation extraction across different formats."""

import os
import logging
from typing import Dict, List, Any, Optional

from src.extractors.markdown_extractor import MarkdownExtractor
from src.extractors.rst_extractor import RSTExtractor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocExtractor:
    """
    Factory class for extracting information from various documentation formats.

    Acts as a dispatcher to route extraction requests to the appropriate
    format-specific extractor.
    """

    def __init__(self):
        """Initialize the documentation extractor with supported format extractors."""
        # Map of file extensions to their corresponding extractors
        self.extractors = {
            ".md": MarkdownExtractor(),
            ".markdown": MarkdownExtractor(),
            ".rst": RSTExtractor(),
            ".rest": RSTExtractor(),
        }

        # Additional file extensions by format
        self.extension_aliases = {
            ".mdown": ".md",
            ".mkd": ".md",
            ".mdwn": ".md",
            ".mdtxt": ".md",
            ".mdtext": ".md",
            ".rmd": ".md",  # R Markdown
            ".txt": ".md",  # Treat plain text as markdown for simple parsing
        }

    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract documentation information from a file based on its extension.

        Args:
            file_path: Path to the file to extract from

        Returns:
            List of extracted items
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()  # Normalize extension

        # Check if this is an alias extension
        if ext in self.extension_aliases:
            ext = self.extension_aliases[ext]

        # Find the appropriate extractor
        if ext in self.extractors:
            extractor = self.extractors[ext]
            logger.info(f"Using {type(extractor).__name__} for {file_path}")
            return extractor.extract_from_file(file_path)
        else:
            logger.warning(f"No extractor available for extension {ext} ({file_path})")
            return self._extract_generic(file_path)

    def _extract_generic(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Perform generic extraction for unsupported documentation file types.

        Args:
            file_path: Path to the file

        Returns:
            List with basic file information
        """
        try:
            # Just extract the file as a text document
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()

            # Create a simple representation
            file_info = {
                "type": "section",
                "level": 0,
                "title": os.path.basename(file_path),
                "content": content,
                "file_path": file_path,
                "position": 0,
                "content_type": "documentation",
                "format": "unknown",
            }

            return [file_info]
        except Exception as e:
            logger.error(f"Failed to extract from {file_path}: {str(e)}")
            return []

    def register_extractor(self, extension: str, extractor: Any) -> None:
        """
        Register a new extractor for a specific file extension.

        Args:
            extension: File extension (including dot, e.g. '.html')
            extractor: Extractor instance to use for this extension
        """
        self.extractors[extension.lower()] = extractor
        logger.info(f"Registered {type(extractor).__name__} for extension {extension}")

    def register_extension_alias(self, alias: str, target: str) -> None:
        """
        Register an extension alias pointing to an existing extension.

        Args:
            alias: Alias extension (e.g. '.mdown')
            target: Target extension (e.g. '.md')
        """
        self.extension_aliases[alias.lower()] = target.lower()
        logger.info(f"Registered extension alias {alias} -> {target}")

    def get_supported_extensions(self) -> List[str]:
        """
        Get a list of supported file extensions.

        Returns:
            List of supported extensions
        """
        return list(self.extractors.keys()) + list(self.extension_aliases.keys())
