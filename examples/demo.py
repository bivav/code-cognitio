#!/usr/bin/env python
"""
Code Cognitio Demo - Shows how to use all the enhanced search features.

This script demonstrates the various search capabilities of Code Cognitio
including parameter filtering, document searching, and specialized queries.
"""

import os
import subprocess
import argparse
from typing import List, Optional


def run_command(command: List[str]) -> None:
    """Run a command and print the header."""
    header = f"Running: {' '.join(command)}"
    print("\n" + "=" * 80)
    print(f"{header}")
    print("=" * 80)

    # Execute the command
    subprocess.run(command)


def run_demo(source_path: str, build_index: bool = True) -> None:
    """Run the Code Cognitio demo with various search types."""
    if build_index:
        # Build the index first
        run_command(
            ["python", "-m", "src.main", "build", source_path, "--file-types", "all"]
        )

    # Basic searches
    run_command(["python", "-m", "src.main", "search", "process data"])

    # Advanced searches with parameter filtering
    run_command(
        ["python", "-m", "src.main", "search", "process list", "--param-type", "list"]
    )
    run_command(
        [
            "python",
            "-m",
            "src.main",
            "search",
            "validate user input",
            "--param-name",
            "email",
        ]
    )

    # Content type filtering
    run_command(
        [
            "python",
            "-m",
            "src.main",
            "search",
            "installation",
            "--filter",
            "documentation",
        ]
    )
    run_command(
        ["python", "-m", "src.main", "search", "data processing", "--filter", "code"]
    )

    # Type filtering
    run_command(["python", "-m", "src.main", "search", "process", "--type", "class"])
    run_command(
        ["python", "-m", "src.main", "search", "validate", "--type", "function"]
    )

    # Score threshold
    run_command(
        ["python", "-m", "src.main", "search", "configuration", "--min-score", "0.4"]
    )

    # Return type filtering
    run_command(
        ["python", "-m", "src.main", "search", "validate", "--return-type", "bool"]
    )

    # Combined filters
    run_command(
        [
            "python",
            "-m",
            "src.main",
            "search",
            "process data",
            "--type",
            "method",
            "--filter",
            "code",
            "--top-k",
            "3",
        ]
    )

    # Dockerfile search
    run_command(
        ["python", "-m", "src.main", "search", "dockerfile", "--filter", "code"]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Code Cognitio demonstration")
    parser.add_argument(
        "source_path",
        nargs="?",
        default="examples",
        help="Path to source code to index and search (default: examples)",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip building the index (use existing)",
    )

    args = parser.parse_args()
    run_demo(args.source_path, build_index=not args.skip_build)
