"""Integration tests for the code-cognitio system."""

import os
import tempfile
import pytest

from src.extractors.code_extractor import CodeExtractor
from src.extractors.doc_extractor import DocExtractor
from src.processors.text_processor import TextProcessor
from src.search.search_engine import SearchEngine


class TestIntegration:
    """Integration tests for the entire extraction, processing, and search pipeline."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_end_to_end_python(self, temp_python_file, temp_data_dir):
        """Test the end-to-end process with a Python file."""
        # Extract chunks from the Python file
        code_extractor = CodeExtractor()
        chunks = code_extractor.extract_from_file(temp_python_file)

        # Process the chunks
        text_processor = TextProcessor(use_spacy=False)  # Disable spaCy for testing
        processed_chunks = []
        for chunk in chunks:
            processed_chunk = text_processor.process_chunk(chunk)
            processed_chunks.append(processed_chunk)

        # Build a search index
        search_engine = SearchEngine(data_dir=temp_data_dir)
        search_engine.add_chunks(processed_chunks)
        search_engine.build_index()

        # Verify index was created
        assert os.path.exists(os.path.join(temp_data_dir, "chunks.json"))

        # Test simple search
        results = search_engine.search("sample function")
        assert len(results) > 0

        # Check that we get some results
        assert isinstance(results, list)
        assert len(results) > 0

        # Check result structure
        for result in results:
            assert "chunk" in result
            assert "score" in result

    def test_end_to_end_markdown(self, temp_markdown_file, temp_data_dir):
        """Test the end-to-end process with a Markdown file."""
        # Extract chunks from the Markdown file
        doc_extractor = DocExtractor()
        chunks = doc_extractor.extract_from_file(temp_markdown_file)

        # Process the chunks
        text_processor = TextProcessor(use_spacy=False)  # Disable spaCy for testing
        processed_chunks = []
        for chunk in chunks:
            processed_chunk = text_processor.process_chunk(chunk)
            processed_chunks.append(processed_chunk)

        # Build a search index
        search_engine = SearchEngine(data_dir=temp_data_dir)
        search_engine.add_chunks(processed_chunks)
        search_engine.build_index()

        # Verify index was created
        assert os.path.exists(os.path.join(temp_data_dir, "chunks.json"))

        # Test searching for installation instructions
        results = search_engine.search("install package")
        assert len(results) > 0

        # Verify we get results with the expected content
        found_install_section = False
        for result in results:
            chunk = result["chunk"]
            content = result.get("content", "")
            if "pip install" in content or (
                chunk.get("content") and "pip install" in chunk.get("content", "")
            ):
                found_install_section = True
                break

        assert found_install_section

    def test_mixed_content_indexing(
        self, temp_python_file, temp_markdown_file, temp_data_dir
    ):
        """Test indexing and searching across different content types."""
        # Extract chunks from both files
        code_extractor = CodeExtractor()
        doc_extractor = DocExtractor()

        code_chunks = code_extractor.extract_from_file(temp_python_file)
        doc_chunks = doc_extractor.extract_from_file(temp_markdown_file)

        # Process all chunks
        text_processor = TextProcessor(use_spacy=False)
        processed_chunks = []

        for chunk in code_chunks + doc_chunks:
            processed_chunk = text_processor.process_chunk(chunk)
            processed_chunks.append(processed_chunk)

        # Build a search index
        search_engine = SearchEngine(data_dir=temp_data_dir)
        search_engine.add_chunks(processed_chunks)
        search_engine.build_index()

        # Test search across content types
        results = search_engine.search("sample")
        assert len(results) > 0

        # Basic validation of search functionality
        assert isinstance(results, list)
        assert len(results) > 0
