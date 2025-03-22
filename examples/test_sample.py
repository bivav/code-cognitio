"""
Sample Python file for testing the semantic search functionality.
This file contains various functions and classes with docstrings
to test the extraction and indexing capabilities.
"""

import os
import json
from typing import Dict, List, Any, Optional


def process_data(data: Dict[str, Any], normalize: bool = True) -> Dict[str, Any]:
    """
    Process the input data dictionary by normalizing values and filtering keys.

    Args:
        data: Input dictionary to process
        normalize: Whether to normalize string values

    Returns:
        Processed dictionary with normalized values
    """
    result = {}

    for key, value in data.items():
        # Skip internal fields
        if key.startswith("_"):
            continue

        # Process string values
        if isinstance(value, str) and normalize:
            # Convert to lowercase and strip whitespace
            processed_value = value.lower().strip()
            result[key] = processed_value
        else:
            result[key] = value

    return result


class DataProcessor:
    """
    Class for processing and transforming data structures.

    This class provides methods to transform, filter, and analyze
    various data structures like dictionaries and lists.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the DataProcessor with optional configuration.

        Args:
            config: Configuration dictionary with processing parameters
        """
        self.config = config or {}
        self.processed_count = 0

    def process_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of data items using the configured settings.

        Args:
            items: List of dictionaries to process

        Returns:
            List of processed dictionaries
        """
        results = []

        for item in items:
            # Apply preprocessing
            processed_item = self._preprocess_item(item)

            # Apply main processing
            processed_item = process_data(
                processed_item, normalize=self.config.get("normalize", True)
            )

            # Apply postprocessing
            processed_item = self._postprocess_item(processed_item)

            results.append(processed_item)
            self.processed_count += 1

        return results

    def _preprocess_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply preprocessing steps to an item before main processing.

        Args:
            item: Dictionary to preprocess

        Returns:
            Preprocessed dictionary
        """
        # Create a copy to avoid modifying the original
        result = item.copy()

        # Add metadata field if configured
        if self.config.get("add_metadata", False):
            result["_metadata"] = {
                "preprocessed": True,
                "version": self.config.get("version", "1.0"),
            }

        return result

    def _postprocess_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply postprocessing steps to an item after main processing.

        Args:
            item: Dictionary to postprocess

        Returns:
            Postprocessed dictionary
        """
        # Create a copy to avoid modifying the original
        result = item.copy()

        # Add timestamp if configured
        if self.config.get("add_timestamp", False):
            import datetime

            result["processed_at"] = datetime.datetime.now().isoformat()

        return result

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the processing operations.

        Returns:
            Dictionary with processing statistics
        """
        return {"processed_count": self.processed_count, "config": self.config}


def save_results(results: List[Dict[str, Any]], output_path: str) -> bool:
    """
    Save processing results to a JSON file.

    Args:
        results: List of processed dictionaries to save
        output_path: Path to the output JSON file

    Returns:
        True if saving was successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save to JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        return True
    except Exception as e:
        print(f"Error saving results: {str(e)}")
        return False


class AdvancedProcessor(DataProcessor):
    """
    Advanced data processor with additional capabilities.

    This class extends the base DataProcessor with more advanced
    transformation and analysis features.
    """

    def __init__(
        self, config: Optional[Dict[str, Any]] = None, plugins: List[str] = None
    ):
        """
        Initialize the AdvancedProcessor with configuration and plugins.

        Args:
            config: Configuration dictionary with processing parameters
            plugins: List of plugin names to enable
        """
        super().__init__(config)
        self.plugins = plugins or []

    def process_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of data items with advanced features.

        This method extends the base processing with plugin support
        and additional transformation capabilities.

        Args:
            items: List of dictionaries to process

        Returns:
            List of processed dictionaries with advanced transformations
        """
        # First apply the base processing
        results = super().process_items(items)

        # Then apply plugin-specific processing if plugins are enabled
        if "categorize" in self.plugins:
            results = self._categorize_items(results)

        if "deduplicate" in self.plugins:
            results = self._remove_duplicates(results)

        return results

    def _categorize_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Categorize items based on their content.

        Args:
            items: List of dictionaries to categorize

        Returns:
            List of dictionaries with category information
        """
        categorized = []

        for item in items:
            item_copy = item.copy()

            # Simple categorization logic
            if any(key.startswith("user_") for key in item):
                item_copy["category"] = "user"
            elif any(key.startswith("product_") for key in item):
                item_copy["category"] = "product"
            elif any(key.startswith("order_") for key in item):
                item_copy["category"] = "order"
            else:
                item_copy["category"] = "other"

            categorized.append(item_copy)

        return categorized

    def _remove_duplicates(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate items from the list.

        Args:
            items: List of dictionaries that may contain duplicates

        Returns:
            List of dictionaries with duplicates removed
        """
        unique_items = []
        seen_keys = set()

        # Use a simple strategy based on a tuple of sorted keys and values
        for item in items:
            # Create a hashable representation of the item
            item_key = tuple(
                sorted(
                    (k, str(v))
                    for k, v in item.items()
                    if not k.startswith("_") and k != "processed_at"
                )
            )

            if item_key not in seen_keys:
                seen_keys.add(item_key)
                unique_items.append(item)

        return unique_items
