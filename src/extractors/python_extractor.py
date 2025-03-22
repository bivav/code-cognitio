"""Module for extracting information from Python files."""

import ast
import os
import io
import logging
from typing import Dict, List, Any, Optional, Iterator, Tuple
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PythonExtractor:
    """Class for extracting information from Python files."""

    def __init__(
        self, large_file_threshold: int = 1024 * 1024, chunk_size: int = 100 * 1024
    ):
        """
        Initialize the Python extractor.

        Args:
            large_file_threshold: Threshold for considering a file as large (in bytes)
            chunk_size: Chunk size for processing large files (in bytes)
        """
        self.large_file_threshold = large_file_threshold
        self.chunk_size = chunk_size

    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract functions, docstrings, and other information from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            List of dictionaries containing extracted information
        """
        try:
            file_size = os.path.getsize(file_path)

            # Check if the file is too large
            if file_size > self.large_file_threshold:
                logger.info(
                    f"Large file detected: {file_path} ({file_size/1024/1024:.2f} MB). Processing in chunks."
                )
                return self._extract_from_large_file(file_path)

            # Process normal-sized file
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = file.read()

            return self._extract_from_content(file_content, file_path)
        except UnicodeDecodeError as e:
            logger.warning(
                f"Unicode decode error in {file_path}: {str(e)}. Trying with error handling."
            )
            return self._extract_with_error_handling(file_path)
        except MemoryError as e:
            logger.warning(
                f"Memory error while processing {file_path}: {str(e)}. Falling back to safer processing."
            )
            return self._extract_from_large_file(file_path)
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {str(e)}")
            return []

    def _extract_from_content(
        self, content: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Extract information from Python code content.

        Args:
            content: Python code as string
            file_path: Path to the file (for reference)

        Returns:
            List of extracted items
        """
        try:
            tree = ast.parse(content)
            extracted_items = []

            # Extract module-level docstring if it exists
            if isinstance(tree.body[0], ast.Expr) and isinstance(
                tree.body[0].value, ast.Str
            ):
                module_doc = {
                    "type": "module",
                    "name": os.path.basename(file_path),
                    "docstring": tree.body[0].value.s,
                    "file_path": file_path,
                    "lineno": 1,
                    "imports": self._extract_imports(tree),
                }
                extracted_items.append(module_doc)

            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self._extract_function_info(node, file_path)
                    extracted_items.append(func_info)
                elif isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node, file_path)
                    extracted_items.append(class_info)

                    # Extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = self._extract_function_info(
                                item, file_path, class_name=node.name
                            )
                            extracted_items.append(method_info)

            return extracted_items
        except SyntaxError as e:
            logger.warning(
                f"Syntax error while parsing Python content from {file_path}: {str(e)}"
            )
            # Try a more forgiving approach with partial parsing
            return self._extract_docstrings_with_regex(content, file_path)

    def _extract_with_error_handling(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract information from a file with error handling for encoding issues.

        Args:
            file_path: Path to the file

        Returns:
            List of extracted items
        """
        try:
            # Try with a more lenient error handler
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                content = file.read()

            logger.info(f"Successfully read {file_path} with 'replace' error handler")
            return self._extract_from_content(content, file_path)
        except Exception as e:
            logger.error(
                f"Failed to extract from {file_path} even with error handling: {str(e)}"
            )
            return []

    def _extract_from_large_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract information from a large file by processing it in chunks.

        Args:
            file_path: Path to the file

        Returns:
            List of extracted items
        """
        extracted_items = []

        try:
            # First pass: try to get the module docstring
            with open(file_path, "r", encoding="utf-8", errors="replace") as file:
                # Read first 10KB which should contain module docstring if any
                start_content = file.read(10 * 1024)

            try:
                tree = ast.parse(start_content)
                if isinstance(tree.body[0], ast.Expr) and isinstance(
                    tree.body[0].value, ast.Str
                ):
                    module_doc = {
                        "type": "module",
                        "name": os.path.basename(file_path),
                        "docstring": tree.body[0].value.s,
                        "file_path": file_path,
                        "lineno": 1,
                        "imports": [],  # Can't extract all imports from just the start
                    }
                    extracted_items.append(module_doc)
            except Exception as e:
                logger.warning(
                    f"Error parsing module docstring from {file_path}: {str(e)}"
                )

            # Second pass: extract function-by-function
            for func_content, line_start in self._read_functions(file_path):
                try:
                    # Try to parse this function
                    func_tree = ast.parse(func_content)

                    # Extract function/class nodes
                    for node in func_tree.body:
                        if isinstance(node, ast.FunctionDef):
                            # Adjust line number based on where we found this function
                            node.lineno += line_start - 1
                            func_info = self._extract_function_info(node, file_path)
                            extracted_items.append(func_info)
                        elif isinstance(node, ast.ClassDef):
                            # Adjust line number
                            node.lineno += line_start - 1
                            class_info = self._extract_class_info(node, file_path)
                            extracted_items.append(class_info)

                            # Extract methods
                            for item in node.body:
                                if isinstance(item, ast.FunctionDef):
                                    # Adjust line number
                                    item.lineno += line_start - 1
                                    method_info = self._extract_function_info(
                                        item, file_path, class_name=node.name
                                    )
                                    extracted_items.append(method_info)
                except Exception as e:
                    logger.debug(f"Error parsing function from {file_path}: {str(e)}")
                    # Continue to the next function
                    continue

            return extracted_items
        except Exception as e:
            logger.error(f"Error processing large file {file_path}: {str(e)}")
            return extracted_items  # Return whatever we managed to extract

    def _read_functions(self, file_path: str) -> Iterator[Tuple[str, int]]:
        """
        Read a file and yield content that looks like complete functions or classes.

        Args:
            file_path: Path to the file

        Yields:
            Tuples of (function_content, line_number)
        """
        import re

        # Patterns to detect function and class definitions
        func_pattern = re.compile(r"^def\s+\w+\s*\(")
        class_pattern = re.compile(r"^class\s+\w+\s*(\(|:)")

        # Read the file line by line
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            line_num = 0
            buffer = []
            buffer_start = 0
            in_definition = False
            indent_level = 0

            for line in file:
                line_num += 1

                # Detect the start of a new definition
                if not in_definition:
                    if func_pattern.match(line.lstrip()) or class_pattern.match(
                        line.lstrip()
                    ):
                        buffer = [line]
                        buffer_start = line_num
                        in_definition = True

                        # Calculate indent level (0 for top-level definitions)
                        indent_level = len(line) - len(line.lstrip())
                    continue

                # Add line to current definition
                buffer.append(line)

                # Check if this might be the end of the definition
                # We look for a line with the same or less indentation as the definition start
                current_indent = len(line) - len(line.lstrip()) if line.strip() else 999

                if (
                    current_indent <= indent_level
                    and line.strip()
                    and not line.strip().startswith("#")
                ):
                    # This appears to be the end of the definition
                    # Remove the last line (which belongs to the next definition)
                    content = "".join(buffer[:-1])
                    yield content, buffer_start

                    # Check if the current line is a new definition
                    if func_pattern.match(line.lstrip()) or class_pattern.match(
                        line.lstrip()
                    ):
                        buffer = [line]
                        buffer_start = line_num
                        indent_level = len(line) - len(line.lstrip())
                    else:
                        in_definition = False
                        buffer = []

            # Don't forget the last definition if any
            if buffer:
                content = "".join(buffer)
                yield content, buffer_start

    def _extract_docstrings_with_regex(
        self, content: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Extract docstrings using regex for cases where AST parsing fails.

        Args:
            content: Python code as string
            file_path: Path to the file

        Returns:
            List of extracted items with basic information
        """
        import re

        extracted_items = []

        # Regex patterns for functions, classes and docstrings
        func_pattern = re.compile(
            r'def\s+(\w+)\s*\([^)]*\)[^:]*:(?:\s*"""(.*?)""")?', re.DOTALL
        )
        class_pattern = re.compile(
            r'class\s+(\w+)(?:\([^)]*\))?[^:]*:(?:\s*"""(.*?)""")?', re.DOTALL
        )

        # Find all functions
        for match in func_pattern.finditer(content):
            func_name = match.group(1)
            docstring = match.group(2) or ""

            # Find the line number
            line_num = content[: match.start()].count("\n") + 1

            func_info = {
                "type": "function",
                "name": func_name,
                "full_name": func_name,
                "docstring": docstring,
                "parameters": [],  # Can't extract accurately with regex
                "returns": None,
                "file_path": file_path,
                "lineno": line_num,
                "class_name": None,
            }
            extracted_items.append(func_info)

        # Find all classes
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            docstring = match.group(2) or ""

            # Find the line number
            line_num = content[: match.start()].count("\n") + 1

            class_info = {
                "type": "class",
                "name": class_name,
                "docstring": docstring,
                "bases": [],  # Can't extract accurately with regex
                "file_path": file_path,
                "lineno": line_num,
            }
            extracted_items.append(class_info)

            # Try to find methods in this class
            class_content = content[match.start() :].split("\n")
            class_end = 0

            # Find class indentation and content
            for i, line in enumerate(class_content[1:], 1):
                if (
                    line.strip()
                    and not line.startswith(" ")
                    and not line.startswith("\t")
                ):
                    class_end = i
                    break

            class_content = "\n".join(class_content[: class_end if class_end else None])

            # Find methods in this class
            method_pattern = re.compile(
                r'def\s+(\w+)\s*\([^)]*\)[^:]*:(?:\s*"""(.*?)""")?', re.DOTALL
            )
            for m_match in method_pattern.finditer(class_content):
                method_name = m_match.group(1)
                method_docstring = m_match.group(2) or ""

                # Find the line number
                method_line_num = line_num + class_content[: m_match.start()].count(
                    "\n"
                )

                method_info = {
                    "type": "method",
                    "name": method_name,
                    "full_name": f"{class_name}.{method_name}",
                    "docstring": method_docstring,
                    "parameters": [],  # Can't extract accurately with regex
                    "returns": None,
                    "file_path": file_path,
                    "lineno": method_line_num,
                    "class_name": class_name,
                }
                extracted_items.append(method_info)

        return extracted_items

    def _extract_function_info(
        self, node: ast.FunctionDef, file_path: str, class_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract information from a function definition.

        Args:
            node: AST node for the function
            file_path: Path to the file containing the function
            class_name: Name of the class if this is a method

        Returns:
            Dictionary with function information
        """
        # Extract docstring
        docstring = ast.get_docstring(node) or ""

        # Extract parameters
        params = []
        returns = None

        try:
            for arg in node.args.args:
                param_name = arg.arg
                param_type = None

                # Extract type annotation if it exists
                if hasattr(arg, "annotation") and arg.annotation:
                    try:
                        param_type = ast.unparse(arg.annotation)
                    except (AttributeError, ValueError):
                        # ast.unparse is only available in Python 3.9+
                        # for earlier versions, we'll use a simple string representation
                        param_type = str(arg.annotation)

                params.append({"name": param_name, "type": param_type})
        except Exception as e:
            logger.warning(
                f"Error extracting parameters from {file_path}:{node.lineno}: {str(e)}"
            )

        # Extract return type annotation
        if hasattr(node, "returns") and node.returns:
            try:
                returns = ast.unparse(node.returns)
            except (AttributeError, ValueError):
                # Handle earlier Python versions
                returns = str(node.returns)

        func_type = "method" if class_name else "function"
        full_name = f"{class_name}.{node.name}" if class_name else node.name

        return {
            "type": func_type,
            "name": node.name,
            "full_name": full_name,
            "docstring": docstring,
            "parameters": params,
            "returns": returns,
            "file_path": file_path,
            "lineno": node.lineno,
            "class_name": class_name,
        }

    def _extract_class_info(self, node: ast.ClassDef, file_path: str) -> Dict[str, Any]:
        """
        Extract information from a class definition.

        Args:
            node: AST node for the class
            file_path: Path to the file containing the class

        Returns:
            Dictionary with class information
        """
        # Extract docstring
        docstring = ast.get_docstring(node) or ""

        # Extract base classes
        bases = []
        try:
            for base in node.bases:
                try:
                    bases.append(ast.unparse(base))
                except (AttributeError, ValueError):
                    # Handle earlier Python versions
                    bases.append(str(base))
        except Exception as e:
            logger.warning(
                f"Error extracting base classes from {file_path}:{node.lineno}: {str(e)}"
            )

        return {
            "type": "class",
            "name": node.name,
            "docstring": docstring,
            "bases": bases,
            "file_path": file_path,
            "lineno": node.lineno,
        }

    def _extract_imports(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """
        Extract import statements from the module.

        Args:
            tree: AST tree of the module

        Returns:
            List of dictionaries with import information
        """
        imports = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(
                        {"type": "import", "name": name.name, "asname": name.asname}
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    imports.append(
                        {
                            "type": "importfrom",
                            "module": module,
                            "name": name.name,
                            "asname": name.asname,
                        }
                    )

        return imports
