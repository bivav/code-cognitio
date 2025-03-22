"""Module for extracting information from Dockerfiles."""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Set
from src.extractors.base_extractor import BaseExtractor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerfileExtractor(BaseExtractor):
    """Class for extracting information from Dockerfiles."""

    def __init__(self):
        """Initialize the Dockerfile extractor."""
        # Regex patterns for Dockerfile extraction
        self.instruction_pattern = re.compile(
            r"^\s*(?P<instruction>FROM|RUN|CMD|LABEL|MAINTAINER|EXPOSE|ENV|ADD|COPY|ENTRYPOINT|VOLUME|USER|WORKDIR|ARG|ONBUILD|HEALTHCHECK|SHELL|STOPSIGNAL)\s+(?P<value>.*?)(?:\s*#.*)?$",
            re.MULTILINE,
        )
        self.comment_pattern = re.compile(r"^\s*#\s*(?P<comment>.*)$", re.MULTILINE)
        self.env_pattern = re.compile(r"ENV\s+(?P<key>\w+)(?:\s+|=)(?P<value>[^\s]+)")
        self.label_pattern = re.compile(
            r"LABEL\s+(?P<key>\w+)(?:\s+|=)(?P<value>[^\s]+)"
        )
        self.from_pattern = re.compile(
            r"FROM\s+(?P<image>[^:\s]+)(?::(?P<tag>[^\s]+))?(?:\s+AS\s+(?P<alias>\w+))?"
        )

    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract code information from a Dockerfile.

        Args:
            file_path: Path to the Dockerfile

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
        Extract code information from Dockerfile content.

        Args:
            content: Dockerfile content as string
            file_path: Path to the file (for reference)

        Returns:
            List of extracted items
        """
        extracted_items = []

        # Extract base image info
        base_images = self._extract_base_images(content)

        # Extract instructions
        instructions = self._extract_instructions(content)

        # Extract environment variables
        env_vars = self._extract_env_vars(content)

        # Extract exposed ports
        exposed_ports = self._extract_exposed_ports(content)

        # Extract volumes
        volumes = self._extract_volumes(content)

        # Extract comments
        comments = self._extract_comments(content)

        # Create a Dockerfile item
        dockerfile_item = {
            "type": "dockerfile",
            "name": os.path.basename(file_path),
            "file_path": file_path,
            "content_type": "code",
            "language": "dockerfile",
            "base_images": base_images,
            "instructions": instructions,
            "env_vars": env_vars,
            "exposed_ports": exposed_ports,
            "volumes": volumes,
            "description": self._generate_description(
                base_images, instructions, env_vars, exposed_ports
            ),
        }

        # Add comments as documentation if available
        if comments:
            dockerfile_item["comments"] = comments

        extracted_items.append(dockerfile_item)

        # Also extract each instruction as a separate item for more granular searching
        for idx, instruction in enumerate(instructions):
            instruction_item = {
                "type": "dockerfile_instruction",
                "name": instruction["instruction"],
                "value": instruction["value"],
                "file_path": file_path,
                "language": "dockerfile",
                "lineno": instruction["lineno"],
                "content_type": "code",
                "readable_name": f"{instruction['instruction']} {instruction['value'][:30]}{'...' if len(instruction['value']) > 30 else ''}",
            }
            extracted_items.append(instruction_item)

        return extracted_items

    def get_supported_extensions(self) -> Set[str]:
        """
        Get the set of file extensions this extractor supports.

        Returns:
            Set of file extensions
        """
        return {".dockerfile", "Dockerfile", ".Dockerfile"}

    def _extract_base_images(self, content: str) -> List[Dict[str, str]]:
        """
        Extract base image information from Dockerfile.

        Args:
            content: Dockerfile content

        Returns:
            List of base image information
        """
        base_images = []

        for match in self.from_pattern.finditer(content):
            image = match.group("image")
            tag = match.group("tag") or "latest"
            alias = match.group("alias")

            base_image = {
                "image": image,
                "tag": tag,
            }

            if alias:
                base_image["alias"] = alias

            base_images.append(base_image)

        return base_images

    def _extract_instructions(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract instructions from Dockerfile.

        Args:
            content: Dockerfile content

        Returns:
            List of instructions
        """
        instructions = []

        for match in self.instruction_pattern.finditer(content):
            instruction_name = match.group("instruction")
            value = match.group("value")
            lineno = content[: match.start()].count("\n") + 1

            instructions.append(
                {
                    "instruction": instruction_name,
                    "value": value,
                    "lineno": lineno,
                }
            )

        return instructions

    def _extract_env_vars(self, content: str) -> List[Dict[str, str]]:
        """
        Extract environment variables from Dockerfile.

        Args:
            content: Dockerfile content

        Returns:
            List of environment variables
        """
        env_vars = []

        for match in self.env_pattern.finditer(content):
            key = match.group("key")
            value = match.group("value")

            env_vars.append(
                {
                    "key": key,
                    "value": value,
                }
            )

        return env_vars

    def _extract_exposed_ports(self, content: str) -> List[str]:
        """
        Extract exposed ports from Dockerfile.

        Args:
            content: Dockerfile content

        Returns:
            List of exposed ports
        """
        ports = []
        expose_pattern = re.compile(r"EXPOSE\s+(.+)(?:\s*#.*)?$", re.MULTILINE)

        for match in expose_pattern.finditer(content):
            port_str = match.group(1)
            # Split by space and/or comma
            for port in re.split(r"[,\s]+", port_str):
                if port:
                    ports.append(port)

        return ports

    def _extract_volumes(self, content: str) -> List[str]:
        """
        Extract volumes from Dockerfile.

        Args:
            content: Dockerfile content

        Returns:
            List of volumes
        """
        volumes = []
        volume_pattern = re.compile(r"VOLUME\s+(.+)(?:\s*#.*)?$", re.MULTILINE)

        for match in volume_pattern.finditer(content):
            volume_str = match.group(1)
            # Handle JSON array format and space-separated list
            if volume_str.strip().startswith("["):
                # JSON array format
                try:
                    import json

                    volume_list = json.loads(volume_str)
                    volumes.extend(volume_list)
                except:
                    # Fallback to simple parsing if JSON parsing fails
                    for volume in re.split(r"[,\s]+", volume_str.strip(" []")):
                        if volume and volume != ",":
                            volumes.append(volume)
            else:
                # Space-separated list
                for volume in re.split(r"[,\s]+", volume_str):
                    if volume:
                        volumes.append(volume)

        return volumes

    def _extract_comments(self, content: str) -> List[str]:
        """
        Extract comments from Dockerfile.

        Args:
            content: Dockerfile content

        Returns:
            List of comments
        """
        comments = []

        for match in self.comment_pattern.finditer(content):
            comment = match.group("comment").strip()
            if comment:
                comments.append(comment)

        return comments

    def _generate_description(
        self, base_images, instructions, env_vars, exposed_ports
    ) -> str:
        """
        Generate a human-readable description of the Dockerfile.

        Args:
            base_images: List of base images
            instructions: List of instructions
            env_vars: List of environment variables
            exposed_ports: List of exposed ports

        Returns:
            Description string
        """
        description_parts = []

        # Add base image info
        if base_images:
            base_image_str = (
                f"Based on {base_images[0]['image']}:{base_images[0]['tag']}"
            )
            if len(base_images) > 1:
                base_image_str += f" and {len(base_images) - 1} other base images"
            description_parts.append(base_image_str)

        # Count instruction types
        instruction_counts = {}
        for instr in instructions:
            name = instr["instruction"]
            instruction_counts[name] = instruction_counts.get(name, 0) + 1

        # Add instruction summary
        if instruction_counts:
            instr_summary = ", ".join(
                [f"{count} {name}" for name, count in instruction_counts.items()]
            )
            description_parts.append(f"Contains {instr_summary}")

        # Add env vars if present
        if env_vars:
            env_var_str = f"Sets {len(env_vars)} environment variables"
            description_parts.append(env_var_str)

        # Add exposed ports if present
        if exposed_ports:
            ports_str = f"Exposes {', '.join(exposed_ports[:3])}"
            if len(exposed_ports) > 3:
                ports_str += f" and {len(exposed_ports) - 3} more ports"
            description_parts.append(ports_str)

        return ". ".join(description_parts)
