"""Base class for all code extractors."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set


class BaseExtractor(ABC):
    """
    Abstract base class for all language-specific code extractors.

    All language extractors should inherit from this class and implement
    the required methods.
    """

    @abstractmethod
    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract code information from a file.

        Args:
            file_path: Path to the file to extract information from

        Returns:
            List of extracted items with their metadata
        """
        pass

    @abstractmethod
    def extract_from_content(
        self, content: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Extract code information from content string.

        Args:
            content: String content of the code
            file_path: Path to the file (for reference)

        Returns:
            List of extracted items with their metadata
        """
        pass

    @abstractmethod
    def get_supported_extensions(self) -> Set[str]:
        """
        Get the set of file extensions this extractor supports.

        Returns:
            Set of file extensions (including the dot, e.g. '.js')
        """
        pass

    def get_language_name(self) -> str:
        """
        Get the name of the language this extractor handles.

        Returns:
            String name of the language
        """
        return self.__class__.__name__.replace("Extractor", "").lower()
