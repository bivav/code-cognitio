"""
Example module for testing enhanced code search functionality.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass


class BaseRepository:
    """Base class for all repository classes."""

    def __init__(self, db_connection: str):
        """Initialize the repository with a database connection."""
        self.db_connection = db_connection

    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Find an entity by its ID."""
        return {"id": id, "name": "Example Entity"}

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all entities."""
        return [{"id": 1, "name": "First Entity"}, {"id": 2, "name": "Second Entity"}]


class UserRepository(BaseRepository):
    """Repository for user data access."""

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find a user by their username."""
        # This is a CRUD read operation
        print(f"Finding user with username: {username}")
        return {"id": 1, "username": username, "email": f"{username}@example.com"}

    def create_user(self, username: str, email: str) -> Dict[str, Any]:
        """Create a new user."""
        # This is a CRUD create operation
        user = {"id": 2, "username": username, "email": email}
        print(f"Created user: {user}")
        return user

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID."""
        # This is a CRUD delete operation
        print(f"Deleted user with ID: {user_id}")
        return True


@dataclass
class ValidationError:
    """Represents a validation error."""

    field: str
    message: str


def validate_email(email: str) -> List[ValidationError]:
    """
    Validate email format.

    Args:
        email: The email address to validate

    Returns:
        List of validation errors, empty if valid
    """
    errors = []
    if not email or "@" not in email:
        errors.append(ValidationError("email", "Invalid email format"))

    return errors


def calculate_total_price(items: List[Dict[str, Any]], tax_rate: float = 0.1) -> float:
    """
    Calculate total price including tax.

    Args:
        items: List of items with 'price' and 'quantity' keys
        tax_rate: The tax rate to apply (default: 0.1)

    Returns:
        Total price including tax
    """
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    tax = subtotal * tax_rate
    return subtotal + tax


class UserService:
    """Service for user-related operations."""

    def __init__(self, user_repository: UserRepository):
        """Initialize with a user repository."""
        self.repository = user_repository

    def register_user(self, username: str, email: str) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            username: The user's username
            email: The user's email

        Returns:
            Created user information

        Raises:
            ValueError: If validation fails
        """
        # Validate the email first
        errors = validate_email(email)
        if errors:
            raise ValueError(f"Invalid email: {errors[0].message}")

        # Create user if validation passes
        return self.repository.create_user(username, email)

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information by username."""
        return self.repository.find_by_username(username)


class DataProcessor:
    """Process and transform data."""

    @staticmethod
    def transform_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform a list of data dictionaries.

        Args:
            data: List of data dictionaries to transform

        Returns:
            Transformed data
        """
        transformed = []
        for item in data:
            transformed_item = {
                "id": item.get("id", 0),
                "name": item.get("name", "").upper(),
                "tags": item.get("tags", []),
                "processed": True,
            }
            transformed.append(transformed_item)

        return transformed


def process_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of items.

    This is a higher-level function that uses DataProcessor.

    Args:
        items: List of items to process

    Returns:
        Processed items
    """
    processor = DataProcessor()
    return processor.transform_data(items)


if __name__ == "__main__":
    # Example usage
    user_repo = UserRepository("example_db_connection")
    user_service = UserService(user_repo)

    try:
        # This will fail validation
        user_service.register_user("john_doe", "invalid-email")
    except ValueError as e:
        print(f"Error: {e}")

    # This should succeed
    user = user_service.register_user("john_doe", "john@example.com")
    print(f"Registered user: {user}")

    # Calculate price
    items = [
        {"name": "Product 1", "price": 10.0, "quantity": 2},
        {"name": "Product 2", "price": 15.0, "quantity": 1},
    ]
    total = calculate_total_price(items)
    print(f"Total price: ${total:.2f}")

    # Process items
    processed_items = process_items(
        [
            {"id": 1, "name": "item1", "tags": ["tag1", "tag2"]},
            {"id": 2, "name": "item2", "tags": ["tag3"]},
        ]
    )
    print(f"Processed items: {processed_items}")
