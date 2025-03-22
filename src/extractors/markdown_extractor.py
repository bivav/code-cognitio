"""Module for extracting information from Markdown files."""

import os
import re
from typing import Dict, List, Any


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

            # If no sections were found, create a single section for the whole document
            if not sections:
                sections = [
                    {
                        "type": "section",
                        "level": 0,
                        "title": title,
                        "content": content,
                        "file_path": file_path,
                        "position": 0,
                        "content_type": "documentation",
                        "description": f"{title} documentation",
                    }
                ]

            # Add the document title as metadata and enhance section data
            for section in sections:
                section["document_title"] = title

                # Add content type for proper processing
                section["content_type"] = "documentation"

                # Add a description based on the section title
                if "description" not in section:
                    section["description"] = section.get("title", "")

                # Add section content summary
                section_content = section.get("content", "")
                if section_content:
                    # Create a summary by taking the first sentence or first 100 chars
                    first_sentence = re.match(r"^(.*?[.!?])\s", section_content)
                    if first_sentence:
                        section["summary"] = first_sentence.group(1)
                    else:
                        section["summary"] = (
                            section_content[:100] + "..."
                            if len(section_content) > 100
                            else section_content
                        )

            return sections
        except Exception as e:
            print(f"Error extracting from {file_path}: {str(e)}")
            return []

    def _extract_sections(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract sections from Markdown content.

        Args:
            content: Markdown content
            file_path: Path to the Markdown file

        Returns:
            List of section dictionaries
        """
        sections = []
        lines = content.split("\n")
        current_section = None
        current_content = []
        current_level = 0
        position = 0

        for i, line in enumerate(lines):
            # Check if this is a header line
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if header_match:
                # If we were building a section, add it to the list
                if current_section:
                    section_content = "\n".join(current_content).strip()
                    sections.append(
                        {
                            "type": "section",
                            "level": current_level,
                            "title": current_section,
                            "content": section_content,
                            "file_path": file_path,
                            "position": position,
                            "content_type": "documentation",
                        }
                    )

                # Start a new section
                current_level = len(header_match.group(1))
                current_section = header_match.group(2)
                current_content = []
                position = i

            # Add line to current section content
            elif current_section is not None:
                current_content.append(line)

        # Add the last section if there is one
        if current_section:
            section_content = "\n".join(current_content).strip()
            sections.append(
                {
                    "type": "section",
                    "level": current_level,
                    "title": current_section,
                    "content": section_content,
                    "file_path": file_path,
                    "position": position,
                    "content_type": "documentation",
                }
            )

        # Extract code blocks as separate elements
        code_blocks = self._extract_code_blocks(content, file_path)
        sections.extend(code_blocks)

        return sections

    def _extract_code_blocks(
        self, content: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Extract code blocks from Markdown content.

        Args:
            content: Markdown content
            file_path: Path to the Markdown file

        Returns:
            List of code block dictionaries
        """
        code_blocks = []
        code_block_pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)

        for i, match in enumerate(code_block_pattern.finditer(content)):
            language = match.group(1) or "text"
            code = match.group(2).strip()
            position = match.start()

            # Check if this is a significant code block (not just a small example)
            if len(code.split("\n")) > 2:
                # Determine a title for the code block
                lines_before = content[:position].split("\n")
                header_match = None
                for line in reversed(lines_before[-5:]):  # Look at the 5 lines before
                    if re.match(r"^(#{1,6})\s+(.+)$", line):
                        header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
                        break

                title = (
                    f"Code block ({language})"
                    if not header_match
                    else f"{header_match.group(2)} - Code Example"
                )

                code_blocks.append(
                    {
                        "type": "code_block",
                        "language": language,
                        "title": title,
                        "content": code,
                        "file_path": file_path,
                        "position": position,
                        "content_type": "documentation",
                    }
                )

        return code_blocks
