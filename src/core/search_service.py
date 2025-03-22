"""Core search functionality for Code Cognitio."""

import os
import logging
from typing import List, Dict, Any, Optional

from src.search.search_engine import SearchEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchService:
    """Service class for managing search operations."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        data_dir: str = "data/processed",
        use_gpu: bool = False,
    ):
        """
        Initialize the search service.

        Args:
            model_name: Name of the embedding model to use
            data_dir: Directory to store processed data
            use_gpu: Whether to use GPU for embedding and search
        """
        self.model_name = model_name
        self.data_dir = data_dir
        self.use_gpu = use_gpu

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Initialize the search engine
        self.engine = SearchEngine(
            model_name=model_name, data_dir=data_dir, use_gpu=use_gpu
        )

        logger.info(f"Initialized SearchService with model {model_name}")

    def build_index(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Build the search index from processed chunks.

        Args:
            chunks: List of processed document chunks

        Returns:
            True if the index was built successfully, False otherwise
        """
        try:
            self.engine.add_chunks(chunks)
            self.engine.build_index()
            return True
        except Exception as e:
            logger.error(f"Error building index: {str(e)}")
            return False

    def search(
        self,
        query: str,
        top_k: int = 5,
        content_filter: Optional[str] = None,
        min_score: float = 0.0,
        type_filter: Optional[str] = None,
        signature_filter: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for chunks relevant to the query.

        Args:
            query: Search query
            top_k: Number of results to return
            content_filter: Filter results by content type ('code' or 'documentation')
            min_score: Minimum similarity score threshold
            type_filter: Filter by Python type (function, class, method, module)
            signature_filter: Filter by function signature (e.g. parameter or return types)

        Returns:
            List of search results with similarity scores
        """
        if not self.load_index():
            logger.warning("No index found. Please build the index first.")
            return []

        return self.engine.search(
            query=query,
            top_k=top_k,
            content_filter=content_filter,
            min_score=min_score,
            type_filter=type_filter,
            signature_filter=signature_filter,
        )

    def load_index(self) -> bool:
        """
        Load a pre-built search index.

        Returns:
            True if index was loaded successfully, False otherwise
        """
        return self.engine.load_index()
