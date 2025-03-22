.PHONY: clean test test-unit test-integration test-extractors test-processors test-search coverage coverage-html dev requirements

# Variables
PYTHON = python
PYTEST = pytest
PIP = uv pip

# Directories
SRC_DIR = src
TEST_DIR = tests

# Default target
all: test

# Install dependencies
deps:
	$(PIP) install -U pytest pytest-cov

# Run all tests
test: deps
	$(PYTEST) $(TEST_DIR) -v

# Run only unit tests
test-unit: deps
	$(PYTEST) $(TEST_DIR)/extractors $(TEST_DIR)/processors $(TEST_DIR)/search -v

# Run only integration tests
test-integration: deps
	$(PYTEST) $(TEST_DIR)/test_integration.py -v

# Run only extractor tests
test-extractors: deps
	$(PYTEST) $(TEST_DIR)/extractors -v

# Run only processor tests
test-processors: deps
	$(PYTEST) $(TEST_DIR)/processors -v

# Run only search tests
test-search: deps
	$(PYTEST) $(TEST_DIR)/search -v

# Run tests with coverage report
coverage: deps
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=term $(TEST_DIR)

# Run tests with HTML coverage report
coverage-html: deps
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=html $(TEST_DIR)

# Clean up generated files
clean:
	rm -rf .coverage htmlcov
	rm -rf .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Check code style with flake8
lint: deps
	$(PIP) install flake8
	flake8 $(SRC_DIR) $(TEST_DIR)

# Format code with black
format: deps
	$(PIP) install black
	black $(SRC_DIR) $(TEST_DIR)

# Run type checking with mypy
typecheck: deps
	$(PIP) install mypy
	mypy $(SRC_DIR)

# Update requirements file
requirements:
	$(PIP) freeze > requirements.txt

# Development setup
dev: deps
	$(PIP) install black flake8 mypy
	$(PIP) install -e . 