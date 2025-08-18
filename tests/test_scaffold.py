"""Tests for the project scaffold utility."""

import tempfile
from pathlib import Path

import yaml

from app.files.scaffold import ensure_project_exists, scaffold_project


class TestScaffoldProject:
    """Test suite for scaffold_project function."""

    def test_creates_directory_structure(self) -> None:
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            # Verify project directory exists
            assert project_path.exists()
            assert project_path.is_dir()
            assert project_path == base / "test-project"

            # Verify subdirectories exist
            assert (project_path / "elements").exists()
            assert (project_path / "elements").is_dir()
            assert (project_path / "research").exists()
            assert (project_path / "research").is_dir()
            assert (project_path / "exports").exists()
            assert (project_path / "exports").is_dir()

    def test_creates_seed_files(self) -> None:
        """Test that all required seed files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            # Verify files exist
            assert (project_path / "project.yaml").exists()
            assert (project_path / "kernel.md").exists()
            assert (project_path / "outline.md").exists()

            # Verify files are not empty
            assert (project_path / "project.yaml").stat().st_size > 0
            assert (project_path / "kernel.md").stat().st_size > 0
            assert (project_path / "outline.md").stat().st_size > 0

    def test_project_yaml_content(self) -> None:
        """Test that project.yaml has correct structure and content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            with open(project_path / "project.yaml", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            assert data["name"] == "test-project"
            assert "created" in data
            assert data["stage"] == "capture"
            assert "description" in data
            assert isinstance(data["tags"], list)
            assert data["metadata"]["version"] == "1.0.0"
            assert data["metadata"]["format"] == "brainstormbuddy-project"

    def test_kernel_md_content(self) -> None:
        """Test that kernel.md has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            content = (project_path / "kernel.md").read_text(encoding="utf-8")

            # Check frontmatter
            assert "---" in content
            assert "title: Kernel" in content
            assert "project: test-project" in content
            assert "stage: kernel" in content

            # Check main headers
            assert "# Kernel" in content
            assert "## Core Concept" in content
            assert "## Key Questions" in content
            assert "## Success Criteria" in content

    def test_outline_md_content(self) -> None:
        """Test that outline.md has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            content = (project_path / "outline.md").read_text(encoding="utf-8")

            # Check frontmatter
            assert "---" in content
            assert "title: Outline" in content
            assert "project: test-project" in content
            assert "stage: outline" in content

            # Check main headers
            assert "# Outline" in content
            assert "## Executive Summary" in content
            assert "## Main Sections" in content
            assert "### Section 1" in content
            assert "## Next Steps" in content

    def test_idempotency(self) -> None:
        """Test that running scaffold_project twice doesn't cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # First run
            project_path1 = scaffold_project("test-project", base)

            # Get initial file modification times
            yaml_mtime1 = (project_path1 / "project.yaml").stat().st_mtime
            kernel_mtime1 = (project_path1 / "kernel.md").stat().st_mtime
            outline_mtime1 = (project_path1 / "outline.md").stat().st_mtime

            # Second run (should not error)
            project_path2 = scaffold_project("test-project", base)

            # Paths should be the same
            assert project_path1 == project_path2

            # Files should not be modified (times should be the same)
            yaml_mtime2 = (project_path2 / "project.yaml").stat().st_mtime
            kernel_mtime2 = (project_path2 / "kernel.md").stat().st_mtime
            outline_mtime2 = (project_path2 / "outline.md").stat().st_mtime

            assert yaml_mtime1 == yaml_mtime2
            assert kernel_mtime1 == kernel_mtime2
            assert outline_mtime1 == outline_mtime2

    def test_idempotency_preserves_content(self) -> None:
        """Test that re-running doesn't overwrite existing content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # First run
            project_path = scaffold_project("test-project", base)

            # Modify a file
            kernel_path = project_path / "kernel.md"
            custom_content = "# Custom Kernel Content\n\nThis was modified."
            kernel_path.write_text(custom_content, encoding="utf-8")

            # Second run
            scaffold_project("test-project", base)

            # Content should be preserved
            assert kernel_path.read_text(encoding="utf-8") == custom_content

    def test_string_base_path(self) -> None:
        """Test that base can be provided as a string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = scaffold_project("test-project", tmpdir)

            assert project_path.exists()
            assert project_path.parent == Path(tmpdir)

    def test_path_base_path(self) -> None:
        """Test that base can be provided as a Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            assert project_path.exists()
            assert project_path.parent == base

    def test_nested_base_path(self) -> None:
        """Test creating projects in nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "nested" / "projects"
            project_path = scaffold_project("test-project", base)

            assert project_path.exists()
            assert project_path.parent == base
            assert base.exists()

    def test_ensure_project_exists_alias(self) -> None:
        """Test that ensure_project_exists works as an alias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            path1 = ensure_project_exists("test-project", base)
            path2 = scaffold_project("test-project", base)

            assert path1 == path2
            assert path1.exists()

    def test_multiple_projects(self) -> None:
        """Test creating multiple projects in the same base directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            project1 = scaffold_project("project-one", base)
            project2 = scaffold_project("project-two", base)

            assert project1.exists()
            assert project2.exists()
            assert project1 != project2
            assert project1.name == "project-one"
            assert project2.name == "project-two"

    def test_slug_with_special_characters(self) -> None:
        """Test that slugs with hyphens and underscores work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            project1 = scaffold_project("my-cool-project", base)
            project2 = scaffold_project("my_cool_project", base)

            assert project1.exists()
            assert project2.exists()
            assert project1.name == "my-cool-project"
            assert project2.name == "my_cool_project"
