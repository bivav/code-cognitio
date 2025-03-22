# Python Utility Functions Documentation

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Package Dependencies](#package-dependencies)
- [Function Reference](#function-reference)
- [Examples](#examples)
- [FAQ](#faq)
- [Contributing](#contributing)

## Overview

`dummy.py` is a collection of utility functions that demonstrate various Python programming concepts and best practices. The library includes functions for mathematical calculations, string manipulation, date handling, and data processing. Each function is thoroughly documented with type hints, docstrings, and examples.

## Installation

To use these utility functions, you'll need Python 3.7 or later. Clone this repository and install the required packages:

```bash
# Clone the repository
git clone https://github.com/yourusername/python-utilities.git

# Navigate to the project directory
cd python-utilities

# Install dependencies using uv
uv pip install -r requirements.txt
```

## Package Dependencies

The following packages are required:

- `typing`: For type hints (included in Python 3.7+)
- `datetime`: For date manipulation (included in Python standard library)
- `math`: For mathematical operations (included in Python standard library)

## Function Reference

### Mathematical Functions

#### `calculate_fibonacci(n: int) -> int`

Calculates the nth number in the Fibonacci sequence using an iterative approach.

- Input: Position in the sequence (non-negative integer)
- Output: The Fibonacci number at that position
- Time complexity: O(n)
- Space complexity: O(1)

#### `calculate_circle_properties(radius: float) -> Dict[str, float]`

Computes various properties of a circle including area, circumference, and diameter.

- Uses math.pi for precise calculations
- Returns a dictionary with all properties
- Raises ValueError for negative radius

### String Processing

#### `validate_email(email: str) -> bool`

Performs basic email validation with the following checks:

- Single @ symbol
- Valid local part
- Valid domain with at least one dot
- Minimum length requirements

#### `process_text_data(text: str, case_sensitive: bool = False) -> Dict[str, int]`

Analyzes text to generate word frequency statistics:

- Optional case sensitivity
- Returns a dictionary of word counts
- Handles empty strings and special cases

#### `is_palindrome(text: str, ignore_case: bool = True, ignore_spaces: bool = True) -> bool`

Checks if a string reads the same forwards and backwards:

- Configurable case sensitivity
- Option to ignore spaces
- Fast implementation using string slicing

### Data Structure Operations

#### `merge_sorted_lists(list1: List[int], list2: List[int]) -> List[int]`

Efficiently merges two sorted lists:

- Uses two-pointer technique
- Maintains sorting order
- O(n + m) time complexity
- O(n + m) space complexity

### Time and Date Handling

#### `format_duration(seconds: int) -> str`

Converts seconds into a human-readable duration string:

- Handles multiple time units (years to seconds)
- Grammatically correct pluralization
- Natural language formatting

#### `generate_date_range(start_date: datetime, end_date: datetime, include_weekends: bool = True) -> List[datetime]`

Creates a list of dates between two points:

- Optional weekend filtering
- Inclusive of end date
- Proper error handling for invalid ranges

### Error Handling

#### `safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: Optional[float] = None) -> Optional[float]`

Demonstrates robust error handling:

- Handles division by zero
- Type conversion errors
- Configurable default value

### Temperature Processing

#### `calculate_average_temperature(temperatures: List[float]) -> float`

Calculates the mean temperature from a list:

- Input validation
- Handles empty list cases
- Returns precise floating-point average

## Examples

### Working with Fibonacci Numbers

```python
# Calculate first 10 Fibonacci numbers
fibs = [calculate_fibonacci(i) for i in range(10)]
print(fibs)  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

### Text Analysis

```python
# Analyze word frequency in a text
text = "Hello world hello Python world Python"
freq = process_text_data(text)
print(freq)  # {'hello': 2, 'world': 2, 'python': 2}
```

### Date Range Generation

```python
from datetime import datetime

# Generate weekday dates for a week
start = datetime(2024, 1, 1)
end = datetime(2024, 1, 7)
dates = generate_date_range(start, end, include_weekends=False)
```

## FAQ

### Q: Why use these functions instead of built-in alternatives?

A: These functions provide additional error handling, type safety, and convenience features not found in built-in functions. They also serve as educational examples of Python best practices.

### Q: Are these functions thread-safe?

A: Yes, all functions are stateless and thread-safe. They don't modify any global state or shared resources.

### Q: What Python versions are supported?

A: The code is compatible with Python 3.7+ due to the use of type hints and f-strings.

### Q: How can I contribute?

A: Contributions are welcome! Please see the Contributing section below.

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functions
4. Ensure all tests pass
5. Submit a pull request

Please follow these guidelines:

- Use type hints for all functions
- Include comprehensive docstrings
- Add examples in docstrings
- Follow PEP 8 style guidelines
- Write unit tests for new features
