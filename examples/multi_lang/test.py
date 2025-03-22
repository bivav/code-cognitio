#!/usr/bin/env python
"""Sample Python file for testing multi-language support."""


class User:
    """Represents a user in the system."""

    def __init__(self, name: str, email: str):
        """Initialize a new user.

        Args:
            name: The user's name
            email: The user's email
        """
        self.name = name
        self.email = email

    def validate_email(self) -> bool:
        """Check if the email is valid.

        Returns:
            True if valid, False otherwise
        """
        return "@" in self.email and "." in self.email.split("@")[1]


def create_user(name: str, email: str) -> User:
    """Create a new user.

    Args:
        name: The user's name
        email: The user's email

    Returns:
        A new User instance
    """
    user = User(name, email)
    if not user.validate_email():
        raise ValueError(f"Invalid email: {email}")
    return user


if __name__ == "__main__":
    try:
        user = create_user("John Doe", "john@example.com")
        print(f"Created user {user.name} with email {user.email}")
    except ValueError as e:
        print(f"Error: {e}")
