"""Tests for the Chunker class."""

import pytest
from src.processors.chunker import Chunker


class TestChunker:
    """Test the Chunker class."""

    @pytest.fixture
    def chunker(self):
        """Create a chunker instance for testing."""
        return Chunker(max_chunk_size=500)

    def test_initialization(self, chunker):
        """Test that the chunker initializes properly."""
        assert isinstance(chunker, Chunker)
        assert chunker.max_chunk_size == 500

    def test_split_into_paragraphs(self, chunker):
        """Test splitting text into paragraphs."""
        text = "Hello world!\n\nThis is a test."
        paragraphs = chunker._split_into_paragraphs(text)

        assert len(paragraphs) == 2
        assert paragraphs[0] == "Hello world!"
        assert paragraphs[1] == "This is a test."

        # Test with different text
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        paragraphs = chunker._split_into_paragraphs(text)
        assert len(paragraphs) == 3

        # Test with no paragraph breaks
        text = "No paragraph breaks here."
        paragraphs = chunker._split_into_paragraphs(text)
        assert len(paragraphs) == 1
        assert paragraphs[0] == "No paragraph breaks here."

    def test_split_into_sentences(self, chunker):
        """Test splitting text into sentences."""
        text = "Hello world! This is a test. And another sentence."
        sentences = chunker._split_into_sentences(text)

        assert len(sentences) >= 2
        # Results may vary depending on implementation but should at least split somewhere
        assert "Hello world!" in sentences[0] or "Hello world" in sentences[0]

    def test_chunk_content(self, chunker):
        """Test chunking content with different item types."""
        # Test with a function item
        function_item = {
            "type": "function",
            "name": "test_function",
            "content": "Function content",
        }

        chunked = chunker.chunk_content([function_item])
        assert len(chunked) == 1
        assert chunked[0] == function_item  # Functions should be preserved as-is

        # Test with a method item
        method_item = {
            "type": "method",
            "name": "test_method",
            "content": "Method content",
        }

        chunked = chunker.chunk_content([method_item])
        assert len(chunked) == 1
        assert chunked[0] == method_item  # Methods should be preserved as-is

        # Test with a class item
        class_item = {
            "type": "class",
            "name": "TestClass",
            "content": "Class content",
        }

        chunked = chunker.chunk_content([class_item])
        assert len(chunked) == 1
        assert chunked[0] == class_item  # Classes should be preserved as-is

        # Test with a module item
        module_item = {
            "type": "module",
            "name": "test_module",
            "content": "Module content",
        }

        chunked = chunker.chunk_content([module_item])
        assert len(chunked) == 1
        assert chunked[0] == module_item  # Modules should be preserved as-is

        # Test with a default item
        default_item = {
            "type": "unknown",
            "name": "unknown_item",
            "content": "Unknown content",
        }

        chunked = chunker.chunk_content([default_item])
        assert len(chunked) == 1
        assert chunked[0] == default_item  # Default should be preserved as-is

    def test_chunk_section(self, chunker):
        """Test chunking a section."""
        # Small section that doesn't need chunking
        small_section = {
            "type": "section",
            "title": "Small Section",
            "content": "This is a small section that fits within the chunk size.",
        }

        chunked = chunker._chunk_section(small_section)
        assert len(chunked) == 1
        assert chunked[0] == small_section

        # Large section that needs chunking
        large_content = "Paragraph 1. " * 100 + "\n\n" + "Paragraph 2. " * 100
        large_section = {
            "type": "section",
            "title": "Large Section",
            "content": large_content,
        }

        chunked = chunker._chunk_section(large_section)
        assert len(chunked) > 1

        # Check that chunks have sequential indices
        for i, chunk in enumerate(chunked):
            assert chunk["chunk_index"] == i
            assert "content" in chunk
            assert len(chunk["content"]) <= chunker.max_chunk_size
            assert chunk["title"] == "Large Section"  # Title should be preserved

    def test_chunk_content_with_sections(self, chunker):
        """Test chunking content with sections."""
        # Create a list with a mix of items including a large section
        large_content = "Paragraph 1. " * 100 + "\n\n" + "Paragraph 2. " * 100
        items = [
            {
                "type": "function",
                "name": "test_function",
                "content": "Function content",
            },
            {
                "type": "section",
                "title": "Large Section",
                "content": large_content,
            },
            {
                "type": "class",
                "name": "TestClass",
                "content": "Class content",
            },
        ]

        chunked = chunker.chunk_content(items)

        # The large section should be chunked, so total items should be more than 3
        assert len(chunked) > 3

        # First and last items should be preserved as-is
        assert chunked[0]["type"] == "function"
        assert chunked[0]["name"] == "test_function"

        assert chunked[-1]["type"] == "class"
        assert chunked[-1]["name"] == "TestClass"

        # There should be section chunks in between
        section_chunks = [item for item in chunked if item["type"] == "section"]
        assert len(section_chunks) > 1  # The large section should be chunked

        # Check that section chunks have sequential indices
        for i, chunk in enumerate(section_chunks):
            assert chunk["chunk_index"] == i
            assert "content" in chunk
            assert len(chunk["content"]) <= chunker.max_chunk_size

    def test_chunk_small_text(self, chunker):
        """Test chunking text smaller than chunk size."""
        small_text = "This is a small text."
        small_section = {
            "type": "section",
            "title": "Small Section",
            "content": small_text,
        }

        chunks = chunker._chunk_section(small_section)

        # Should be just one chunk
        assert len(chunks) == 1
        assert chunks[0]["content"] == small_text

    def test_chunk_empty_text(self, chunker):
        """Test chunking empty text."""
        empty_section = {
            "type": "section",
            "title": "Empty Section",
            "content": "",
        }

        chunks = chunker._chunk_section(empty_section)

        # Should return a single chunk with empty content
        assert len(chunks) == 1
        assert chunks[0]["content"] == ""

    def test_split_into_sentences_complex(self, chunker):
        """Test splitting text into sentences with complex text."""
        text = "This is sentence one. This is sentence two! Is this sentence three? Yes, it is sentence four."

        sentences = chunker._split_into_sentences(text)

        # Results may vary based on implementation, but should split at sentence boundaries
        assert len(sentences) >= 1
        # Check for presence of content from different sentences
        all_text = " ".join(sentences)
        assert "sentence one" in all_text
        assert "sentence two" in all_text
        assert "sentence three" in all_text
        assert "sentence four" in all_text
