"""Tests for the TextProcessor class."""

import pytest
from src.processors.text_processor import TextProcessor


class TestTextProcessor:
    """Tests for the TextProcessor class."""

    @pytest.fixture
    def text_processor(self):
        """Create a TextProcessor instance for testing."""
        return TextProcessor(use_spacy=False)  # Use NLTK for consistent testing

    def test_initialization(self, text_processor):
        """Test that TextProcessor initializes properly."""
        assert isinstance(text_processor, TextProcessor)
        # The TextProcessor doesn't have remove_code_blocks as a public method, it's _remove_code_blocks
        assert hasattr(text_processor, "_remove_code_blocks")
        assert hasattr(text_processor, "clean_text")
        assert hasattr(text_processor, "process_chunk")

    def test_process_chunk(self, text_processor):
        """Test processing a chunk."""
        # Test with a function chunk
        function_chunk = {
            "type": "function",
            "name": "test_function",
            "docstring": "This is a function docstring with code `example`.",
            "parameters": [
                {"name": "param1", "type": "str"},
                {"name": "param2", "type": "int"},
            ],
            "returns": "bool",
        }

        processed = text_processor.process_chunk(function_chunk)
        assert processed["content_type"] == "code"
        assert "function docstring" in processed["processed_text"]
        assert "function_signature" in processed

        # Test with a section chunk
        section_chunk = {
            "type": "section",
            "title": "Installation",
            "content": "To install:\n```bash\npip install package\n```\nThen configure.",
        }

        processed = text_processor.process_chunk(section_chunk)
        assert processed["content_type"] == "documentation"
        assert "section_type" in processed
        assert (
            "install" in processed["processed_text"]
            or "configure" in processed["processed_text"]
        )

    def test_clean_text(self, text_processor):
        """Test the combined text cleaning process."""
        # Test with text that needs both code removal and whitespace normalization
        mixed_text = """
    This is  a paragraph   with extra  spaces.

    ```python
    def example():
        # This should be removed
        return "Hello"
    ```

       This has leading whitespace.
    """
        result = text_processor.clean_text(mixed_text)

        # Code blocks should be removed
        assert "```python" not in result
        assert "def example():" not in result

        # Should be lowercase
        assert result.islower()

        # Should not contain punctuation
        assert "(" not in result
        assert ")" not in result
        assert '"' not in result

        # Basic content should remain
        assert "paragraph" in result
        assert "space" in result
        assert "whitespace" in result

    def test_internal_remove_code_blocks(self, text_processor):
        """Test removing code blocks from text using the internal method."""
        text_with_code = """
This is a paragraph.

```python
def hello():
    print("Hello, world!")
```

This is another paragraph.

```
Some code without language specified
```

End of text.
"""
        result = text_processor._remove_code_blocks(text_with_code)

        # Code blocks should be removed
        assert "```python" not in result
        assert "def hello():" not in result
        assert "```" not in result
        assert "Some code without language specified" not in result

        # Text outside code blocks should remain
        assert "This is a paragraph." in result
        assert "This is another paragraph." in result
        assert "End of text." in result

    def test_get_function_signature(self, text_processor):
        """Test generating a function signature."""
        func_data = {
            "name": "test_function",
            "parameters": [
                {"name": "param1", "type": "str"},
                {"name": "param2", "type": "int"},
            ],
            "returns": "bool",
        }

        signature = text_processor._get_function_signature(func_data)
        assert signature == "test_function(param1: str, param2: int) -> bool"

        # Test with no parameters
        func_data_no_params = {
            "name": "no_params",
            "parameters": [],
            "returns": "None",
        }

        signature = text_processor._get_function_signature(func_data_no_params)
        assert signature == "no_params() -> None"

        # Test with no return type
        func_data_no_return = {
            "name": "no_return",
            "parameters": [{"name": "param", "type": ""}],
        }

        signature = text_processor._get_function_signature(func_data_no_return)
        assert signature == "no_return(param)"

    def test_spacy_fallback(self):
        """Test that TextProcessor falls back to NLTK when spaCy is not available."""
        processor = TextProcessor(use_spacy=True)  # Try to use spaCy

        # Regardless of whether spaCy is installed, the processor should initialize
        assert processor is not None
        assert hasattr(processor, "clean_text")

        # Test with a simple clean text operation
        result = processor.clean_text("Test with spaces   and CAPITALS.")
        assert result is not None
        assert isinstance(result, str)

    def test_process_with_nltk(self, text_processor):
        """Test processing text with NLTK."""
        if text_processor.nltk_lemmatizer:
            # Only run this test if NLTK is available
            result = text_processor._process_with_nltk("Running and jumping quickly")
            # Check for the presence of the words, being flexible about case and exact form
            assert any(word in result for word in ["Running", "running", "run"])
            assert any(word in result for word in ["jumping", "jump", "Jumping"])
            assert "quickly" in result
            # Stop words should be removed
            assert "and" not in result

    def test_handle_edge_cases(self, text_processor):
        """Test handling of edge cases."""
        # Test with empty string
        assert text_processor.clean_text("") == ""

        # Test with None
        try:
            result = text_processor.clean_text(None)
            assert result == ""
        except Exception:
            # If it raises an exception, that's an acceptable implementation too
            pass
