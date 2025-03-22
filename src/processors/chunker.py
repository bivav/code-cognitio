"""Module for chunking extracted content into smaller, searchable pieces."""

from typing import List, Dict, Any


class Chunker:
    """Class for chunking extracted content into smaller, searchable pieces."""

    def __init__(self, max_chunk_size: int = 500):
        """
        Initialize the chunker.

        Args:
            max_chunk_size: Maximum chunk size in characters
        """
        self.max_chunk_size = max_chunk_size

    def chunk_content(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk a list of extracted items into smaller pieces.

        Args:
            items: List of extracted items

        Returns:
            List of chunked items
        """
        chunked_items = []

        for item in items:
            # Different chunking strategies based on item type
            item_type = item.get("type", "")

            if item_type in ("function", "method", "class"):
                # Functions, methods, and classes are already natural chunks
                chunked_items.append(item)

            elif item_type == "section":
                # Sections may need to be split into smaller chunks
                section_chunks = self._chunk_section(item)
                chunked_items.extend(section_chunks)

            elif item_type == "module":
                # Module docstrings can be large, so chunk them
                chunked_items.append(item)

            else:
                # Default: just add the item as is
                chunked_items.append(item)

        return chunked_items

    def _chunk_section(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a section into multiple chunks if needed.

        Args:
            section: Section data

        Returns:
            List of section chunks
        """
        content = section.get("content", "")

        # If content is small enough, return as is
        if len(content) <= self.max_chunk_size:
            return [section]

        # Otherwise, split the content into paragraphs and chunk them
        chunks = []
        paragraphs = self._split_into_paragraphs(content)

        current_chunk = ""
        current_chunk_data = section.copy()
        chunk_index = 0

        for para in paragraphs:
            # If adding this paragraph would exceed the max size, create a new chunk
            if len(current_chunk) + len(para) > self.max_chunk_size and current_chunk:
                # Save the current chunk
                current_chunk_data["content"] = current_chunk
                current_chunk_data["chunk_index"] = chunk_index
                chunks.append(current_chunk_data)

                # Start a new chunk
                current_chunk_data = section.copy()
                current_chunk = para
                chunk_index += 1
            else:
                # Add to the current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Save the last chunk if there's anything left
        if current_chunk:
            current_chunk_data["content"] = current_chunk
            current_chunk_data["chunk_index"] = chunk_index
            chunks.append(current_chunk_data)

        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.

        Args:
            text: Text to split

        Returns:
            List of paragraphs
        """
        # Split by double newline (paragraph boundary)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # If paragraphs are still too large, split them further
        result = []
        for para in paragraphs:
            if len(para) <= self.max_chunk_size:
                result.append(para)
            else:
                # Split long paragraph into sentences
                sentences = self._split_into_sentences(para)
                current_chunk = ""

                for sentence in sentences:
                    if (
                        len(current_chunk) + len(sentence) > self.max_chunk_size
                        and current_chunk
                    ):
                        result.append(current_chunk)
                        current_chunk = sentence
                    else:
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence

                if current_chunk:
                    result.append(current_chunk)

        return result

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting - not perfect but good enough for chunking
        # Handles common end-of-sentence marks followed by a space and uppercase letter
        import re

        sentence_endings = r"(?<=[.!?])\s+(?=[A-Z])"
        sentences = re.split(sentence_endings, text)
        return sentences
