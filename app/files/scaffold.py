"""Project scaffold utility for creating standardized project structures."""

from datetime import datetime
from pathlib import Path

import yaml


def scaffold_project(slug: str, base: Path | str = "projects") -> Path:
    """
    Create a project directory structure with seed files.

    Args:
        slug: Project identifier (will be used as directory name)
        base: Base directory for projects (default: "projects")

    Returns:
        Path to the created/existing project directory

    The function is idempotent - running it multiple times with the same
    slug will not cause errors or duplicate content.
    """
    base_path = Path(base) if isinstance(base, str) else base
    project_path = base_path / slug

    # Create directory structure
    _create_directories(project_path)

    # Create seed files
    _create_project_yaml(project_path / "project.yaml", slug)
    _create_kernel_md(project_path / "kernel.md", slug)
    _create_outline_md(project_path / "outline.md", slug)

    return project_path


def _create_directories(project_path: Path) -> None:
    """Create the required directory structure."""
    directories = [
        project_path,
        project_path / "elements",
        project_path / "research",
        project_path / "exports",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def _create_project_yaml(file_path: Path, slug: str) -> None:
    """Create project.yaml with basic metadata if it doesn't exist."""
    if file_path.exists():
        return

    project_data = {
        "name": slug,
        "created": datetime.now().isoformat(),
        "stage": "capture",
        "description": f"Brainstorming project: {slug}",
        "tags": [],
        "metadata": {
            "version": "1.0.0",
            "format": "brainstormbuddy-project",
        },
    }

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(project_data, f, default_flow_style=False, sort_keys=False)


def _create_kernel_md(file_path: Path, slug: str) -> None:
    """Create kernel.md with minimal structure if it doesn't exist."""
    if file_path.exists():
        return

    content = f"""---
title: Kernel
project: {slug}
created: {datetime.now().isoformat()}
stage: kernel
---

# Kernel

## Core Concept

*The essential idea or problem to explore.*

## Key Questions

*What are we trying to answer or solve?*

## Success Criteria

*How will we know when we've achieved our goal?*
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def _create_outline_md(file_path: Path, slug: str) -> None:
    """Create outline.md with minimal structure if it doesn't exist."""
    if file_path.exists():
        return

    content = f"""---
title: Outline
project: {slug}
created: {datetime.now().isoformat()}
stage: outline
---

# Outline

## Executive Summary

*High-level overview of the project.*

## Main Sections

### Section 1

*Key points and structure.*

### Section 2

*Key points and structure.*

### Section 3

*Key points and structure.*

## Next Steps

*What needs to be done next?*
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def ensure_project_exists(slug: str, base: Path | str = "projects") -> Path:
    """
    Ensure a project exists, creating it if necessary.

    This is an alias for scaffold_project for clarity in different contexts.
    """
    return scaffold_project(slug, base)
