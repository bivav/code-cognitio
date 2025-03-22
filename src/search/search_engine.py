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
        # Get basic search results from the backend
        results = self.backend.search(
            query=query,
            top_k=top_k * 3,  # Get more results to filter locally
            content_filter=content_filter,
            min_score=min_score,
        )

        # Apply additional filters locally
        filtered_results = []
        for result in results:
            chunk = result.get("chunk", {})

            # Apply type filter if specified
            if type_filter and chunk.get("type") != type_filter:
                continue

            # Apply signature filter if specified
            if signature_filter and not self._matches_signature_filter(
                chunk, signature_filter
            ):
                continue

            filtered_results.append(result)

            # Stop once we have enough results
            if len(filtered_results) >= top_k:
                break

        return filtered_results[:top_k]

    def _matches_signature_filter(
        self, chunk: Dict[str, Any], signature_filter: Dict[str, str]
    ) -> bool:
        """
        Check if a chunk matches the given signature filter.

        Args:
            chunk: The chunk to check
            signature_filter: The signature filter to apply

        Returns:
            True if the chunk matches the filter, False otherwise
        """
        # For non-function chunks, no signature to match
        if chunk.get("type") not in ["function", "method"]:
            return False

        # Get parameters list from either "parameters" or "params" field
        parameters = chunk.get("parameters", chunk.get("params", []))

        # Check parameter type
        if "param_type" in signature_filter:
            param_type = signature_filter["param_type"]
            found = False
            for param in parameters:
                # Case insensitive matching for parameter type
                param_type_value = param.get("type", "")
                if param_type_value and param_type.lower() in param_type_value.lower():
                    found = True
                    break
            if not found:
                return False

        # Check parameter name
        if "param_name" in signature_filter:
            param_name = signature_filter["param_name"]
            found = False
            for param in parameters:
                # Case insensitive matching for parameter name
                param_name_value = param.get("name", "")
                if param_name_value and param_name.lower() in param_name_value.lower():
                    found = True
                    break
            if not found:
                return False

        # Check return type
        if "return_type" in signature_filter:
            return_type = signature_filter["return_type"]
            function_return_type = chunk.get("return_type", chunk.get("returns", ""))
            # Case insensitive matching for return type
            if (
                not function_return_type
                or return_type.lower() not in function_return_type.lower()
            ):
                return False

        return True

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
