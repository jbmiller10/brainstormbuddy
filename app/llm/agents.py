"""Agent specification loader and materializer for Claude Code subagents."""

import importlib.resources as resources
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.files.atomic import atomic_write_text


@dataclass(frozen=True)
class AgentSpec:
    """Specification for a Claude Code subagent."""

    name: str
    description: str
    tools: list[str]
    prompt: str


def _parse_agent_markdown(content: str, filename: str) -> AgentSpec:
    """
    Parse an agent specification from markdown with YAML frontmatter.

    Args:
        content: The markdown file content
        filename: The source filename for error messages

    Returns:
        Parsed AgentSpec

    Raises:
        ValueError: If frontmatter is invalid or required fields are missing
    """
    # Extract frontmatter using regex
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        raise ValueError(
            f"Invalid agent spec in {filename}: Missing YAML frontmatter. "
            "Expected format: ---\\n<yaml>\\n---\\n<markdown>"
        )

    frontmatter_str, body = match.groups()

    # Parse YAML frontmatter
    try:
        frontmatter: dict[str, Any] = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError as e:
        raise ValueError(
            f"Invalid YAML frontmatter in {filename}: {e}. Please check YAML syntax."
        ) from e

    # Validate required fields
    missing_fields = []
    if "name" not in frontmatter:
        missing_fields.append("name")
    if "description" not in frontmatter:
        missing_fields.append("description")

    if missing_fields:
        raise ValueError(
            f"Missing required fields in {filename}: {', '.join(missing_fields)}. "
            f"Required fields are: name (str), description (str)"
        )

    # Validate field types
    if not isinstance(frontmatter["name"], str):
        raise ValueError(
            f"Invalid field type in {filename}: 'name' must be a string, "
            f"got {type(frontmatter['name']).__name__}"
        )

    if not isinstance(frontmatter["description"], str):
        raise ValueError(
            f"Invalid field type in {filename}: 'description' must be a string, "
            f"got {type(frontmatter['description']).__name__}"
        )

    # Handle optional tools field
    tools = frontmatter.get("tools", [])
    if not isinstance(tools, list):
        raise ValueError(
            f"Invalid field type in {filename}: 'tools' must be a list, got {type(tools).__name__}"
        )

    # Ensure all tools are strings
    for i, tool in enumerate(tools):
        if not isinstance(tool, str):
            raise ValueError(
                f"Invalid tool in {filename}: tools[{i}] must be a string, "
                f"got {type(tool).__name__}"
            )

    return AgentSpec(
        name=frontmatter["name"],
        description=frontmatter["description"],
        tools=tools,
        prompt=body.strip(),
    )


def load_agent_specs(source_pkg: str = "app.llm.agentspecs") -> list[AgentSpec]:
    """
    Load agent specifications from a Python package.

    Args:
        source_pkg: Dot-separated package path containing agent spec markdown files

    Returns:
        List of loaded AgentSpec instances

    Raises:
        ValueError: If any spec file is invalid
        ModuleNotFoundError: If the source package doesn't exist
    """
    specs: list[AgentSpec] = []

    # Convert package string to module parts
    module_parts = source_pkg.split(".")

    # Try to access the package
    try:
        # For Python 3.9+, we use files() directly
        # For compatibility with 3.11+, we handle the traversable protocol
        if len(module_parts) == 1:
            pkg_files = resources.files(module_parts[0])
        else:
            # Build up the package reference step by step
            pkg_files = resources.files(module_parts[0])
            for part in module_parts[1:]:
                pkg_files = pkg_files / part
    except (ModuleNotFoundError, AttributeError) as e:
        raise ModuleNotFoundError(
            f"Cannot find package '{source_pkg}'. "
            f"Make sure it exists and is a valid Python package."
        ) from e

    # Find all .md files in the package
    md_files = []
    try:
        for item in pkg_files.iterdir():
            if item.name.endswith(".md"):
                md_files.append(item)
    except AttributeError as e:
        # Fallback for older Python versions or different resource types
        raise ValueError(
            f"Cannot iterate files in package '{source_pkg}'. "
            f"Make sure it's a directory package with __init__.py."
        ) from e

    # Sort files for consistent ordering
    md_files.sort(key=lambda f: f.name)

    # Parse each markdown file
    for file_resource in md_files:
        try:
            content = file_resource.read_text(encoding="utf-8")
            spec = _parse_agent_markdown(content, file_resource.name)
            specs.append(spec)
        except Exception as e:
            raise ValueError(f"Error loading agent spec from {file_resource.name}: {e}") from e

    return specs


def materialize_agents(target_dir: Path, source_pkg: str = "app.llm.agentspecs") -> Path:
    """
    Materialize agent specs from a package to a target directory for Claude Code.

    Args:
        target_dir: Directory where .claude/agents will be created
        source_pkg: Package path containing agent spec files

    Returns:
        Path to the created agents directory

    Raises:
        ValueError: If specs cannot be loaded or written
    """
    # Load specs from the source package
    specs = load_agent_specs(source_pkg)

    # Create target directory structure
    agents_dir = target_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Get original filenames from the package to preserve them
    module_parts = source_pkg.split(".")
    if len(module_parts) == 1:
        pkg_files = resources.files(module_parts[0])
    else:
        pkg_files = resources.files(module_parts[0])
        for part in module_parts[1:]:
            pkg_files = pkg_files / part

    # Create a mapping of spec names to original filenames
    name_to_filename: dict[str, str] = {}
    for item in pkg_files.iterdir():
        if item.name.endswith(".md"):
            content = item.read_text(encoding="utf-8")
            try:
                spec = _parse_agent_markdown(content, item.name)
                name_to_filename[spec.name] = item.name
            except ValueError:
                # Skip invalid files
                continue

    # Write each spec to the target directory
    for spec in specs:
        # Use original filename if available, otherwise use name.md
        filename = name_to_filename.get(spec.name, f"{spec.name}.md")
        target_path = agents_dir / filename

        # Reconstruct the markdown with frontmatter
        frontmatter_dict: dict[str, Any] = {
            "name": spec.name,
            "description": spec.description,
        }
        if spec.tools:
            frontmatter_dict["tools"] = spec.tools

        frontmatter_yaml = yaml.dump(frontmatter_dict, default_flow_style=False, sort_keys=False)
        content = f"---\n{frontmatter_yaml}---\n\n{spec.prompt}\n"

        # Write the file
        atomic_write_text(target_path, content)

    return agents_dir
