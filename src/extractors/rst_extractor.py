"""Module for extracting information from reStructuredText files."""

import os
import re
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSTExtractor:
    """Class for extracting information from reStructuredText files."""

    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract sections and content from a reStructuredText file.

        Args:
            file_path: Path to the RST file

        Returns:
            List of dictionaries containing extracted information
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            # Extract the title (first heading)
            title_match = self._find_title(content)
            title = title_match if title_match else os.path.basename(file_path)

            # Extract sections based on headers
            sections = self._extract_sections(content, file_path)

            # Add the document title as metadata
            for section in sections:
                section["document_title"] = title
                section["content_type"] = "documentation"
                section["format"] = "rst"

            return sections
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {str(e)}")
            return []

    def _find_title(self, content: str) -> Optional[str]:
        """
        Find the title of the RST document.

        RST titles can be identified by underlines or overlines+underlines.

        Args:
            content: RST content

        Returns:
            Title if found, None otherwise
        """
        # Look for section headers with underlines
        lines = content.split("\n")
        for i in range(len(lines) - 1):
            # Check if the next line is an underline (====, ----, etc.)
            if (
                i + 1 < len(lines)
                and lines[i].strip()
                and self._is_header_marker(lines[i + 1])
            ):
                return lines[i].strip()

            # Check for overline + title + underline pattern
            if (
                i + 2 < len(lines)
                and self._is_header_marker(lines[i])
                and lines[i + 1].strip()
                and self._is_header_marker(lines[i + 2])
            ):
                return lines[i + 1].strip()

        return None

    def _is_header_marker(self, line: str) -> bool:
        """
        Check if a line is a RST header marker (==== or ---- etc.).

        Args:
            line: Line to check

        Returns:
            True if the line is a header marker, False otherwise
        """
        if not line.strip():
            return False

        # Header markers consist of repeated punctuation characters
        return all(c == line.strip()[0] for c in line.strip())

    def _extract_sections(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract sections from RST content based on headers.

        Args:
            content: RST content
            file_path: Path to the file

        Returns:
            List of dictionaries with section information
        """
        sections = []
        lines = content.split("\n")

        # Add document as a whole first
        sections.append(
            {
                "type": "section",
                "level": 0,
                "title": os.path.basename(file_path),
                "content": content,
                "file_path": file_path,
                "position": 0,
            }
        )

        # Find all section headers
        section_starts = []
        for i in range(len(lines)):
            # Check for underline style headers (title followed by ==== or ----)
            if i > 0 and lines[i - 1].strip() and self._is_header_marker(lines[i]):
                level = self._get_header_level(lines[i][0])
                section_starts.append((i - 1, level, lines[i - 1].strip()))

            # Check for overline+underline style headers (==== followed by title followed by ====)
            if (
                i > 0
                and i + 1 < len(lines)
                and self._is_header_marker(lines[i - 1])
                and lines[i].strip()
                and i + 1 < len(lines)
                and self._is_header_marker(lines[i + 1])
            ):
                level = self._get_header_level(lines[i - 1][0])
                section_starts.append((i, level, lines[i].strip()))

        # Sort by position
        section_starts.sort(key=lambda x: x[0])

        # Extract each section's content
        for i, (line_num, level, title) in enumerate(section_starts):
            # Calculate the end line (next section or end of file)
            end_line = (
                section_starts[i + 1][0] if i + 1 < len(section_starts) else len(lines)
            )

            # Get section content
            if self._is_header_marker(lines[line_num + 1]):
                # Skip the underline for regular headers
                section_content = "\n".join(lines[line_num + 2 : end_line])
            elif (
                line_num > 0
                and self._is_header_marker(lines[line_num - 1])
                and self._is_header_marker(lines[line_num + 1])
            ):
                # Skip both overline and underline
                section_content = "\n".join(lines[line_num + 2 : end_line])
            else:
                # Fallback
                section_content = "\n".join(lines[line_num + 1 : end_line])

            # Calculate position in characters
            position = sum(len(line) + 1 for line in lines[:line_num])

            section = {
                "type": "section",
                "level": level,
                "title": title,
                "content": section_content.strip(),
                "file_path": file_path,
                "position": position,
            }

            # Extract code blocks if present
            code_blocks = self._extract_code_blocks(section_content)
            if code_blocks:
                section["code_blocks"] = code_blocks

            sections.append(section)

        return sections

    def _get_header_level(self, marker: str) -> int:
        """
        Determine the header level based on the marker character.

        RST doesn't have strict level associations with specific characters,
        but there are conventions. We'll use a common mapping.

        Args:
            marker: Header marker character

        Returns:
            Header level (1-6)
        """
        # Common RST header level markers, in typical order of hierarchy
        markers = ["#", "*", "=", "-", "^", '"']
        try:
            return markers.index(marker) + 1
        except ValueError:
            # For any other character, assume a deep level
            return 6

    def _extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract code blocks from RST content.

        Args:
            content: RST content

        Returns:
            List of dictionaries with code block information
        """
        code_blocks = []

        # Find all code-block directives
        # Pattern matches: .. code-block:: python
        code_pattern = re.compile(
            r".. code-block:: (\w+)\s*\n\s*\n(.*?)(?:\n\s*\n|$)", re.DOTALL
        )

        for match in code_pattern.finditer(content):
            language = match.group(1) or "text"
            code = match.group(2)

            # Remove indentation
            lines = code.split("\n")
            if lines:
                # Find minimum indentation (ignoring empty lines)
                indents = [
                    len(line) - len(line.lstrip()) for line in lines if line.strip()
                ]
                if indents:
                    min_indent = min(indents)
                    # Remove the common indentation
                    code = "\n".join(
                        line[min_indent:] if line.strip() else line for line in lines
                    )

            code_blocks.append(
                {"type": "code_block", "language": language, "code": code}
            )

        # Also find literal blocks (indented blocks after ::)
        literal_pattern = re.compile(r"::\s*\n\s*\n((?:\s+.*\n)+)", re.MULTILINE)

        for match in literal_pattern.finditer(content):
            code = match.group(1)

            # Remove common indentation
            lines = code.split("\n")
            if lines:
                indents = [
                    len(line) - len(line.lstrip()) for line in lines if line.strip()
                ]
                if indents:
                    min_indent = min(indents)
                    code = "\n".join(
                        line[min_indent:] if line.strip() else line for line in lines
                    )

            code_blocks.append(
                {
                    "type": "code_block",
                    "language": "text",  # Literal blocks don't specify language
                    "code": code,
                }
            )

        return code_blocks
