"""Module for semantic search using FAISS vector database."""

import os
import json
import logging
import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Union, Tuple

from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaissSearchEngine:
    """Class for semantic search using FAISS vector similarity."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        data_dir: str = "data/processed",
        use_gpu: bool = False,
    ):
        """
        Initialize the FAISS search engine.

        Args:
            model_name: Name of the SentenceTransformer model to use
            data_dir: Directory to store/load processed data and embeddings
            use_gpu: Whether to use GPU acceleration if available
        """
        self.model_name = model_name
        self.data_dir = data_dir
        self.use_gpu = use_gpu

        # Load the sentence transformer model
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

        # Initialize index variables
        self.index = None
        self.chunks = []
        self.index_metadata = {}

        # Create separate indices for code and documentation
        self.code_index = None
        self.code_chunks = []
        self.doc_index = None
        self.doc_chunks = []

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Initialize FAISS indices
        self._init_indices()

    def _init_indices(self):
        """Initialize FAISS indices for vector similarity search."""
        # Create a flat index using inner product (equivalent to cosine similarity on normalized vectors)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.code_index = faiss.IndexFlatIP(self.dimension)
        self.doc_index = faiss.IndexFlatIP(self.dimension)

        # Use GPU if requested and available
        if self.use_gpu:
            try:
                gpu_resources = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(gpu_resources, 0, self.index)
                self.code_index = faiss.index_cpu_to_gpu(
                    gpu_resources, 0, self.code_index
                )
                self.doc_index = faiss.index_cpu_to_gpu(
                    gpu_resources, 0, self.doc_index
                )
                logger.info("Using GPU acceleration for FAISS")
            except Exception as e:
                logger.warning(
                    f"Failed to use GPU acceleration: {str(e)}. Using CPU instead."
                )
                self.use_gpu = False

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Add chunks to the search index.

        Args:
            chunks: List of processed chunks to add
        """
        if not chunks:
            logger.warning("No chunks to add.")
            return

        # Get text representations for embeddings
        texts = [self._get_text_for_embedding(chunk) for chunk in chunks]

        # Generate embeddings (normalized for cosine similarity)
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(
            texts, normalize_embeddings=True, show_progress_bar=True, batch_size=32
        )

        # Add to the combined index
        self.index.add(np.array(embeddings).astype("float32"))
        self.chunks.extend(chunks)

        # Separate and add to content-specific indices
        code_chunks = []
        code_embeddings = []
        doc_chunks = []
        doc_embeddings = []

        for i, chunk in enumerate(chunks):
            content_type = chunk.get("content_type", "")
            if content_type == "code":
                code_chunks.append(chunk)
                code_embeddings.append(embeddings[i])
            elif content_type == "documentation":
                doc_chunks.append(chunk)
                doc_embeddings.append(embeddings[i])

        # Add to code index if we have code chunks
        if code_chunks:
            self.code_index.add(np.array(code_embeddings).astype("float32"))
            self.code_chunks.extend(code_chunks)

        # Add to documentation index if we have doc chunks
        if doc_chunks:
            self.doc_index.add(np.array(doc_embeddings).astype("float32"))
            self.doc_chunks.extend(doc_chunks)

        logger.info(
            f"Added {len(chunks)} chunks to index. "
            f"Total: {len(self.chunks)} chunks "
            f"({len(self.code_chunks)} code, {len(self.doc_chunks)} documentation)."
        )

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
            top_k: Number of top results to return
            content_filter: Filter by content type ('code' or 'documentation')
            min_score: Minimum similarity score to include in results

        Returns:
            List of search results with similarity scores
        """
        # Try to load index if not initialized
        if self.index is None or self.index.ntotal == 0:
            if not self._load_index():
                logger.warning("No index available. Please build the index first.")
                return []

        # Encode the query
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        query_embedding = np.array(query_embedding).astype("float32")

        # Determine which index to search based on content filter
        if content_filter == "code" and self.code_index.ntotal > 0:
            logger.info(f"Searching for '{query}' in code index only...")
            index_to_search = self.code_index
            chunks_to_search = self.code_chunks
        elif content_filter == "documentation" and self.doc_index.ntotal > 0:
            logger.info(f"Searching for '{query}' in documentation index only...")
            index_to_search = self.doc_index
            chunks_to_search = self.doc_chunks
        else:
            logger.info(f"Searching for '{query}' in all content...")
            index_to_search = self.index
            chunks_to_search = self.chunks

        # Search the index
        scores, indices = index_to_search.search(
            query_embedding, k=top_k * 2
        )  # Get more than needed for filtering

        # Build results
        results = []
        for i, (idx, score) in enumerate(zip(indices[0], scores[0])):
            # Break if we've collected enough results or if score is below threshold
            if len(results) >= top_k or score < min_score:
                break

            if idx < 0 or idx >= len(chunks_to_search):
                continue  # Skip invalid indices

            chunk = chunks_to_search[idx]
            result = {
                "chunk": chunk,
                "score": float(score),
                "content": self._get_display_content(chunk),
            }
            results.append(result)

        return results

    def build_index(self):
        """Build the search index and save it to disk."""
        if not self.chunks:
            logger.warning("No chunks to index.")
            return

        # Index is built incrementally in add_chunks,
        # so we just need to save the index here
        self._save_index()

        logger.info(
            f"Index built with {len(self.chunks)} chunks "
            f"({len(self.code_chunks)} code, {len(self.doc_chunks)} documentation)."
        )

    def _save_index(self):
        """Save the search indices and data to disk."""
        # Save metadata about the indices
        metadata = {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "total_chunks": len(self.chunks),
            "code_chunks": len(self.code_chunks),
            "doc_chunks": len(self.doc_chunks),
        }

        metadata_file = os.path.join(self.data_dir, "index_metadata.json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Save chunks
        self._save_chunks(self.chunks, "chunks.json")
        self._save_chunks(self.code_chunks, "code_chunks.json")
        self._save_chunks(self.doc_chunks, "doc_chunks.json")

        # Save indices
        self._save_faiss_index(self.index, "faiss_index.bin")
        self._save_faiss_index(self.code_index, "faiss_code_index.bin")
        self._save_faiss_index(self.doc_index, "faiss_doc_index.bin")

        logger.info(f"Saved index to {self.data_dir}")

    def _save_chunks(self, chunks: List[Dict[str, Any]], filename: str):
        """Save chunks to a JSON file."""
        file_path = os.path.join(self.data_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2)

    def _save_faiss_index(self, index, filename: str):
        """Save a FAISS index to disk."""
        file_path = os.path.join(self.data_dir, filename)
        if self.use_gpu:
            # Convert GPU index to CPU for storage
            index = faiss.index_gpu_to_cpu(index)
        faiss.write_index(index, file_path)

    def _load_index(self) -> bool:
        """
        Load the search indices from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        metadata_file = os.path.join(self.data_dir, "index_metadata.json")
        if not os.path.exists(metadata_file):
            logger.warning(f"Index metadata not found at {metadata_file}")
            return False

        try:
            # Load metadata
            with open(metadata_file, "r", encoding="utf-8") as f:
                self.index_metadata = json.load(f)

            # Check model compatibility
            if self.index_metadata.get("model_name") != self.model_name:
                logger.warning(
                    f"Index was built with a different model: {self.index_metadata.get('model_name')}"
                )

            # Load chunks
            self._load_chunks("chunks.json", target="all")
            self._load_chunks("code_chunks.json", target="code")
            self._load_chunks("doc_chunks.json", target="doc")

            # Load indices
            self._load_faiss_index("faiss_index.bin", target="all")
            self._load_faiss_index("faiss_code_index.bin", target="code")
            self._load_faiss_index("faiss_doc_index.bin", target="doc")

            logger.info(
                f"Loaded index with {len(self.chunks)} chunks "
                f"({len(self.code_chunks)} code, {len(self.doc_chunks)} documentation)."
            )
            return True

        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            return False

    def _load_chunks(self, filename: str, target: str):
        """Load chunks from a JSON file."""
        file_path = os.path.join(self.data_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)

                if target == "all":
                    self.chunks = chunks
                elif target == "code":
                    self.code_chunks = chunks
                elif target == "doc":
                    self.doc_chunks = chunks

    def _load_faiss_index(self, filename: str, target: str):
        """Load a FAISS index from disk."""
        file_path = os.path.join(self.data_dir, filename)
        if os.path.exists(file_path):
            index = faiss.read_index(file_path)

            # Convert to GPU if requested
            if self.use_gpu:
                try:
                    gpu_resources = faiss.StandardGpuResources()
                    index = faiss.index_cpu_to_gpu(gpu_resources, 0, index)
                except Exception as e:
                    logger.warning(
                        f"Failed to use GPU for index {filename}: {str(e)}. Using CPU."
                    )

            if target == "all":
                self.index = index
            elif target == "code":
                self.code_index = index
            elif target == "doc":
                self.doc_index = index

    def _get_text_for_embedding(self, chunk: Dict[str, Any]) -> str:
        """
        Get a text representation of a chunk for embedding.

        Args:
            chunk: Chunk data

        Returns:
            Text representation of the chunk
        """
        # Use processed text if available
        text = chunk.get("processed_text", "")

        if not text:
            chunk_type = chunk.get("type", "")

            if chunk_type == "function" or chunk_type == "method":
                # For functions and methods, use signature and docstring
                signature = chunk.get("function_signature", "")
                docstring = chunk.get("docstring", "")
                text = f"{signature}\n{docstring}"

            elif chunk_type == "class":
                # For classes, use name and docstring
                name = chunk.get("name", "")
                docstring = chunk.get("docstring", "")
                text = f"class {name}\n{docstring}"

            elif chunk_type == "section":
                # For sections, use title and content
                title = chunk.get("title", "")
                content = chunk.get("content", "")
                text = f"{title}\n{content}"

            elif chunk_type == "file":
                # For generic files, use name and content
                name = chunk.get("name", "")
                content = chunk.get("content", "")
                text = f"{name}\n{content}"

        # If still no text, use fallback
        if not text:
            text = str(chunk.get("content", chunk.get("docstring", "Empty chunk")))

        return text

    def _get_display_content(self, chunk: Dict[str, Any]) -> str:
        """
        Get a displayable string representation of a chunk.

        Args:
            chunk: Chunk to display

        Returns:
            Formatted string for display
        """
        chunk_type = chunk.get("type", "")

        if chunk_type == "function":
            signature = chunk.get("function_signature", "")
            docstring = chunk.get("docstring", "")
            file_path = chunk.get("file_path", "")
            line_no = chunk.get("lineno", "")

            return f"{signature}\n\n{docstring}\n\nLocation: {file_path}:{line_no}"

        elif chunk_type == "method":
            class_name = chunk.get("class_name", "")
            signature = chunk.get("method_signature", "")
            docstring = chunk.get("docstring", "")
            file_path = chunk.get("file_path", "")
            line_no = chunk.get("lineno", "")

            return f"Class: {class_name}\n{signature}\n\n{docstring}\n\nLocation: {file_path}:{line_no}"

        elif chunk_type == "class":
            name = chunk.get("name", "")
            docstring = chunk.get("docstring", "")
            file_path = chunk.get("file_path", "")
            line_no = chunk.get("lineno", "")

            return f"Class: {name}\n\n{docstring}\n\nLocation: {file_path}:{line_no}"

        elif chunk_type == "section":
            title = chunk.get("title", "")
            document_title = chunk.get("document_title", "")
            content = chunk.get("content", "")
            file_path = chunk.get("file_path", "")

            return f"Document: {document_title}\nSection: {title}\n\n{content}\n\nLocation: {file_path}"

        else:
            # Generic fallback
            return str(
                chunk.get("content", chunk.get("docstring", "No content available"))
            )
