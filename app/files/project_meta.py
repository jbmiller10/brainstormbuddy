"""Project metadata operations with YAML handling."""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from app.core.interfaces import Stage
from app.files.atomic import atomic_write_text
from app.files.slug import slugify


class ProjectMeta:
    """Implementation of ProjectMetaProtocol for project metadata operations."""

    @staticmethod
    def read_project_yaml(slug: str) -> dict[str, Any] | None:
        """
        Read project.yaml for given slug.

        Args:
            slug: Project slug identifier

        Returns:
            Parsed YAML data or None if invalid/missing
        """
        project_path = Path("projects") / slug / "project.yaml"
        if not project_path.exists():
            return None

        try:
            with open(project_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Handle legacy projects that only have "name" field
            if data and "name" in data and "slug" not in data:
                # Migrate legacy format
                data["slug"] = slugify(data["name"])
                data["title"] = data.get("title", data["name"])
                # Write back the migrated data
                ProjectMeta.write_project_yaml(slug, data)

            return data  # type: ignore[no-any-return]
        except (yaml.YAMLError, OSError):
            return None

    @staticmethod
    def write_project_yaml(slug: str, data: dict[str, Any]) -> None:
        """
        Write project.yaml atomically.

        Args:
            slug: Project slug identifier
            data: YAML data to write
        """
        project_path = Path("projects") / slug / "project.yaml"

        # Ensure parent directory exists
        project_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure required fields are present
        if "slug" not in data:
            data["slug"] = slug
        if "title" not in data:
            data["title"] = slug
        if "created" not in data:
            data["created"] = datetime.now().isoformat()
        if "metadata" not in data:
            data["metadata"] = {
                "version": "1.0.0",
                "format": "brainstormbuddy-project",
            }

        # Convert to YAML string
        yaml_content = yaml.safe_dump(data, default_flow_style=False, sort_keys=False)

        # Write atomically
        atomic_write_text(project_path, yaml_content)

    @staticmethod
    def set_project_stage(slug: str, stage: Stage) -> bool:
        """
        Update project stage.

        Args:
            slug: Project slug identifier
            stage: New stage to set

        Returns:
            Success status
        """
        # Validate stage value
        valid_stages: set[Stage] = {
            "capture",
            "clarify",
            "kernel",
            "outline",
            "research",
            "synthesis",
        }
        if stage not in valid_stages:
            return False

        # Read existing data
        data = ProjectMeta.read_project_yaml(slug)
        if data is None:
            return False

        # Update stage
        data["stage"] = stage

        # Write back
        try:
            ProjectMeta.write_project_yaml(slug, data)
            return True
        except Exception:
            return False

    @staticmethod
    def validate_project_yaml(data: dict[str, Any]) -> bool:
        """
        Validate YAML has required fields.

        Required fields:
        - slug: str   (machine-safe)
        - title: str  (human-friendly)
        - created: ISO timestamp
        - stage: Stage
        - description: str
        - tags: list[str]
        - metadata: {version: "1.0.0", format: "brainstormbuddy-project"}

        Args:
            data: YAML data to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            return False

        # Check required top-level fields
        required_fields = {"slug", "title", "created", "stage", "description", "tags", "metadata"}
        if not all(field in data for field in required_fields):
            return False

        # Validate field types
        if not isinstance(data["slug"], str):
            return False
        if not isinstance(data["title"], str):
            return False
        if not isinstance(data["created"], str):
            return False
        if not isinstance(data["description"], str):
            return False
        if not isinstance(data["tags"], list):
            return False

        # Validate stage value
        valid_stages: set[Stage] = {
            "capture",
            "clarify",
            "kernel",
            "outline",
            "research",
            "synthesis",
        }
        if data["stage"] not in valid_stages:
            return False

        # Validate metadata structure
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            return False
        if metadata.get("version") != "1.0.0":
            return False
        if metadata.get("format") != "brainstormbuddy-project":
            return False

        # Validate ISO timestamp format
        try:
            datetime.fromisoformat(data["created"])
        except (ValueError, TypeError):
            return False

        return True
