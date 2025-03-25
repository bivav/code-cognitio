"""Service for managing code search functionality."""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from .file_processor import FileProcessor
from ..search.faiss_search import FaissSearchEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchService:
    """Service class for managing code search operations."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        data_dir: str = "data/processed",
        use_gpu: bool = False,
    ):
        """
        Initialize the search service.

        Args:
            model_name: Name of the sentence transformer model to use
            data_dir: Directory for storing processed data
            use_gpu: Whether to use GPU acceleration
        """
        self.model_name: str = model_name
        self.data_dir: str = data_dir
        self.use_gpu: bool = use_gpu

        # Initialize search engine
        self.engine: FaissSearchEngine = FaissSearchEngine(
            model_name=model_name,
            data_dir=data_dir,
            use_gpu=use_gpu,
        )

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

    def build_index(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Build the search index from code chunks.

        Args:
            chunks: List of code chunks to index

        Returns:
            True if index was built successfully
        """
        try:
            # Add chunks to the search engine
            self.engine.add_chunks(chunks)
            return True
        except Exception as e:
            logger.error(f"Failed to build index: {str(e)}")
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
        Search for code chunks matching the query.

        Args:
            query: Search query
            top_k: Number of results to return
            content_filter: Filter by content type
            min_score: Minimum similarity score
            type_filter: Filter by code type
            signature_filter: Filter by function/method signature

        Returns:
            List of matching code chunks with scores
        """
        try:
            # Perform search
            results = self.engine.search(
                query=query,
                top_k=top_k,
                content_filter=content_filter,
                min_score=min_score,
            )

            # Apply additional filters
            if type_filter or signature_filter:
                filtered_results = []
                for result in results:
                    chunk = result["chunk"]

                    # Check type filter
                    if type_filter and chunk.get("type") != type_filter:
                        continue

                    # Check signature filter
                    if signature_filter:
                        signature_match = True
                        for key, value in signature_filter.items():
                            if chunk.get(key) != value:
                                signature_match = False
                                break
                        if not signature_match:
                            continue

                    filtered_results.append(result)
                return filtered_results

            return results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    def load_index(self) -> bool:
        """
        Load the search index from disk.

        Returns:
            True if index was loaded successfully
        """
        try:
            return self.engine._load_index()
        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}")
            return False

    def get_index_status(self) -> str:
        """
        Get the current status of the search index.

        Returns:
            Status message describing the index state
        """
        index_file = os.path.join(self.data_dir, "faiss_index.bin")
        if not os.path.exists(index_file):
            return "No index found. Please build the index first."

        # Try to load the index to verify it's valid
        if not self.load_index():
            return "Index exists but could not be loaded."

        # Return index information
        try:
            index_size = os.path.getsize(index_file)
            num_chunks = len(self.engine.chunks)
            return f"Index is ready. Size: {index_size/1024/1024:.2f} MB, Chunks: {num_chunks}, Model: {self.model_name}"
        except Exception as e:
            return f"Index exists but encountered an error: {str(e)}"
