# Tests for Code Cognitio

This directory contains tests for the Code Cognitio semantic search system.

## Test Structure

- `conftest.py`: Contains shared pytest fixtures
- `extractors/`: Tests for the extraction modules
- `processors/`: Tests for the text processing modules
- `search/`: Tests for the search engine components
- `test_integration.py`: Integration tests for the end-to-end system

## Running Tests

You can run the tests using the Makefile at the root of the project:

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run only integration tests
make test-integration

# Run tests with coverage report
make coverage
```

## Test Data

The tests use temporary files and directories created by the fixtures in `conftest.py`. These are automatically cleaned up after the tests run.

## Adding New Tests

When adding new functionality to the codebase, please also add corresponding tests:

1. For new extractors, add tests to `tests/extractors/`
2. For new processors, add tests to `tests/processors/`
3. For new search components, add tests to `tests/search/`
4. For features that span multiple components, add integration tests to `test_integration.py`
