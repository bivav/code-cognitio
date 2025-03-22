"""Module for extracting information from Python files."""

import ast
import os
import logging
from typing import Dict, List, Any, Optional, Iterator, Tuple, Set
from pathlib import Path

from src.extractors.base_extractor import BaseExtractor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PythonExtractor(BaseExtractor):
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

            # Extract function and class definitions
            extracted_items = self._extract_from_content(file_content, file_path)

            # Analyze function usage in the file
            usage_info = self._analyze_function_usage(file_content, extracted_items)

            # Add usage information to each extracted function
            for item in extracted_items:
                if item["type"] in ["function", "method"]:
                    item_id = item["full_name"]
                    if item_id in usage_info:
                        item["usage"] = usage_info[item_id]

            return extracted_items
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

    def extract_from_content(
        self, content: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Extract code information from Python content.

        Args:
            content: Python code as string
            file_path: Path to the file (for reference)

        Returns:
            List of extracted items
        """
        # Use the existing private method, which already does the work
        return self._extract_from_content(content, file_path)

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

            # Create a map of all classes and functions for context reference
            code_map = self._build_code_map(tree)

            # Extract context-based relationships
            context_relationships = self._analyze_code_relationships(tree, code_map)

            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self._extract_function_info(node, file_path)

                    # Add surrounding code context
                    context = self._extract_code_context(
                        node, tree, code_map, file_path
                    )
                    if context:
                        func_info["context"] = context

                    # Add relationships if any
                    node_id = f"function:{node.name}"
                    if node_id in context_relationships:
                        func_info["relationships"] = context_relationships[node_id]

                    # Identify common patterns in functions
                    patterns = self._identify_function_patterns(node)
                    if patterns:
                        func_info["patterns"] = patterns

                    extracted_items.append(func_info)
                elif isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node, file_path)

                    # Add surrounding code context
                    context = self._extract_code_context(
                        node, tree, code_map, file_path
                    )
                    if context:
                        class_info["context"] = context

                    # Add relationships if any
                    node_id = f"class:{node.name}"
                    if node_id in context_relationships:
                        class_info["relationships"] = context_relationships[node_id]

                    # Identify common design patterns in classes
                    class_patterns = self._identify_class_patterns(node)
                    if class_patterns:
                        class_info["patterns"] = class_patterns

                    extracted_items.append(class_info)

                    # Extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = self._extract_function_info(
                                item, file_path, class_name=node.name
                            )

                            # Add surrounding code context
                            context = self._extract_code_context(
                                item, node, code_map, file_path, in_class=True
                            )
                            if context:
                                method_info["context"] = context

                            # Add relationships if any
                            method_id = f"method:{node.name}.{item.name}"
                            if method_id in context_relationships:
                                method_info["relationships"] = context_relationships[
                                    method_id
                                ]

                            # Identify common patterns in methods
                            method_patterns = self._identify_function_patterns(
                                item, is_method=True
                            )
                            if method_patterns:
                                method_info["patterns"] = method_patterns

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
        Extract information from a function definition node.

        Args:
            node: The function definition node
            file_path: Path to the file containing the function
            class_name: Name of the class if this is a method

        Returns:
            Dictionary containing function information
        """
        # Get docstring if available
        docstring = ast.get_docstring(node)

        # Extract parameter information
        params = []
        for arg in node.args.args:
            param_info = {"name": arg.arg}

            # Extract parameter type if available
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param_info["type"] = arg.annotation.id
                elif isinstance(arg.annotation, ast.Attribute):
                    param_info["type"] = self._format_attribute(arg.annotation)
                elif isinstance(arg.annotation, ast.Subscript):
                    param_info["type"] = self._format_subscript(arg.annotation)
                else:
                    param_info["type"] = ast.unparse(arg.annotation)

            params.append(param_info)

        # Extract return type if available
        return_type = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Attribute):
                return_type = self._format_attribute(node.returns)
            elif isinstance(node.returns, ast.Subscript):
                return_type = self._format_subscript(node.returns)
            else:
                return_type = ast.unparse(node.returns)

        # Parse function name into a meaningful phrase
        readable_name = self._function_name_to_phrase(node.name)

        # Create function information
        func_info = {
            "type": "method" if class_name else "function",
            "name": node.name,
            "readable_name": readable_name,
            "class_name": class_name,
            "full_name": f"{class_name}.{node.name}" if class_name else node.name,
            "docstring": docstring if docstring else "",
            "file_path": file_path,
            "lineno": node.lineno,
            "params": params,
            "return_type": return_type,
            "content_type": "code",
        }

        # Extract function body
        func_info["body"] = self._extract_function_body(node)

        # Extract key operations in the function
        func_info["key_operations"] = self._extract_key_operations(node)

        return func_info

    def _format_attribute(self, node: ast.Attribute) -> str:
        """Format an attribute node as a string."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._format_attribute(node.value)}.{node.attr}"
        return f"?.{node.attr}"

    def _format_subscript(self, node: ast.Subscript) -> str:
        """Format a subscript node as a string."""
        if hasattr(ast, "unparse"):  # Python 3.9+
            return ast.unparse(node)

        # Simplified fallback for earlier Python versions
        value = ""
        if isinstance(node.value, ast.Name):
            value = node.value.id
        elif isinstance(node.value, ast.Attribute):
            value = self._format_attribute(node.value)

        return f"{value}[...]"

    def _function_name_to_phrase(self, name: str) -> str:
        """Convert function name to a readable phrase."""
        # Handle special cases
        if name.startswith("__") and name.endswith("__"):
            special_methods = {
                "__init__": "initialize object",
                "__str__": "convert to string",
                "__repr__": "get representation",
                "__eq__": "check equality",
                "__lt__": "compare less than",
                "__gt__": "compare greater than",
                "__le__": "compare less than or equal",
                "__ge__": "compare greater than or equal",
                "__add__": "add objects",
                "__sub__": "subtract objects",
                "__mul__": "multiply objects",
                "__div__": "divide objects",
                "__call__": "make callable",
                "__enter__": "enter context",
                "__exit__": "exit context",
                "__len__": "get length",
                "__getitem__": "get item by key",
                "__setitem__": "set item by key",
                "__delitem__": "delete item by key",
                "__iter__": "iterate over object",
                "__next__": "get next item",
            }
            if name in special_methods:
                return special_methods[name]
            return f"special method {name}"

        # Split by underscores or camelCase
        if "_" in name:
            words = name.split("_")
        else:
            # Handle camelCase
            words = []
            current_word = ""
            for char in name:
                if char.isupper() and current_word:
                    words.append(current_word)
                    current_word = char.lower()
                else:
                    current_word += char
            if current_word:
                words.append(current_word)

        # Process common prefixes
        if words and len(words) > 1:
            common_prefixes = {
                "get": "get",
                "set": "set",
                "is": "check if",
                "has": "check if has",
                "calc": "calculate",
                "calculate": "calculate",
                "compute": "compute",
                "find": "find",
                "search": "search for",
                "fetch": "fetch",
                "load": "load",
                "save": "save",
                "store": "store",
                "update": "update",
                "delete": "delete",
                "remove": "remove",
                "add": "add",
                "create": "create",
                "build": "build",
                "convert": "convert",
                "transform": "transform",
                "process": "process",
                "handle": "handle",
                "validate": "validate",
                "check": "check",
                "parse": "parse",
                "format": "format",
                "render": "render",
                "display": "display",
                "show": "show",
                "print": "print",
                "log": "log",
                "init": "initialize",
                "setup": "set up",
                "cleanup": "clean up",
                "start": "start",
                "stop": "stop",
                "begin": "begin",
                "end": "end",
                "open": "open",
                "close": "close",
                "read": "read",
                "write": "write",
                "send": "send",
                "receive": "receive",
                "extract": "extract",
            }

            if words[0] in common_prefixes:
                prefix = common_prefixes[words[0]]
                return f"{prefix} {' '.join(words[1:])}"

        # Default: just join the words
        return " ".join(words)

    def _extract_function_body(self, node: ast.FunctionDef) -> str:
        """Extract the function body as a string."""
        try:
            if hasattr(ast, "unparse"):  # Python 3.9+
                # Get the function body without the decorator and signature
                body_nodes = ast.Module(body=node.body, type_ignores=[])
                return ast.unparse(body_nodes)
            else:
                # For earlier Python versions, return simplified representation
                return "\n".join(
                    [
                        f"Line {child.lineno}: {type(child).__name__}"
                        for child in node.body
                        if hasattr(child, "lineno")
                    ]
                )
        except Exception as e:
            logger.error(f"Error extracting function body: {str(e)}")
            return ""

    def _extract_key_operations(self, node: ast.FunctionDef) -> List[str]:
        """Extract key operations performed in the function."""
        operations = []

        for child_node in ast.walk(node):
            # Function calls
            if isinstance(child_node, ast.Call):
                if isinstance(child_node.func, ast.Name):
                    operations.append(f"calls function {child_node.func.id}")
                elif isinstance(child_node.func, ast.Attribute):
                    if isinstance(child_node.func.value, ast.Name):
                        operations.append(
                            f"uses {child_node.func.value.id}.{child_node.func.attr}"
                        )

            # Return statements with values
            elif isinstance(child_node, ast.Return) and child_node.value:
                operations.append("returns a value")

            # Assignments
            elif isinstance(child_node, ast.Assign):
                if len(child_node.targets) == 1 and isinstance(
                    child_node.targets[0], ast.Name
                ):
                    operations.append(f"assigns to variable {child_node.targets[0].id}")

            # Control flow
            elif isinstance(child_node, ast.If):
                operations.append("uses conditional logic")
            elif isinstance(child_node, ast.For):
                operations.append("uses loop")
            elif isinstance(child_node, ast.While):
                operations.append("uses while loop")
            elif isinstance(child_node, ast.Try):
                operations.append("uses exception handling")

        # Return unique operations
        return list(set(operations))

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

    def _identify_function_patterns(
        self, node: ast.FunctionDef, is_method: bool = False
    ) -> List[str]:
        """
        Identify common patterns in function definitions.

        Args:
            node: Function definition node
            is_method: Whether the function is a method of a class

        Returns:
            List of identified patterns
        """
        patterns = []

        # Check for getter/setter pattern
        if node.name.startswith("get_") or node.name.startswith("set_"):
            patterns.append("accessor" if node.name.startswith("get_") else "mutator")

        # Check for property pattern (Python decorators)
        if node.decorator_list:
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == "property":
                    patterns.append("property getter")
                elif isinstance(decorator, ast.Attribute) and decorator.attr in (
                    "setter",
                    "deleter",
                ):
                    patterns.append(f"property {decorator.attr}")

        # Check for factory pattern
        if (
            node.name.startswith("create_")
            or node.name.startswith("build_")
            or node.name.startswith("make_")
        ):
            # Look for return statements that create objects
            for child in ast.walk(node):
                if isinstance(child, ast.Return) and isinstance(child.value, ast.Call):
                    patterns.append("factory method")
                    break

        # Check for validation pattern
        if (
            node.name.startswith("validate_")
            or node.name.startswith("check_")
            or node.name.startswith("is_valid_")
            or node.name.startswith("is_")
        ):
            patterns.append("validation")

        # Check for callback pattern
        if "callback" in node.name or "handler" in node.name or "on_" in node.name:
            patterns.append("callback/event handler")

        # Check for iterator pattern
        if node.name == "__iter__" or node.name == "__next__":
            patterns.append("iterator")

        # Check for context manager pattern
        if node.name == "__enter__" or node.name == "__exit__":
            patterns.append("context manager")

        # Check for CRUD operations
        crud_patterns = {
            "create": ["create", "add", "insert", "new"],
            "read": ["read", "get", "fetch", "retrieve", "find", "search"],
            "update": ["update", "modify", "change", "edit", "set"],
            "delete": ["delete", "remove", "drop", "clear"],
        }

        for operation, keywords in crud_patterns.items():
            for keyword in keywords:
                if node.name.startswith(keyword + "_") or node.name == keyword:
                    patterns.append(f"CRUD {operation} operation")
                    break

        # Check for decorator pattern
        if is_method and node.name == "decorate":
            patterns.append("decorator")

        # Check for initialization
        if node.name == "__init__":
            patterns.append("constructor")

        # Check for API endpoint handler patterns
        api_patterns = self._identify_api_patterns(node)
        if api_patterns:
            patterns.extend(api_patterns)

        # Check for data transformation patterns
        if any(
            keyword in node.name
            for keyword in ["transform", "convert", "format", "parse"]
        ):
            patterns.append("data transformation")

        # Check for error handling patterns
        has_try_except = any(isinstance(child, ast.Try) for child in node.body)
        if has_try_except:
            patterns.append("error handling")

        return patterns

    def _identify_api_patterns(self, node: ast.FunctionDef) -> List[str]:
        """
        Identify common API endpoint patterns in functions.

        Args:
            node: Function definition node

        Returns:
            List of identified API patterns
        """
        patterns = []

        # Check for common API endpoint names
        api_keywords = ["endpoint", "api", "route", "handler", "controller"]
        if any(keyword in node.name for keyword in api_keywords):
            patterns.append("API endpoint")

        # Check for decorators that might indicate API endpoints
        api_decorators = ["route", "get", "post", "put", "delete", "patch", "api"]
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Name)
                and decorator.id.lower() in api_decorators
            ):
                patterns.append(f"API endpoint ({decorator.id.upper()})")
            elif (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id.lower() in api_decorators
            ):
                patterns.append(f"API endpoint ({decorator.func.id.upper()})")
            elif (
                isinstance(decorator, ast.Attribute)
                and decorator.attr.lower() in api_decorators
            ):
                patterns.append(f"API endpoint ({decorator.attr.upper()})")

        # Check for framework-specific patterns
        flask_patterns = self._identify_flask_patterns(node)
        if flask_patterns:
            patterns.extend(flask_patterns)

        django_patterns = self._identify_django_patterns(node)
        if django_patterns:
            patterns.extend(django_patterns)

        fastapi_patterns = self._identify_fastapi_patterns(node)
        if fastapi_patterns:
            patterns.extend(fastapi_patterns)

        return patterns

    def _identify_flask_patterns(self, node: ast.FunctionDef) -> List[str]:
        """Identify Flask-specific patterns in functions."""
        patterns = []

        # Check for Flask route decorators
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
            ):

                if decorator.func.attr == "route" or decorator.func.attr in [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                ]:
                    patterns.append(f"Flask {decorator.func.attr} endpoint")

        return patterns

    def _identify_django_patterns(self, node: ast.FunctionDef) -> List[str]:
        """Identify Django-specific patterns in functions."""
        patterns = []

        # Check for Django view decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in [
                "login_required",
                "permission_required",
            ]:
                patterns.append(f"Django {decorator.id} view")
            elif isinstance(decorator, ast.Call) and isinstance(
                decorator.func, ast.Name
            ):
                if decorator.func.id in ["api_view", "require_http_methods"]:
                    patterns.append("Django REST API view")

        return patterns

    def _identify_fastapi_patterns(self, node: ast.FunctionDef) -> List[str]:
        """Identify FastAPI-specific patterns in functions."""
        patterns = []

        # Check for FastAPI route decorators
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
            ):

                if decorator.func.attr in ["get", "post", "put", "delete", "patch"]:
                    patterns.append(f"FastAPI {decorator.func.attr} endpoint")

        return patterns

    def _identify_class_patterns(self, node: ast.ClassDef) -> List[str]:
        """
        Identify common design patterns in class definitions.

        Args:
            node: Class definition node

        Returns:
            List of identified patterns
        """
        patterns = []

        # Get base class names
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(
                    f"{base.value.id}.{base.attr}"
                    if isinstance(base.value, ast.Name)
                    else base.attr
                )

        # Check for common Python patterns in class names
        name = node.name.lower()

        # Check for singleton pattern
        for item in node.body:
            # Look for class variables that might indicate a singleton
            if (
                isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
                and item.target.id == "_instance"
            ):
                patterns.append("singleton")
            # Look for __new__ method which is often used in singletons
            if isinstance(item, ast.FunctionDef) and item.name == "__new__":
                patterns.append("singleton")

        # Check for factory pattern
        if "factory" in name:
            patterns.append("factory")

        # Check for common design patterns
        pattern_indicators = {
            "adapter": ["adapter"],
            "decorator": ["decorator"],
            "observer": ["observer", "listener", "subscriber"],
            "strategy": ["strategy"],
            "command": ["command", "action"],
            "proxy": ["proxy"],
            "builder": ["builder"],
            "composite": ["composite"],
            "iterator": ["iterator"],
            "prototype": ["prototype"],
            "state": ["state"],
            "template": ["template"],
            "visitor": ["visitor"],
        }

        for pattern, keywords in pattern_indicators.items():
            if any(keyword in name for keyword in keywords):
                patterns.append(pattern)

        # Check for common base class patterns
        if (
            "exception" in name
            or "error" in name
            or any(
                "error" in base.lower() or "exception" in base.lower()
                for base in base_classes
            )
        ):
            patterns.append("exception")

        if "abstract" in name or any("abc" in base.lower() for base in base_classes):
            patterns.append("abstract base class")

        if "mixin" in name or "interface" in name:
            patterns.append("mixin/interface")

        # Check for DAO/Repository pattern
        if any(keyword in name for keyword in ["repository", "dao", "data"]):
            patterns.append("data access object")

        # Check for service pattern
        if "service" in name:
            patterns.append("service")

        # Check for controller pattern
        if "controller" in name:
            patterns.append("controller")

        # Check for model pattern
        if "model" in name:
            patterns.append("model")

        # Check for utility or helper class
        if any(keyword in name for keyword in ["util", "utils", "helper", "helpers"]):
            patterns.append("utility")

        # Check for data container/structure
        has_instance_vars = False
        has_methods = False
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and not item.name.startswith("__"):
                has_methods = True
            elif isinstance(item, ast.Assign):
                has_instance_vars = True

        if has_instance_vars and not has_methods:
            patterns.append("data container")

        # Look for enum pattern
        constant_count = 0
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constant_count += 1

        if constant_count > 2:
            patterns.append("enumeration")

        return patterns

    def _analyze_function_usage(
        self, content: str, extracted_items: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze how functions are used within a file's content.

        Args:
            content: The Python file content
            extracted_items: List of extracted functions and classes

        Returns:
            Dictionary mapping function names to usage information
        """
        usage_info = {}

        try:
            tree = ast.parse(content)

            # Build a map of defined functions
            defined_functions = {}
            for item in extracted_items:
                if item["type"] in ["function", "method"]:
                    defined_functions[item["name"]] = item["full_name"]

            # Find all function calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    called_func = None

                    # Direct function call: func()
                    if isinstance(node.func, ast.Name):
                        called_func = node.func.id

                    # Method call: obj.method()
                    elif isinstance(node.func, ast.Attribute) and isinstance(
                        node.func.value, ast.Name
                    ):
                        # We only track method calls on objects, not chained calls
                        called_func = f"{node.func.value.id}.{node.func.attr}"

                    if called_func and called_func in defined_functions:
                        func_id = defined_functions[called_func]

                        if func_id not in usage_info:
                            usage_info[func_id] = {
                                "call_count": 0,
                                "callers": set(),
                                "arg_patterns": [],
                                "context_keywords": set(),
                            }

                        usage_info[func_id]["call_count"] += 1

                        # Track the calling function
                        for parent in ast.walk(tree):
                            if (
                                isinstance(parent, ast.FunctionDef)
                                and parent != node
                                and node in ast.walk(parent)
                            ):
                                if parent.name in defined_functions:
                                    caller = defined_functions[parent.name]
                                    usage_info[func_id]["callers"].add(caller)

                        # Analyze argument patterns
                        arg_pattern = self._analyze_arg_pattern(node)
                        if arg_pattern:
                            usage_info[func_id]["arg_patterns"].append(arg_pattern)

                        # Get surrounding context
                        context = self._get_call_context(node, tree)
                        if context:
                            usage_info[func_id]["context_keywords"].update(context)

            # Convert sets to lists for JSON serialization
            for func_id, info in usage_info.items():
                info["callers"] = list(info["callers"])
                info["context_keywords"] = list(info["context_keywords"])

                # Analyze arg patterns to find common usage
                if info["arg_patterns"]:
                    info["common_usage"] = self._determine_common_usage(
                        info["arg_patterns"]
                    )

        except Exception as e:
            logger.error(f"Error analyzing function usage: {str(e)}")

        return usage_info

    def _analyze_arg_pattern(self, call_node: ast.Call) -> Dict[str, Any]:
        """
        Analyze the argument pattern of a function call.

        Args:
            call_node: The function call node

        Returns:
            Dictionary with argument pattern information or None
        """
        try:
            args_info = {
                "positional_count": len(call_node.args),
                "keyword_count": len(call_node.keywords),
                "total_args": len(call_node.args) + len(call_node.keywords),
                "keyword_args": [kw.arg for kw in call_node.keywords if kw.arg],
            }

            # Categorize common patterns
            if args_info["positional_count"] == 0 and args_info["keyword_count"] == 0:
                args_info["pattern"] = "no_args"
            elif args_info["positional_count"] > 0 and args_info["keyword_count"] == 0:
                args_info["pattern"] = "positional_only"
            elif args_info["positional_count"] == 0 and args_info["keyword_count"] > 0:
                args_info["pattern"] = "keyword_only"
            else:
                args_info["pattern"] = "mixed"

            return args_info
        except Exception as e:
            logger.error(f"Error analyzing argument pattern: {str(e)}")
            return None

    def _get_call_context(self, call_node: ast.Call, tree: ast.Module) -> Set[str]:
        """
        Extract context keywords from the surroundings of a function call.

        Args:
            call_node: The function call node
            tree: The AST tree

        Returns:
            Set of context keywords
        """
        context_keywords = set()

        try:
            # Look at parent nodes for context
            for parent in ast.walk(tree):
                if hasattr(parent, "body") and any(
                    call_node in ast.walk(child) for child in parent.body
                ):
                    # If we're in an if statement condition, that provides context
                    if isinstance(parent, ast.If):
                        # Extract variable names from the test condition
                        for node in ast.walk(parent.test):
                            if isinstance(node, ast.Name):
                                context_keywords.add(node.id)

                    # If we're in a loop, that's contextual
                    elif isinstance(parent, (ast.For, ast.While)):
                        context_keywords.add("in_loop")

                    # If we're in a try/except, that's contextual
                    elif isinstance(parent, ast.Try):
                        context_keywords.add("in_exception_handler")

                    # If we're in an assignment, extract the target variable
                    elif isinstance(parent, ast.Assign):
                        for target in parent.targets:
                            if isinstance(target, ast.Name):
                                context_keywords.add(f"assigned_to_{target.id}")

                    # For error handling
                    elif isinstance(parent, ast.ExceptHandler):
                        context_keywords.add("in_error_handler")

                    # For context managers (with statement)
                    elif isinstance(parent, ast.With):
                        context_keywords.add("in_context_manager")

        except Exception as e:
            logger.error(f"Error getting call context: {str(e)}")

        return context_keywords

    def _determine_common_usage(self, arg_patterns: List[Dict[str, Any]]) -> List[str]:
        """
        Determine common usage patterns from argument patterns.

        Args:
            arg_patterns: List of argument pattern dictionaries

        Returns:
            List of common usage pattern descriptions
        """
        common_patterns = []
        pattern_counts = {}
        keyword_counts = {}

        # Count patterns and keywords
        for pattern in arg_patterns:
            pattern_type = pattern.get("pattern", "unknown")

            if pattern_type not in pattern_counts:
                pattern_counts[pattern_type] = 0
            pattern_counts[pattern_type] += 1

            for keyword in pattern.get("keyword_args", []):
                if keyword not in keyword_counts:
                    keyword_counts[keyword] = 0
                keyword_counts[keyword] += 1

        # Determine most common pattern
        most_common_pattern = max(
            pattern_counts.items(), key=lambda x: x[1], default=(None, 0)
        )
        if most_common_pattern[0]:
            pattern_percentage = (most_common_pattern[1] / len(arg_patterns)) * 100
            if pattern_percentage > 50:  # If more than 50% of calls use this pattern
                if most_common_pattern[0] == "no_args":
                    common_patterns.append("typically called with no arguments")
                elif most_common_pattern[0] == "positional_only":
                    common_patterns.append(
                        "typically called with positional arguments only"
                    )
                elif most_common_pattern[0] == "keyword_only":
                    common_patterns.append(
                        "typically called with keyword arguments only"
                    )
                elif most_common_pattern[0] == "mixed":
                    common_patterns.append(
                        "typically called with both positional and keyword arguments"
                    )

        # Determine most common keywords
        common_keywords = []
        for keyword, count in keyword_counts.items():
            keyword_percentage = (count / len(arg_patterns)) * 100
            if keyword_percentage > 30:  # If more than 30% of calls use this keyword
                common_keywords.append(keyword)

        if common_keywords:
            common_patterns.append(
                f"commonly used with keywords: {', '.join(common_keywords)}"
            )

        return common_patterns

    def _build_code_map(self, tree: ast.Module) -> Dict[str, Dict[str, Any]]:
        """
        Build a map of all code objects in the module for context referencing.

        Args:
            tree: The AST tree of the module

        Returns:
            Dictionary mapping node IDs to information about code objects
        """
        code_map = {}

        # Collect all classes with their locations
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                code_map[f"class:{node.name}"] = {
                    "type": "class",
                    "name": node.name,
                    "lineno": node.lineno,
                    "end_lineno": getattr(
                        node, "end_lineno", node.lineno + len(node.body)
                    ),
                    "methods": [],
                    "attributes": [],
                }

                # Collect methods and attributes
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        code_map[f"class:{node.name}"]["methods"].append(item.name)
                        code_map[f"method:{node.name}.{item.name}"] = {
                            "type": "method",
                            "name": item.name,
                            "class_name": node.name,
                            "lineno": item.lineno,
                            "end_lineno": getattr(
                                item, "end_lineno", item.lineno + len(item.body)
                            ),
                        }
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                code_map[f"class:{node.name}"]["attributes"].append(
                                    target.id
                                )

            elif isinstance(node, ast.FunctionDef) and not hasattr(
                node, "parent_class"
            ):
                code_map[f"function:{node.name}"] = {
                    "type": "function",
                    "name": node.name,
                    "lineno": node.lineno,
                    "end_lineno": getattr(
                        node, "end_lineno", node.lineno + len(node.body)
                    ),
                }

        return code_map

    def _analyze_code_relationships(
        self, tree: ast.Module, code_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Analyze relationships between code objects (e.g., function calls, inheritance).

        Args:
            tree: The AST tree of the module
            code_map: Map of code objects

        Returns:
            Dictionary mapping node IDs to their relationships
        """
        relationships = {}

        # Analyze function calls
        for node in ast.walk(tree):
            # Track containing function/method for this part of the AST
            containing_function = None
            containing_class = None

            # Find the parent function/method for call nodes
            for parent in ast.walk(tree):
                if isinstance(parent, ast.FunctionDef) and node in ast.walk(parent):
                    containing_function = parent.name
                    # Check if this is a method
                    for cls_node in ast.walk(tree):
                        if (
                            isinstance(cls_node, ast.ClassDef)
                            and parent in cls_node.body
                        ):
                            containing_class = cls_node.name
                            break
                    break

            # Analyze function calls
            if isinstance(node, ast.Call):
                # Get the caller ID
                caller_id = None
                if containing_function and containing_class:
                    caller_id = f"method:{containing_class}.{containing_function}"
                elif containing_function:
                    caller_id = f"function:{containing_function}"

                if caller_id:
                    # Get the called function
                    if isinstance(node.func, ast.Name):
                        called_id = f"function:{node.func.id}"
                        if called_id in code_map:
                            if caller_id not in relationships:
                                relationships[caller_id] = []
                            relationships[caller_id].append(
                                {
                                    "type": "calls",
                                    "target": called_id,
                                    "name": code_map[called_id]["name"],
                                }
                            )
                    elif isinstance(node.func, ast.Attribute) and isinstance(
                        node.func.value, ast.Name
                    ):
                        # Method call
                        called_id = f"method:{node.func.value.id}.{node.func.attr}"
                        if called_id in code_map:
                            if caller_id not in relationships:
                                relationships[caller_id] = []
                            relationships[caller_id].append(
                                {
                                    "type": "calls",
                                    "target": called_id,
                                    "name": f"{node.func.value.id}.{node.func.attr}",
                                }
                            )

            # Analyze class inheritance
            elif isinstance(node, ast.ClassDef):
                class_id = f"class:{node.name}"

                # Check base classes
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_id = f"class:{base.id}"
                        if base_id in code_map:
                            if class_id not in relationships:
                                relationships[class_id] = []
                            relationships[class_id].append(
                                {
                                    "type": "inherits_from",
                                    "target": base_id,
                                    "name": base.id,
                                }
                            )

        return relationships

    def _extract_code_context(
        self,
        node: ast.AST,
        parent: ast.AST,
        code_map: Dict[str, Dict[str, Any]],
        file_path: str,
        in_class: bool = False,
    ) -> Dict[str, Any]:
        """
        Extract surrounding code context for a node.

        Args:
            node: The AST node
            parent: Parent node or tree
            code_map: Map of code objects
            file_path: Path to the file
            in_class: Whether the node is inside a class

        Returns:
            Dictionary with context information
        """
        context = {}

        # Get the node's type and name
        node_type = None
        node_name = None

        if isinstance(node, ast.FunctionDef):
            node_type = "method" if in_class else "function"
            node_name = node.name
        elif isinstance(node, ast.ClassDef):
            node_type = "class"
            node_name = node.name

        if not node_type or not node_name:
            return {}

        # Get file context (imports, module-level variables)
        if isinstance(parent, ast.Module):
            imports = []
            global_vars = []

            for item in parent.body:
                # Collect imports
                if isinstance(item, (ast.Import, ast.ImportFrom)):
                    try:
                        import_text = (
                            ast.unparse(item).strip()
                            if hasattr(ast, "unparse")
                            else f"import at line {item.lineno}"
                        )
                        imports.append(import_text)
                    except Exception:
                        imports.append(f"import at line {item.lineno}")

                # Collect global variables
                elif isinstance(item, ast.Assign) and all(
                    isinstance(target, ast.Name) for target in item.targets
                ):
                    for target in item.targets:
                        global_vars.append(target.id)

            if imports:
                context["imports"] = imports[:10]  # Limit to avoid too much data

            if global_vars:
                context["global_variables"] = global_vars

        # Get neighboring functions/classes
        if node_type == "function":
            neighboring_funcs = []

            for key, info in code_map.items():
                if key.startswith("function:") and info["name"] != node_name:
                    # Check if they're close to each other (within 20 lines)
                    if abs(info["lineno"] - node.lineno) < 20:
                        neighboring_funcs.append(info["name"])

            if neighboring_funcs:
                context["neighboring_functions"] = neighboring_funcs

        # For methods, get other methods in the same class
        elif node_type == "method" and in_class and isinstance(parent, ast.ClassDef):
            related_methods = []
            class_attrs = []

            class_key = f"class:{parent.name}"
            if class_key in code_map:
                # Get methods
                for method_name in code_map[class_key]["methods"]:
                    if method_name != node_name:
                        related_methods.append(method_name)

                # Get attributes
                class_attrs = code_map[class_key]["attributes"]

            if related_methods:
                context["related_class_methods"] = related_methods

            if class_attrs:
                context["class_attributes"] = class_attrs

        # For classes, get inheritance hierarchy
        elif node_type == "class":
            # Superclasses
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(self._format_attribute(base))

            if bases:
                context["base_classes"] = bases

            # Get relationship information from the code map's analysis
            subclasses = []

            # Look for classes that might inherit from this one
            for key, info in code_map.items():
                if key.startswith("class:") and info["name"] != node_name:
                    # This is a simplified check - in production code you would use the relationships data
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == node_name:
                            subclasses.append(info["name"])
                            break

            if subclasses:
                context["subclasses"] = subclasses

        # Add file context
        if Path(file_path).exists():
            file_name = os.path.basename(file_path)
            dir_name = os.path.dirname(file_path)

            context["file_name"] = file_name
            context["directory"] = dir_name

            # Parse module from file path
            module_parts = []
            current_dir = dir_name
            while current_dir and os.path.exists(
                os.path.join(current_dir, "__init__.py")
            ):
                module_parts.insert(0, os.path.basename(current_dir))
                current_dir = os.path.dirname(current_dir)

            if module_parts:
                module_name = ".".join(module_parts)
                if file_name != "__init__.py":
                    module_name += f".{os.path.splitext(file_name)[0]}"
                context["module"] = module_name

        return context

    def get_supported_extensions(self) -> Set[str]:
        """
        Get the set of file extensions this extractor supports.

        Returns:
            Set of file extensions
        """
        return {".py", ".pyw", ".pyi"}
