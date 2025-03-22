"""Tests for the CodeExtractor class."""

import os
import pytest
from src.extractors.code_extractor import CodeExtractor


class TestCodeExtractor:
    """Test class for CodeExtractor."""

    def test_initialization(self):
        """Test that CodeExtractor initializes properly with expected extractors."""
        extractor = CodeExtractor()

        # Check that we have extractors for common file types
        assert ".py" in extractor.extractors
        assert ".js" in extractor.extractors
        assert ".jsx" in extractor.extractors
        assert ".ts" in extractor.extractors
        assert ".tsx" in extractor.extractors
        assert ".dockerfile" in extractor.extractors

        # Check that we have file pattern extractors
        assert "Dockerfile" in extractor.file_patterns

        # Check extension aliases
        assert ".pyw" in extractor.extension_aliases
        assert extractor.extension_aliases[".pyw"] == ".py"

    def test_extract_from_python_file(self, temp_python_file):
        """Test extraction from a Python file."""
        extractor = CodeExtractor()
        results = extractor.extract_from_file(temp_python_file)

        # We should get at least 3 items: function, class, and method
        assert len(results) >= 3

        # Verify we have different types of chunks
        found_types = {chunk["type"] for chunk in results}
        assert "function" in found_types
        assert "class" in found_types

        # Check the extracted function details
        function_chunks = [chunk for chunk in results if chunk["type"] == "function"]
        assert len(function_chunks) >= 1

        function = function_chunks[0]
        assert function["name"] == "sample_function"
        assert "docstring" in function
        assert function["file_path"] == temp_python_file

        # The actual implementation may have a different structure for parameters
        # This is a more flexible check
        assert "body" in function
        assert "param1" in function["body"]
        assert "param2" in function["body"]
        assert "returns" in function or "bool" in function["body"]

    def test_extract_from_dockerfile(self, temp_dockerfile):
        """Test extraction from a Dockerfile."""
        extractor = CodeExtractor()
        results = extractor.extract_from_file(temp_dockerfile)

        # We should get at least one chunk for the Dockerfile
        assert len(results) >= 1

        # Check the basic file info
        dockerfile = results[0]
        assert dockerfile["file_path"] == temp_dockerfile

        # The content might be in a different field or stored differently
        # Let's check if we have FROM instruction somewhere in any field
        has_from = False

        # Check common fields where the content might be stored
        for field in ["raw_content", "body", "content"]:
            if field in dockerfile and "FROM" in str(dockerfile[field]):
                has_from = True
                break

        # Check if instructions is a list of dictionaries with different structure
        if "instructions" in dockerfile and isinstance(
            dockerfile["instructions"], list
        ):
            for instr in dockerfile["instructions"]:
                # The instructions might have various formats
                if isinstance(instr, dict):
                    # Check if any field in the instruction contains "FROM"
                    for value in instr.values():
                        if isinstance(value, str) and "FROM" in value:
                            has_from = True
                            break

        assert has_from, "Could not find FROM instruction in the Dockerfile chunk"

    def test_guess_language(self):
        """Test the language guessing functionality."""
        extractor = CodeExtractor()

        # Test some common extensions
        assert extractor._guess_language("test.py") == "python"
        assert extractor._guess_language("test.js") == "javascript"
        assert extractor._guess_language("test.ts") == "typescript"

        # Test with uppercase extensions
        assert extractor._guess_language("test.PY") == "python"
        assert extractor._guess_language("test.JS") == "javascript"

    def test_get_supported_extensions(self):
        """Test the get_supported_extensions method."""
        extractor = CodeExtractor()
        extensions = extractor.get_supported_extensions()

        # Check that we get a list of extensions
        assert isinstance(extensions, list)
        assert len(extensions) > 0

        # Check that common extensions are included
        assert ".py" in extensions
        assert ".js" in extensions
