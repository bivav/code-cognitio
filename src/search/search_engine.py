"""Search engine module for semantic search in code repositories."""

import os
import logging
from typing import List, Dict, Any, Optional, Union

from src.search.faiss_search import FaissSearchEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchEngine:
    """Search engine for semantic search in code repositories."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        data_dir: str = "data/processed",
        use_gpu: bool = False,
        use_faiss: bool = True,
    ):
        """
        Initialize the search engine.

        Args:
            model_name: Name of the embedding model to use
            data_dir: Directory to store processed data
            use_gpu: Whether to use GPU for embedding and search
            use_faiss: Whether to use FAISS for vector search
        """
        self.model_name = model_name
        self.data_dir = data_dir
        self.use_gpu = use_gpu
        self.use_faiss = use_faiss

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Initialize search backend
        self._init_search_backend()

        logger.info(
            f"Initialized SearchEngine with model {model_name} {'with GPU' if use_gpu else 'without GPU'}"
        )

    def _init_search_backend(self):
        """Initialize the search backend based on configuration."""
        if self.use_faiss:
            logger.info("Using FAISS search backend")
            self.backend = FaissSearchEngine(
                model_name=self.model_name, data_dir=self.data_dir, use_gpu=self.use_gpu
            )
        else:
            # Fallback to a simpler vector search if FAISS is not available
            raise NotImplementedError("Non-FAISS backend is not implemented yet")

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Add processed chunks to the search index.

        Args:
            chunks: List of processed document chunks
        """
        self.backend.add_chunks(chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        content_filter: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search for chunks relevant to the query.

        Args:
            query: Search query
            top_k: Number of results to return
            content_filter: Filter results by content type ('code' or 'documentation')
            min_score: Minimum similarity score threshold

        Returns:
            List of search results with similarity scores
        """
        return self.backend.search(
            query=query, top_k=top_k, content_filter=content_filter, min_score=min_score
        )

    def build_index(self):
        """Build the search index from added chunks."""
        self.backend.build_index()

    def load_index(self) -> bool:
        """
        Load a pre-built search index.

        Returns:
            True if index was loaded successfully, False otherwise
        """
        if hasattr(self.backend, "_load_index"):
            return self.backend._load_index()
        return False
