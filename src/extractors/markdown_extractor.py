"""Module for extracting information from Markdown files."""

import os
import re
from typing import Dict, List, Any, Tuple


class MarkdownExtractor:
    """Class for extracting information from Markdown files."""

    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract sections and content from a Markdown file.

        Args:
            file_path: Path to the Markdown file

        Returns:
            List of dictionaries containing extracted information
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            # Extract the title (first h1)
            title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
            title = title_match.group(1) if title_match else os.path.basename(file_path)

            # Extract sections based on headers
            sections = self._extract_sections(content, file_path)

            # Add the document title as metadata
            for section in sections:
                section["document_title"] = title

            return sections
        except Exception as e:
            print(f"Error extracting from {file_path}: {str(e)}")
            return []

    def _extract_sections(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract sections from Markdown content based on headers.

        Args:
            content: Markdown content
            file_path: Path to the file

        Returns:
            List of dictionaries with section information
        """
        sections = []

        # Get all headers
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        headers = [
            (match.group(1), match.group(2), match.start())
            for match in header_pattern.finditer(content)
        ]

        # Process each header and its content
        for i, (level, title, start_pos) in enumerate(headers):
            # Determine the end position (next header or end of file)
            end_pos = headers[i + 1][2] if i < len(headers) - 1 else len(content)

            # Extract section content
            section_content = content[start_pos:end_pos].strip()

            # Remove the header from the content
            section_content = re.sub(
                r"^#{1,6}\s+.+$", "", section_content, 1, re.MULTILINE
            ).strip()

            # Create section object
            section = {
                "type": "section",
                "level": len(level),  # Number of # characters
                "title": title,
                "content": section_content,
                "file_path": file_path,
                "position": start_pos,
            }

            # Add subsections classification
            if len(level) > 1:
                # Find parent section
                for potential_parent in reversed(sections):
                    if potential_parent["level"] < len(level):
                        section["parent_title"] = potential_parent["title"]
                        break

            # Extract code blocks if present
            code_blocks = self._extract_code_blocks(section_content)
            if code_blocks:
                section["code_blocks"] = code_blocks

            sections.append(section)

        return sections

    def _extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract code blocks from Markdown content.

        Args:
            content: Markdown content

        Returns:
            List of dictionaries with code block information
        """
        code_blocks = []

        # Pattern for fenced code blocks: ```language\ncode\n```
        pattern = re.compile(r"```([a-zA-Z0-9]*)\n(.*?)\n```", re.DOTALL)

        for match in pattern.finditer(content):
            language = match.group(1) or "text"
            code = match.group(2)

            code_blocks.append(
                {"type": "code_block", "language": language, "code": code}
            )

        return code_blocks
