from typing import List, Dict, Optional, Union
from datetime import datetime
import math


def calculate_fibonacci(n: int) -> int:
    """
    Calculate the nth number in the Fibonacci sequence using iteration.

    Args:
        n (int): The position in the Fibonacci sequence (must be non-negative)

    Returns:
        int: The nth Fibonacci number

    Raises:
        ValueError: If n is negative

    Examples:
        >>> calculate_fibonacci(0)
        0
        >>> calculate_fibonacci(1)
        1
        >>> calculate_fibonacci(5)
        5
    """
    if n < 0:
        raise ValueError("Fibonacci sequence is not defined for negative numbers")
    if n <= 1:
        return n

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def validate_email(email: str) -> bool:
    """
    Validate an email address using basic checks.

    This function performs a simple validation of email addresses by checking for:
    - Presence of exactly one @ symbol
    - At least one character before the @
    - At least one character between @ and .
    - At least two characters after the last .

    Args:
        email (str): The email address to validate

    Returns:
        bool: True if the email is valid, False otherwise
    """
    if not isinstance(email, str):
        return False

    parts = email.split("@")
    if len(parts) != 2:
        return False

    local, domain = parts
    if not local or not domain:
        return False

    domain_parts = domain.split(".")
    if len(domain_parts) < 2:
        return False

    return len(domain_parts[-1]) >= 2


def process_text_data(text: str, case_sensitive: bool = False) -> Dict[str, int]:
    """
    Process text and return word frequency analysis.

    Analyzes the provided text and returns a dictionary containing the frequency
    of each word. Optionally preserves case sensitivity.

    Args:
        text (str): The input text to analyze
        case_sensitive (bool, optional): Whether to treat words as case-sensitive.
            Defaults to False.

    Returns:
        Dict[str, int]: A dictionary with words as keys and their frequencies as values

    Example:
        >>> process_text_data("Hello world hello")
        {'hello': 2, 'world': 1}
    """
    if not case_sensitive:
        text = text.lower()

    words = text.split()
    frequency = {}

    for word in words:
        frequency[word] = frequency.get(word, 0) + 1

    return frequency


def calculate_circle_properties(radius: float) -> Dict[str, float]:
    """
    Calculate various properties of a circle given its radius.

    Computes the area, circumference, and diameter of a circle.
    All calculations use π from the math module for maximum precision.

    Args:
        radius (float): The radius of the circle (must be positive)

    Returns:
        Dict[str, float]: A dictionary containing:
            - 'area': The area of the circle
            - 'circumference': The circumference of the circle
            - 'diameter': The diameter of the circle

    Raises:
        ValueError: If radius is negative
    """
    if radius < 0:
        raise ValueError("Radius cannot be negative")

    return {
        "area": math.pi * radius**2,
        "circumference": 2 * math.pi * radius,
        "diameter": 2 * radius,
    }


def merge_sorted_lists(list1: List[int], list2: List[int]) -> List[int]:
    """
    Merge two sorted lists into a single sorted list.

    Takes two lists that are already sorted in ascending order and combines
    them into a single sorted list. This function uses a two-pointer approach
    for optimal performance.

    Args:
        list1 (List[int]): First sorted list of integers
        list2 (List[int]): Second sorted list of integers

    Returns:
        List[int]: A new sorted list containing all elements from both input lists

    Example:
        >>> merge_sorted_lists([1, 3, 5], [2, 4, 6])
        [1, 2, 3, 4, 5, 6]
    """
    result = []
    i = j = 0

    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1

    result.extend(list1[i:])
    result.extend(list2[j:])
    return result


def format_duration(seconds: int) -> str:
    """
    Format a duration in seconds into a human-readable string.

    Converts a duration given in seconds into a string representation
    showing years, days, hours, minutes, and seconds where applicable.

    Args:
        seconds (int): Number of seconds to format

    Returns:
        str: Formatted duration string

    Examples:
        >>> format_duration(62)
        '1 minute and 2 seconds'
        >>> format_duration(3600)
        '1 hour'
    """
    if seconds == 0:
        return "now"

    units = [
        ("year", 365 * 24 * 3600),
        ("day", 24 * 3600),
        ("hour", 3600),
        ("minute", 60),
        ("second", 1),
    ]

    parts = []

    for unit, unit_seconds in units:
        if seconds >= unit_seconds:
            value = seconds // unit_seconds
            seconds %= unit_seconds
            parts.append(f"{value} {unit}{'s' if value != 1 else ''}")

    if len(parts) > 1:
        return f"{', '.join(parts[:-1])} and {parts[-1]}"
    return parts[0]


def safe_divide(
    numerator: Union[int, float],
    denominator: Union[int, float],
    default: Optional[float] = None,
) -> Optional[float]:
    """
    Safely divide two numbers with error handling.

    Performs division while handling potential errors such as division by zero
    or invalid input types. Returns a default value if the division fails.

    Args:
        numerator (Union[int, float]): The number to be divided
        denominator (Union[int, float]): The number to divide by
        default (Optional[float], optional): Value to return if division fails.
            Defaults to None.

    Returns:
        Optional[float]: Result of division, or default value if division fails

    Examples:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0, default=0)
        0
    """
    try:
        return float(numerator) / float(denominator)
    except (ZeroDivisionError, TypeError, ValueError):
        return default


def is_palindrome(
    text: str, ignore_case: bool = True, ignore_spaces: bool = True
) -> bool:
    """
    Check if a string is a palindrome.

    Determines whether the input string reads the same forwards and backwards,
    with options to ignore case and/or spaces.

    Args:
        text (str): The string to check
        ignore_case (bool, optional): Whether to ignore letter case.
            Defaults to True.
        ignore_spaces (bool, optional): Whether to ignore spaces.
            Defaults to True.

    Returns:
        bool: True if the string is a palindrome, False otherwise

    Examples:
        >>> is_palindrome("A man a plan a canal Panama")
        True
        >>> is_palindrome("race a car")
        False
    """
    if ignore_case:
        text = text.lower()
    if ignore_spaces:
        text = "".join(text.split())

    return text == text[::-1]


def generate_date_range(
    start_date: datetime, end_date: datetime, include_weekends: bool = True
) -> List[datetime]:
    """
    Generate a list of dates between start_date and end_date.

    Creates a list of datetime objects for each day in the specified range,
    with the option to exclude weekends.

    Args:
        start_date (datetime): The start date of the range
        end_date (datetime): The end date of the range (inclusive)
        include_weekends (bool, optional): Whether to include weekend days.
            Defaults to True.

    Returns:
        List[datetime]: List of datetime objects for each day in the range

    Raises:
        ValueError: If start_date is later than end_date

    Example:
        >>> from datetime import datetime
        >>> start = datetime(2024, 1, 1)
        >>> end = datetime(2024, 1, 3)
        >>> dates = generate_date_range(start, end)
        >>> len(dates)
        3
    """
    if start_date > end_date:
        raise ValueError("Start date must be before or equal to end date")

    date_list = []
    current_date = start_date

    while current_date <= end_date:
        if include_weekends or current_date.weekday() < 5:  # 5 is Saturday, 6 is Sunday
            date_list.append(current_date)
        current_date = current_date.replace(day=current_date.day + 1)

    return date_list


def calculate_average_temperature(temperatures: List[float]) -> float:
    """
    Calculate the average temperature from a list of temperatures.

    Args:
        temperatures (List[float]): List of temperatures to calculate the average of

    Returns:
        float: The average temperature

    Raises:
        ValueError: If the list is empty or contains non-numeric values
    """
    if not temperatures:
        raise ValueError("List of temperatures cannot be empty")

    total = sum(temperatures)
    count = len(temperatures)

    return total / count
