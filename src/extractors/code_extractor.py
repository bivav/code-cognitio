"""Module for language-agnostic code extraction."""

import os
import logging
from typing import Dict, List, Any, Optional, Type

from src.extractors.python_extractor import PythonExtractor
from src.extractors.javascript_extractor import JavaScriptExtractor
from src.extractors.dockerfile_extractor import DockerfileExtractor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeExtractor:
    """
    Factory class for extracting information from various programming language files.

    Acts as a dispatcher to route extraction requests to the appropriate
    language-specific extractor.
    """

    def __init__(self):
        """Initialize the code extractor with supported language extractors."""
        # Map of file extensions to their corresponding extractors
        self.extractors = {
            ".py": PythonExtractor(),
            ".js": JavaScriptExtractor(),
            ".jsx": JavaScriptExtractor(),
            ".ts": JavaScriptExtractor(),
            ".tsx": JavaScriptExtractor(),
            ".dockerfile": DockerfileExtractor(),
            ".Dockerfile": DockerfileExtractor(),
            # Add more language extractors as they become available
            # '.java': JavaExtractor(),
            # '.cpp': CPPExtractor(),
            # '.c': CExtractor(),
        }

        # Map of common extensions when multiple extensions use the same parser
        self.extension_aliases = {
            ".pyw": ".py",  # Python GUI scripts
            ".pyc": ".py",  # Python compiled files
            ".pyi": ".py",  # Python interface files
        }

        # Add file detection for files without extensions
        self.file_patterns = {
            "Dockerfile": DockerfileExtractor(),
            "dockerfile": DockerfileExtractor(),  # Add lowercase version
            "docker-compose.yml": DockerfileExtractor(),
            "docker-compose.yaml": DockerfileExtractor(),
        }

    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract code information from a file based on its extension.

        Args:
            file_path: Path to the file to extract from

        Returns:
            List of extracted items
        """
        filename = os.path.basename(file_path)

        # Check if filename matches a known pattern
        if filename in self.file_patterns:
            extractor = self.file_patterns[filename]
            logger.info(
                f"Using {type(extractor).__name__} for {file_path} (matched by filename)"
            )
            return extractor.extract_from_file(file_path)

        # Check by extension
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
        Perform generic extraction for unsupported file types.

        This method tries to extract basic information that doesn't
        depend on language-specific parsing.

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
                "type": "file",
                "name": os.path.basename(file_path),
                "file_path": file_path,
                "content": content,
                "content_type": "code",
                "language": self._guess_language(file_path),
            }

            return [file_info]
        except Exception as e:
            logger.error(f"Failed to extract from {file_path}: {str(e)}")
            return []

    def _guess_language(self, file_path: str) -> str:
        """
        Guess the programming language based on file extension.

        Args:
            file_path: Path to the file

        Returns:
            String representing the language name
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # Map of extensions to language names
        language_map = {
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "c++",
            ".cc": "c++",
            ".cxx": "c++",
            ".h": "c",
            ".hpp": "c++",
            ".cs": "csharp",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".m": "objective-c",
            ".rs": "rust",
            ".scala": "scala",
            ".kt": "kotlin",
            ".kts": "kotlin",
            ".sh": "shell",
            ".bash": "shell",
            ".pl": "perl",
            ".r": "r",
            ".lua": "lua",
            ".groovy": "groovy",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".less": "less",
            ".sql": "sql",
            ".py": "python",
        }

        return language_map.get(ext, "unknown")

    def register_extractor(self, extension: str, extractor: Any) -> None:
        """
        Register a new extractor for a specific file extension.

        Args:
            extension: File extension (including dot, e.g. '.js')
            extractor: Extractor instance to use for this extension
        """
        self.extractors[extension.lower()] = extractor
        logger.info(f"Registered {type(extractor).__name__} for extension {extension}")

    def register_extension_alias(self, alias: str, target: str) -> None:
        """
        Register an extension alias pointing to an existing extension.

        Args:
            alias: Alias extension (e.g. '.jsx')
            target: Target extension (e.g. '.js')
        """
        self.extension_aliases[alias.lower()] = target.lower()
        logger.info(f"Registered extension alias {alias} -> {target}")

    def get_supported_extensions(self) -> List[str]:
        """
        Get a list of supported file extensions.

        Returns:
            List of supported extensions
        """
        # Return both primary extensions and aliases
        return list(self.extractors.keys()) + list(self.extension_aliases.keys())
