"""Module for extracting code information from JavaScript files."""

import re
import logging
from typing import Dict, List, Any, Set
from src.extractors.base_extractor import BaseExtractor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JavaScriptExtractor(BaseExtractor):
    """Class for extracting information from JavaScript files."""

    def __init__(self):
        """Initialize the JavaScript extractor."""
        # Regex patterns for JavaScript extraction
        self.function_pattern = re.compile(
            r"(?:export\s+)?(?:async\s+)?(?:function\s+)?(?P<name>[a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?P<params>\([^)]*\))\s*(?P<body>\{[\s\S]*?\})",
            re.MULTILINE,
        )
        self.class_pattern = re.compile(
            r"(?:export\s+)?class\s+(?P<name>[a-zA-Z_$][a-zA-Z0-9_$]*)(?:\s+extends\s+(?P<extends>[a-zA-Z_$][a-zA-Z0-9_$.]*))?(?P<body>\s*\{[\s\S]*?\})",
            re.MULTILINE,
        )
        self.method_pattern = re.compile(
            r"(?:async\s+)?(?P<name>[a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?P<params>\([^)]*\))\s*(?P<body>\{[\s\S]*?\})",
            re.MULTILINE,
        )
        self.arrow_function_pattern = re.compile(
            r"(?:export\s+)?(?:const|let|var)\s+(?P<name>[a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s+)?(?P<params>(?:\([^)]*\)|[a-zA-Z_$][a-zA-Z0-9_$]*))\s*=>\s*(?:(?P<body>\{[\s\S]*?\})|(?P<expression>[^;{]*?(?:;|\n)))",
            re.MULTILINE,
        )
        self.import_pattern = re.compile(
            r"import\s+(?:(?P<default>[a-zA-Z_$][a-zA-Z0-9_$]*)\s*,?\s*)?(?:\{\s*(?P<named>[^}]*)\s*\})?\s*from\s*['\"](?P<source>[^'\"]*)['\"]",
            re.MULTILINE,
        )
        self.jsx_component_pattern = re.compile(
            r"(?:export\s+)?(?:function|const)\s+(?P<name>[A-Z][a-zA-Z0-9_$]*)\s*(?:=\s*)?(?P<params>\([^)]*\))\s*(?:=>\s*)?(?P<body>\{[\s\S]*?\}|<[\s\S]*?>(?:[\s\S]*?)<\/[a-zA-Z_$][a-zA-Z0-9_$]*>)",
            re.MULTILINE,
        )
        self.jsdoc_pattern = re.compile(r"/\*\*(?P<content>[\s\S]*?)\*/", re.MULTILINE)

    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract code information from a JavaScript file.

        Args:
            file_path: Path to the JavaScript file

        Returns:
            List of extracted items
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            return self.extract_from_content(content, file_path)
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {str(e)}")
            return []

    def extract_from_content(
        self, content: str, file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Extract code information from JavaScript content.

        Args:
            content: JavaScript code as string
            file_path: Path to the file (for reference)

        Returns:
            List of extracted items
        """
        extracted_items = []

        # Extract imports
        imports = self._extract_imports(content)

        # Extract JSDoc comments and associate with code elements
        jsdocs = self._extract_jsdoc_comments(content)

        # Extract functions
        functions = self._extract_functions(content, jsdocs)
        extracted_items.extend(functions)

        # Extract classes and their methods
        classes = self._extract_classes(content, jsdocs)
        extracted_items.extend(classes)

        # Extract React components (for JSX files)
        if file_path.endswith((".jsx", ".tsx")):
            components = self._extract_react_components(content, jsdocs)
            extracted_items.extend(components)

        # Add file information to all extracted items
        for item in extracted_items:
            item["file_path"] = file_path
            item["language"] = "javascript"
            if imports:
                item["imports"] = imports

        return extracted_items

    def get_supported_extensions(self) -> Set[str]:
        """
        Get the set of file extensions this extractor supports.

        Returns:
            Set of file extensions
        """
        return {".js", ".jsx", ".ts", ".tsx"}

    def _extract_imports(self, content: str) -> List[str]:
        """
        Extract import statements from JavaScript content.

        Args:
            content: JavaScript code

        Returns:
            List of import statements
        """
        imports = []
        for match in self.import_pattern.finditer(content):
            source = match.group("source")
            if source:
                imports.append(source)

        return imports

    def _extract_jsdoc_comments(self, content: str) -> Dict[int, Dict[str, Any]]:
        """
        Extract JSDoc comments and their positions.

        Args:
            content: JavaScript code

        Returns:
            Dictionary mapping end positions to parsed JSDoc data
        """
        jsdocs = {}
        for match in self.jsdoc_pattern.finditer(content):
            jsdoc_content = match.group("content")
            end_pos = match.end()

            # Parse JSDoc content
            parsed = self._parse_jsdoc(jsdoc_content)
            jsdocs[end_pos] = parsed

        return jsdocs

    def _parse_jsdoc(self, jsdoc_content: str) -> Dict[str, Any]:
        """
        Parse JSDoc comment content.

        Args:
            jsdoc_content: Content of the JSDoc comment

        Returns:
            Parsed JSDoc data
        """
        parsed = {
            "description": "",
            "params": [],
            "returns": None,
            "throws": [],
            "examples": [],
        }

        # Extract description (first line until @tag)
        lines = jsdoc_content.split("\n")
        description_lines = []

        in_description = True
        for line in lines:
            line = line.strip().lstrip("* ")
            if not line:
                continue

            if line.startswith("@") and in_description:
                in_description = False

            if in_description:
                description_lines.append(line)
            else:
                # Parse tags
                if line.startswith("@param"):
                    param_match = re.match(
                        r"@param\s+(?:{(?P<type>[^}]*)})?\s*(?P<name>[^\s]+)?\s*(?P<desc>.*)?",
                        line,
                    )
                    if param_match:
                        param = {
                            "name": param_match.group("name") or "",
                            "type": param_match.group("type") or "",
                            "description": param_match.group("desc") or "",
                        }
                        parsed["params"].append(param)

                elif line.startswith("@returns") or line.startswith("@return"):
                    returns_match = re.match(
                        r"@returns?\s+(?:{(?P<type>[^}]*)})?\s*(?P<desc>.*)?", line
                    )
                    if returns_match:
                        parsed["returns"] = {
                            "type": returns_match.group("type") or "",
                            "description": returns_match.group("desc") or "",
                        }

                elif line.startswith("@throws") or line.startswith("@throw"):
                    throws_match = re.match(
                        r"@throws?\s+(?:{(?P<type>[^}]*)})?\s*(?P<desc>.*)?", line
                    )
                    if throws_match:
                        parsed["throws"].append(
                            {
                                "type": throws_match.group("type") or "",
                                "description": throws_match.group("desc") or "",
                            }
                        )

                elif line.startswith("@example"):
                    parsed["examples"].append(line.replace("@example", "").strip())

        parsed["description"] = " ".join(description_lines).strip()
        return parsed

    def _extract_functions(
        self, content: str, jsdocs: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract functions from JavaScript content.

        Args:
            content: JavaScript code
            jsdocs: Dictionary of JSDoc comments

        Returns:
            List of extracted functions
        """
        functions = []

        # Extract named functions
        for match in self.function_pattern.finditer(content):
            name = match.group("name")
            params_str = match.group("params")
            body = match.group("body")

            # Find JSDoc for this function
            func_start = match.start()
            docstring = None
            for jsdoc_end, jsdoc_data in jsdocs.items():
                # Find the closest JSDoc that appears right before the function
                if jsdoc_end < func_start and (func_start - jsdoc_end) < 10:
                    docstring = jsdoc_data
                    break

            function = {
                "type": "function",
                "name": name,
                "params": self._parse_parameters(params_str),
                "body": body[:200]
                + ("..." if len(body) > 200 else ""),  # Truncate long bodies
                "lineno": content[:func_start].count("\n") + 1,
                "readable_name": self._make_readable_name(name),
            }

            if docstring:
                function["docstring"] = docstring["description"]
                if docstring["params"]:
                    function["param_docs"] = docstring["params"]
                if docstring["returns"]:
                    function["return_docs"] = docstring["returns"]

            functions.append(function)

        # Extract arrow functions assigned to variables
        for match in self.arrow_function_pattern.finditer(content):
            name = match.group("name")
            params_str = match.group("params")
            body = (
                match.group("body")
                if match.group("body")
                else match.group("expression")
            )

            # Find JSDoc for this function
            func_start = match.start()
            docstring = None
            for jsdoc_end, jsdoc_data in jsdocs.items():
                if jsdoc_end < func_start and (func_start - jsdoc_end) < 10:
                    docstring = jsdoc_data
                    break

            function = {
                "type": "function",
                "name": name,
                "params": self._parse_parameters(params_str),
                "body": body[:200] + ("..." if len(body) > 200 else ""),
                "lineno": content[:func_start].count("\n") + 1,
                "readable_name": self._make_readable_name(name),
                "is_arrow_function": True,
            }

            if docstring:
                function["docstring"] = docstring["description"]
                if docstring["params"]:
                    function["param_docs"] = docstring["params"]
                if docstring["returns"]:
                    function["return_docs"] = docstring["returns"]

            functions.append(function)

        return functions

    def _extract_classes(
        self, content: str, jsdocs: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract classes and their methods from JavaScript content.

        Args:
            content: JavaScript code
            jsdocs: Dictionary of JSDoc comments

        Returns:
            List of extracted classes
        """
        classes = []

        for match in self.class_pattern.finditer(content):
            name = match.group("name")
            extends_class = match.group("extends")
            body = match.group("body")

            # Find JSDoc for this class
            class_start = match.start()
            docstring = None
            for jsdoc_end, jsdoc_data in jsdocs.items():
                if jsdoc_end < class_start and (class_start - jsdoc_end) < 10:
                    docstring = jsdoc_data
                    break

            # Extract methods from class body
            methods = []
            for method_match in self.method_pattern.finditer(body):
                method_name = method_match.group("name")
                method_params = method_match.group("params")
                method_body = method_match.group("body")

                method = {
                    "type": "method",
                    "name": method_name,
                    "params": self._parse_parameters(method_params),
                    "body": method_body[:200]
                    + ("..." if len(method_body) > 200 else ""),
                    "class_name": name,
                    "readable_name": f"{name}.{method_name}",
                }

                methods.append(method)

            # Create class object
            class_obj = {
                "type": "class",
                "name": name,
                "lineno": content[:class_start].count("\n") + 1,
                "methods": methods,
                "readable_name": name,
            }

            if extends_class:
                class_obj["extends"] = extends_class

            if docstring:
                class_obj["docstring"] = docstring["description"]

            classes.append(class_obj)

            # Also add methods as separate items for searching
            for method in methods:
                method_copy = method.copy()
                method_copy["lineno"] = class_obj["lineno"] + body[
                    : body.find(method["name"])
                ].count("\n")
                classes.append(method_copy)

        return classes

    def _extract_react_components(
        self, content: str, jsdocs: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract React components from JSX/TSX content.

        Args:
            content: JavaScript/JSX code
            jsdocs: Dictionary of JSDoc comments

        Returns:
            List of extracted React components
        """
        components = []

        for match in self.jsx_component_pattern.finditer(content):
            name = match.group("name")
            params_str = match.group("params")
            body = match.group("body")

            # Find JSDoc for this component
            comp_start = match.start()
            docstring = None
            for jsdoc_end, jsdoc_data in jsdocs.items():
                if jsdoc_end < comp_start and (comp_start - jsdoc_end) < 10:
                    docstring = jsdoc_data
                    break

            # Parse props from parameters
            props = self._parse_parameters(params_str)

            component = {
                "type": "component",
                "name": name,
                "props": props,
                "body": body[:200] + ("..." if len(body) > 200 else ""),
                "lineno": content[:comp_start].count("\n") + 1,
                "readable_name": name,
                "is_react_component": True,
            }

            if docstring:
                component["docstring"] = docstring["description"]
                if docstring["params"]:
                    component["prop_docs"] = docstring["params"]

            # Try to extract JSX structure
            jsx_elements = self._extract_jsx_elements(body)
            if jsx_elements:
                component["jsx_elements"] = jsx_elements

            components.append(component)

        return components

    def _extract_jsx_elements(self, content: str) -> List[str]:
        """
        Extract JSX element names from component body.

        Args:
            content: Component body

        Returns:
            List of JSX element names
        """
        element_pattern = re.compile(r"<([A-Z][a-zA-Z0-9_$]*)(?:\s|/|>)")
        elements = set()

        for match in element_pattern.finditer(content):
            element_name = match.group(1)
            if element_name and not element_name.startswith(("//", "/*")):
                elements.add(element_name)

        return list(elements)

    def _parse_parameters(self, params_str: str) -> List[Dict[str, Any]]:
        """
        Parse function parameters.

        Args:
            params_str: Parameter string from function definition

        Returns:
            List of parameter information
        """
        if not params_str:
            return []

        # Remove parentheses and split by comma
        params_str = params_str.strip("()")
        if not params_str:
            return []

        params = []
        # Handle destructuring and complex patterns
        param_pattern = re.compile(r"(?:{[^}]*}|\[[^\]]*]|[^,]+)(?:,|$)")

        for param_match in param_pattern.finditer(params_str):
            param_text = param_match.group(0).strip().rstrip(",")

            # Skip empty params
            if not param_text:
                continue

            # Handle default values
            default_value = None
            if "=" in param_text:
                param_name, default_value = param_text.split("=", 1)
                param_name = param_name.strip()
                default_value = default_value.strip()
            else:
                param_name = param_text

            # Handle type annotations (TypeScript)
            param_type = None
            if (
                ":" in param_name
                and not param_name.startswith("{")
                and not param_name.startswith("[")
            ):
                param_name, param_type = param_name.split(":", 1)
                param_name = param_name.strip()
                param_type = param_type.strip()

            # Handle rest parameters
            is_rest = False
            if param_name.startswith("..."):
                param_name = param_name[3:]
                is_rest = True

            param_info = {
                "name": param_name,
            }

            if default_value:
                param_info["default_value"] = default_value

            if param_type:
                param_info["type"] = param_type

            if is_rest:
                param_info["is_rest"] = True

            params.append(param_info)

        return params

    def _make_readable_name(self, name: str) -> str:
        """
        Convert a camelCase or snake_case name to a readable name.

        Args:
            name: Function or class name

        Returns:
            Human-readable name
        """
        # Handle camelCase
        name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)

        # Handle snake_case
        name = name.replace("_", " ")

        # Title case
        return name.lower()
