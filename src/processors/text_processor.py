"""Module for processing and preparing text for indexing and search."""

import re
import string
import logging
from typing import List, Dict, Any, Optional, Union
import spacy
from spacy.language import Language
import nltk  # type: ignore
from nltk.stem import WordNetLemmatizer  # type: ignore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextProcessor:
    """Class for processing and preparing text for indexing and search."""

    def __init__(self, stop_words: Optional[List[str]] = None, use_spacy: bool = True):
        """
        Initialize the text processor.

        Args:
            stop_words: Optional list of stop words to use
            use_spacy: Whether to use spaCy for text processing
        """
        self.stop_words: List[str] = stop_words or self._get_default_stop_words()
        self.use_spacy: bool = use_spacy
        self.nlp: Optional[Language] = None
        self.nltk_lemmatizer: Optional[WordNetLemmatizer] = None

        if use_spacy:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Using spaCy for text processing")
            except Exception as e:
                logger.warning(
                    f"Failed to load spaCy model: {str(e)}. Falling back to NLTK."
                )
                self.use_spacy = False

        if not self.use_spacy:
            try:
                nltk.download("punkt", quiet=True)
                nltk.download("wordnet", quiet=True)
                nltk.download("averaged_perceptron_tagger", quiet=True)
                self.nltk_lemmatizer = WordNetLemmatizer()
                logger.info("Using NLTK for text processing")
            except Exception as e:
                logger.error(f"Failed to initialize NLTK: {str(e)}")
                raise

    def process_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a chunk of text to prepare it for indexing.

        Args:
            chunk: Dictionary containing the chunk data

        Returns:
            Dictionary with processed text
        """
        processed_chunk = chunk.copy()

        # Process different chunk types
        chunk_type = chunk.get("type", "")

        if chunk_type == "function":
            # Process function chunks
            docstring = chunk.get("docstring", "")
            processed_chunk["processed_text"] = self.clean_text(docstring)
            processed_chunk["function_signature"] = self._get_function_signature(chunk)
            processed_chunk["content_type"] = "code"

        elif chunk_type == "method":
            # Process method chunks
            docstring = chunk.get("docstring", "")
            processed_chunk["processed_text"] = self.clean_text(docstring)
            processed_chunk["method_signature"] = self._get_function_signature(chunk)
            processed_chunk["content_type"] = "code"

        elif chunk_type == "class":
            # Process class chunks
            docstring = chunk.get("docstring", "")
            processed_chunk["processed_text"] = self.clean_text(docstring)
            processed_chunk["content_type"] = "code"

        elif chunk_type == "section":
            # Process markdown section chunks
            content = chunk.get("content", "")
            # Remove code blocks for text analysis (but keep them in the raw content)
            cleaned_content = self._remove_code_blocks(content)
            processed_chunk["processed_text"] = self.clean_text(cleaned_content)
            processed_chunk["content_type"] = "documentation"
            # Add section type classification if possible
            section_title = chunk.get("title", "").lower()
            if "install" in section_title or "setup" in section_title:
                processed_chunk["section_type"] = "installation"
            elif "usage" in section_title or "example" in section_title:
                processed_chunk["section_type"] = "usage"
            elif "api" in section_title or "reference" in section_title:
                processed_chunk["section_type"] = "reference"
            elif "config" in section_title:
                processed_chunk["section_type"] = "configuration"
            else:
                processed_chunk["section_type"] = "general"

        return processed_chunk

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove special characters and extra whitespace
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        # Process with available NLP tool
        if self.use_spacy and self.nlp is not None:
            return self._process_with_spacy(text)
        elif self.nltk_lemmatizer is not None:
            return self._process_with_nltk(text)
        else:
            # Fallback to simple stop word removal
            words = text.split()
            words = [word for word in words if word not in self.stop_words]
            return " ".join(words)

    def _process_with_spacy(self, text: str) -> str:
        """
        Process text using spaCy for lemmatization and stop word removal.

        Args:
            text: Text to process

        Returns:
            Processed text
        """
        if self.nlp is None:
            return text

        doc = self.nlp(text)
        tokens = [
            token.lemma_
            for token in doc
            if not token.is_stop and not token.is_punct and token.lemma_.strip()
        ]
        return " ".join(tokens)

    def _process_with_nltk(self, text: str) -> str:
        """
        Process text using NLTK for lemmatization and stop word removal.

        Args:
            text: Text to process

        Returns:
            Processed text
        """
        if self.nltk_lemmatizer is None:
            return text

        tokens = nltk.word_tokenize(text)
        lemmatized = [
            self.nltk_lemmatizer.lemmatize(token)
            for token in tokens
            if token not in self.stop_words
        ]
        return " ".join(lemmatized)

    def _get_function_signature(self, func_data: Dict[str, Any]) -> str:
        """
        Generate a function signature string.

        Args:
            func_data: Dictionary with function data

        Returns:
            Function signature as a string
        """
        name = func_data.get("full_name", func_data.get("name", ""))

        # Build parameters string
        params = []
        for param in func_data.get("parameters", []):
            param_name = param.get("name", "")
            param_type = param.get("type", "")

            if param_type:
                params.append(f"{param_name}: {param_type}")
            else:
                params.append(param_name)

        param_str = ", ".join(params)

        # Add return type if available
        returns = func_data.get("returns", "")
        return_str = f" -> {returns}" if returns else ""

        return f"{name}({param_str}){return_str}"

    def _remove_code_blocks(self, text: str) -> str:
        """
        Remove code blocks from text.

        Args:
            text: Text that may contain code blocks

        Returns:
            Text with code blocks removed
        """
        # Remove fenced code blocks: ```language\ncode\n```
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

        # Remove indented code blocks (lines starting with 4 spaces or a tab)
        lines = []
        for line in text.split("\n"):
            if not line.startswith("    ") and not line.startswith("\t"):
                lines.append(line)

        return "\n".join(lines)

    def _get_default_stop_words(self) -> List[str]:
        """
        Get a default list of English stop words.

        Returns:
            List of stop words
        """
        return [
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "because",
            "as",
            "what",
            "which",
            "this",
            "that",
            "these",
            "those",
            "then",
            "just",
            "so",
            "than",
            "such",
            "both",
            "through",
            "about",
            "for",
            "is",
            "of",
            "while",
            "during",
            "to",
            "from",
            "in",
            "on",
            "by",
            "at",
            "be",
            "with",
            "into",
            "has",
            "are",
            "have",
            "had",
            "was",
            "were",
            "been",
            "being",
            "do",
            "does",
            "did",
            "can",
            "could",
            "may",
            "might",
            "shall",
            "should",
            "will",
            "would",
            "not",
            "up",
            "down",
            "no",
            "yes",
        ]
