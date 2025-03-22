.PHONY: clean test test-unit test-integration test-extractors test-processors test-search coverage coverage-html dev requirements extension extension-clean extension-package copy-python-src ready ready-no-setup

# Variables
PYTHON = python
PYTEST = pytest
PIP = uv pip
VSCE = vsce
NODE = node
NPM = npm

# Directories
SRC_DIR = src
TEST_DIR = tests
EXTENSION_DIR = extension
EXTENSION_PYTHON_DIR = $(EXTENSION_DIR)/python
EXTENSION_SCRIPTS_DIR = $(EXTENSION_DIR)/scripts

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

# Run type checking with mypy but don't fail on errors
typecheck-warn: deps
	$(PIP) install mypy
	-mypy $(SRC_DIR)

# Update requirements file
requirements:
	$(PIP) freeze > requirements.txt

# Development setup
dev: deps
	$(PIP) install black flake8 mypy
	$(PIP) install -e . 

# Extension commands

# Clean extension directories
extension-clean:
	rm -rf $(EXTENSION_DIR)/out
	rm -rf $(EXTENSION_PYTHON_DIR)/src
	rm -rf $(EXTENSION_PYTHON_DIR)/.venv
	rm -f $(EXTENSION_DIR)/*.vsix

# Copy Python source to extension
copy-python-src:
	@echo "Copying Python source to extension..."
	cd $(EXTENSION_DIR) && $(NODE) scripts/copy-python-src.js

# Compile TypeScript for extension
extension-compile:
	cd $(EXTENSION_DIR) && $(NPM) run compile

# Pack the extension
extension-package: extension-compile copy-python-src
	@echo "Packaging VS Code extension..."
	cd $(EXTENSION_DIR) && $(VSCE) package

# Set up extension environment
extension-setup:
	@echo "Setting up extension environment..."
	cd $(EXTENSION_PYTHON_DIR) && $(PYTHON) setup.py

# Test extension
extension-test: copy-python-src
	cd $(EXTENSION_PYTHON_DIR) && $(PYTHON) main.py --data-dir ~/.code-cognitio list-file-types

# Do everything
ready: clean format lint typecheck-warn test coverage extension-clean extension-package extension-setup
	@echo "=================================================="
	@echo "✅ Code Cognitio is ready!"
	@echo "✅ All tests passed"
	@echo "✅ Extension packaged at: $(EXTENSION_DIR)/code-cognitio-*.vsix"
	@echo "=================================================="
	@echo "Next steps:"
	@echo "1. Install the extension in VS Code"
	@echo "2. Run 'make extension-test' to verify extension functionality"
	@echo "=================================================="

# Do everything except extension setup
ready-no-setup: clean format lint typecheck-warn test coverage extension-clean extension-package
	@echo "=================================================="
	@echo "✅ Code Cognitio is ready!"
	@echo "✅ All tests passed"
	@echo "✅ Extension packaged at: $(EXTENSION_DIR)/code-cognitio-*.vsix"
	@echo "=================================================="
	@echo "Next steps:"
	@echo "1. Install the extension in VS Code"
	@echo "2. Run 'make extension-setup' to set up the extension environment"
	@echo "==================================================" 