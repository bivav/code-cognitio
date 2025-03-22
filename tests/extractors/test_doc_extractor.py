"""Tests for the DocExtractor class."""

import os
import pytest
from src.extractors.doc_extractor import DocExtractor


class TestDocExtractor:
    """Test class for DocExtractor."""

    def test_initialization(self):
        """Test that DocExtractor initializes properly."""
        extractor = DocExtractor()

        # Check that we have the expected supported extensions
        supported_extensions = extractor.get_supported_extensions()
        assert ".md" in supported_extensions
        assert ".rst" in supported_extensions

    def test_extract_from_markdown_file(self, temp_markdown_file):
        """Test extraction from a Markdown file."""
        extractor = DocExtractor()
        results = extractor.extract_from_file(temp_markdown_file)

        # We should get at least one chunk
        assert len(results) >= 1

        # Verify we have document sections
        found_types = {chunk["type"] for chunk in results}
        assert "section" in found_types

        # Find the "# Sample Document" section
        main_section = None
        for chunk in results:
            if (
                chunk.get("type") == "section"
                and chunk.get("title") == "Sample Document"
            ):
                main_section = chunk
                break

        assert main_section is not None
        assert (
            "This is a sample markdown document for testing extraction"
            in main_section["content"]
        )

        # Find the "## Installation" subsection
        installation_section = None
        for chunk in results:
            if chunk.get("type") == "section" and chunk.get("title") == "Installation":
                installation_section = chunk
                break

        assert installation_section is not None
        assert "To install the package" in installation_section["content"]
        assert "pip install sample-package" in installation_section["content"]

        # Find the "## Usage" subsection
        usage_section = None
        for chunk in results:
            if chunk.get("type") == "section" and chunk.get("title") == "Usage":
                usage_section = chunk
                break

        assert usage_section is not None
        assert "Here's how to use the package" in usage_section["content"]
        assert "from sample import Sample" in usage_section["content"]

    def test_get_supported_extensions(self):
        """Test the get_supported_extensions method."""
        extractor = DocExtractor()
        extensions = extractor.get_supported_extensions()

        # Check that we get a list of extensions
        assert isinstance(extensions, list)
        assert len(extensions) > 0

        # Check that common doc extensions are included
        assert ".md" in extensions
        assert ".rst" in extensions
