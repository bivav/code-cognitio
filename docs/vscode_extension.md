# VS Code Extension User Guide

Code Cognitio provides a Visual Studio Code extension that integrates semantic code search directly into your development environment. This guide explains how to install, configure, and use the extension.

## Installation

### Prerequisites

Before installing the extension, ensure you have the following requirements:

1. Visual Studio Code version 1.60.0 or higher
2. Python 3.8 or higher
3. Code Cognitio project installed in your workspace

### Extension Installation

You can install the Code Cognitio extension in two ways:

#### From VS Code Marketplace

1. Open VS Code
2. Go to the Extensions view (Ctrl+Shift+X or Cmd+Shift+X on macOS)
3. Search for "Code Cognitio"
4. Click "Install"

#### From VSIX File

1. Download the `.vsix` extension file
2. Open VS Code
3. Go to the Extensions view
4. Click on the "..." menu in the top-right corner
5. Select "Install from VSIX..."
6. Navigate to the downloaded file and select it

## Getting Started

After installing the extension, you'll need to build a search index before you can start searching:

1. Open a project folder in VS Code that contains the code you want to search
2. Open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P on macOS)
3. Type and select "Code Cognitio: Build Search Index"
4. Configure the indexing options:
   - Specify file types to include (or use "all" for all supported types)
   - Specify file types to exclude (e.g., "min.js,bundle.js,lock")
5. Wait for the indexing process to complete (a notification will appear when done)

## Searching Code

Once you've built an index, you can perform semantic searches:

1. Open the Command Palette
2. Type and select "Code Cognitio: Search Code"
3. Enter your natural language search query (e.g., "how to authenticate users")
4. Optionally select a content filter:
   - All Content: Search both code and documentation
   - Code Only: Search only in code files
   - Documentation Only: Search only in documentation files
5. The search results will appear in the Code Cognitio panel on the sidebar

### Working with Search Results

The search results panel displays matches from your codebase:

- Each result shows the file path, similarity score, and content snippet
- Click on a file path to open the file and navigate to the specific line
- Results are sorted by relevance (similarity score)

## Tips for Effective Searching

- Use natural language queries that describe what you're looking for
- Be specific but concise in your queries
- Try different phrasings if you don't get the expected results
- Filter results by content type to narrow down your search
- Rebuild the index after significant changes to your codebase

## Troubleshooting

Common issues and solutions:

### Extension Can't Find Python

Make sure you have a virtual environment set up in your workspace with all the required dependencies. The extension will use the Python from your workspace's venv if available, otherwise it falls back to your system Python.

### No Results Found

- Check that you've built an index for your project
- Try using more general terms in your query
- Ensure the code you're looking for is included in the indexed file types

### Search Performance Issues

For large codebases, consider:

- Excluding unnecessary file types when building the index
- Using more specific search queries
- Limiting your search to specific content types
