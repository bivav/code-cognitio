"""Main entry point for the semantic search system."""

from src.core.cli import main

if __name__ == "__main__":
    main()
    # This script now delegates to the CLI module
    # The --json flag is passed to commands for API output
