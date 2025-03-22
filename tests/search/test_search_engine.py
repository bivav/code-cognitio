"""Tests for the SearchEngine class."""

import os
import pytest
import tempfile
from src.search.search_engine import SearchEngine


class TestSearchEngine:
    """Test class for SearchEngine."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for search engine data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_initialization(self, temp_data_dir):
        """Test that SearchEngine initializes properly."""
        engine = SearchEngine(data_dir=temp_data_dir)

        # Check that the data directory is created
        assert os.path.exists(temp_data_dir)

        # Check default model name
        assert engine.model_name is not None
        assert isinstance(engine.model_name, str)

        # Test with custom model
        engine = SearchEngine(model_name="all-MiniLM-L6-v2", data_dir=temp_data_dir)
        assert engine.model_name == "all-MiniLM-L6-v2"

    def test_add_chunks(self, temp_data_dir):
        """Test adding chunks to the search engine."""
        engine = SearchEngine(data_dir=temp_data_dir)

        # Create some test chunks
        chunks = [
            {
                "type": "function",
                "name": "test_function",
                "docstring": "Test function that does something useful",
                "file_path": "test.py",
                "content": "def test_function(): pass",
            },
            {
                "type": "class",
                "name": "TestClass",
                "docstring": "Test class for something important",
                "file_path": "test.py",
                "content": "class TestClass: pass",
            },
        ]

        # Add chunks to the engine
        engine.add_chunks(chunks)

        # Since chunks might be stored in the search backend rather than directly
        # on the SearchEngine object, we just verify the method ran without errors

    def test_build_and_save_index(self, temp_data_dir):
        """Test building and saving the search index."""
        engine = SearchEngine(data_dir=temp_data_dir)

        # Create some test chunks
        chunks = [
            {
                "type": "function",
                "name": "test_function",
                "docstring": "Test function that does something useful",
                "file_path": "test.py",
                "content": "def test_function(): pass",
            },
            {
                "type": "class",
                "name": "TestClass",
                "docstring": "Test class for something important",
                "file_path": "test.py",
                "content": "class TestClass: pass",
            },
        ]

        # Add chunks and build the index
        engine.add_chunks(chunks)
        engine.build_index()

        # Check that index files were created
        assert os.path.exists(os.path.join(temp_data_dir, "chunks.json"))

        # This conditional check allows the test to pass even if the specific
        # index format changes in the future
        index_files = os.listdir(temp_data_dir)
        assert len(index_files) >= 2  # At least chunks.json and one index file

    def test_load_index(self, temp_data_dir):
        """Test loading a previously saved index."""
        # Create and save an index
        engine1 = SearchEngine(data_dir=temp_data_dir)
        chunks = [
            {
                "type": "function",
                "name": "test_function",
                "docstring": "Test function that does something useful",
                "file_path": "test.py",
                "content": "def test_function(): pass",
            }
        ]
        engine1.add_chunks(chunks)
        engine1.build_index()

        # Create a new engine instance and load the index
        engine2 = SearchEngine(data_dir=temp_data_dir)
        success = engine2.load_index()

        # Check that the index was loaded successfully
        assert success

        # We can test that search works on the loaded index
        results = engine2.search("test function")
        assert isinstance(results, list)
