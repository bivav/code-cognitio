"""Pytest configuration for the code-cognitio tests."""

import os
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_python_file(temp_dir):
    """Create a temporary Python file for testing."""
    file_path = os.path.join(temp_dir, "test_file.py")
    with open(file_path, "w") as f:
        f.write(
            """
def sample_function(param1: str, param2: int = 0) -> bool:
    \"\"\"
    Sample function for testing extraction.

    Args:
        param1: First parameter description
        param2: Second parameter description

    Returns:
        A boolean result
    \"\"\"
    return True

class SampleClass:
    \"\"\"Sample class for testing class extraction.\"\"\"

    def __init__(self, name: str):
        \"\"\"Initialize with a name.\"\"\"
        self.name = name

    def sample_method(self, value: int) -> str:
        \"\"\"
        Sample method for testing method extraction.

        Args:
            value: An integer value

        Returns:
            A string representation
        \"\"\"
        return f"{self.name}: {value}"
"""
        )
    return file_path


@pytest.fixture
def temp_markdown_file(temp_dir):
    """Create a temporary Markdown file for testing."""
    file_path = os.path.join(temp_dir, "test_doc.md")
    with open(file_path, "w") as f:
        f.write(
            """
# Sample Document

This is a sample markdown document for testing extraction.

## Installation

To install the package:

```bash
pip install sample-package
```

## Usage

Here's how to use the package:

```python
from sample import Sample

sample = Sample()
sample.run()
```
"""
        )
    return file_path


@pytest.fixture
def temp_dockerfile(temp_dir):
    """Create a temporary Dockerfile for testing."""
    file_path = os.path.join(temp_dir, "Dockerfile")
    with open(file_path, "w") as f:
        f.write(
            """
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
"""
        )
    return file_path
