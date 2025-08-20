"""Tests for ProjectMeta YAML operations."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from app.core.interfaces import ProjectMetaProtocol, Stage
from app.files.project_meta import ProjectMeta


@pytest.fixture
def temp_projects_dir(tmp_path: Path) -> Path:
    """Create a temporary projects directory."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    return projects_dir


@pytest.fixture
def sample_project_data() -> dict:
    """Create sample project data with all required fields."""
    return {
        "slug": "test-project",
        "title": "Test Project",
        "created": datetime.now().isoformat(),
        "stage": "capture",
        "description": "A test project",
        "tags": ["test", "sample"],
        "metadata": {
            "version": "1.0.0",
            "format": "brainstormbuddy-project",
        },
    }


def test_protocol_implementation() -> None:
    """Test that ProjectMeta implements ProjectMetaProtocol."""
    # This should type check correctly
    project_meta: type[ProjectMetaProtocol] = ProjectMeta
    assert hasattr(project_meta, "read_project_yaml")
    assert hasattr(project_meta, "write_project_yaml")
    assert hasattr(project_meta, "set_project_stage")
    assert hasattr(project_meta, "validate_project_yaml")


def test_validate_project_yaml_valid(sample_project_data: dict) -> None:
    """Test validation with valid data."""
    assert ProjectMeta.validate_project_yaml(sample_project_data) is True


def test_validate_project_yaml_missing_fields() -> None:
    """Test validation with missing required fields."""
    incomplete_data = {
        "slug": "test",
        "title": "Test",
        # Missing other required fields
    }
    assert ProjectMeta.validate_project_yaml(incomplete_data) is False


def test_validate_project_yaml_invalid_stage() -> None:
    """Test validation with invalid stage."""
    data = {
        "slug": "test",
        "title": "Test",
        "created": datetime.now().isoformat(),
        "stage": "invalid_stage",  # Invalid
        "description": "Test",
        "tags": [],
        "metadata": {
            "version": "1.0.0",
            "format": "brainstormbuddy-project",
        },
    }
    assert ProjectMeta.validate_project_yaml(data) is False


def test_validate_project_yaml_invalid_metadata() -> None:
    """Test validation with invalid metadata."""
    data = {
        "slug": "test",
        "title": "Test",
        "created": datetime.now().isoformat(),
        "stage": "capture",
        "description": "Test",
        "tags": [],
        "metadata": {
            "version": "2.0.0",  # Wrong version
            "format": "brainstormbuddy-project",
        },
    }
    assert ProjectMeta.validate_project_yaml(data) is False


def test_validate_project_yaml_invalid_timestamp() -> None:
    """Test validation with invalid ISO timestamp."""
    data = {
        "slug": "test",
        "title": "Test",
        "created": "not-a-timestamp",  # Invalid
        "stage": "capture",
        "description": "Test",
        "tags": [],
        "metadata": {
            "version": "1.0.0",
            "format": "brainstormbuddy-project",
        },
    }
    assert ProjectMeta.validate_project_yaml(data) is False


def test_read_project_yaml_missing_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test reading non-existent project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.chdir(tmpdir)
        Path("projects").mkdir()
        result = ProjectMeta.read_project_yaml("nonexistent")
        assert result is None


def test_read_project_yaml_valid(
    monkeypatch: pytest.MonkeyPatch, sample_project_data: dict
) -> None:
    """Test reading valid project YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.chdir(tmpdir)
        project_dir = Path("projects/test-project")
        project_dir.mkdir(parents=True)

        # Write sample data
        yaml_path = project_dir / "project.yaml"
        with open(yaml_path, "w") as f:
            yaml.safe_dump(sample_project_data, f)

        # Read it back
        result = ProjectMeta.read_project_yaml("test-project")
        assert result is not None
        assert result["slug"] == "test-project"
        assert result["title"] == "Test Project"
        assert result["stage"] == "capture"


def test_read_project_yaml_legacy_migration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test migration of legacy project with only 'name' field."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.chdir(tmpdir)
        project_dir = Path("projects/legacy-project")
        project_dir.mkdir(parents=True)

        # Write legacy format
        legacy_data = {
            "name": "Legacy Project Name",
            "created": datetime.now().isoformat(),
            "stage": "kernel",
            "description": "Old project",
            "tags": [],
            "metadata": {
                "version": "1.0.0",
                "format": "brainstormbuddy-project",
            },
        }
        yaml_path = project_dir / "project.yaml"
        with open(yaml_path, "w") as f:
            yaml.safe_dump(legacy_data, f)

        # Read and check migration
        result = ProjectMeta.read_project_yaml("legacy-project")
        assert result is not None
        assert result["slug"] == "legacy-project-name"  # Slugified
        assert result["title"] == "Legacy Project Name"  # Original name as title
        assert result["name"] == "Legacy Project Name"  # Original preserved
        assert result["stage"] == "kernel"

        # Verify migration was written back
        with open(yaml_path) as f:
            saved_data = yaml.safe_load(f)
        assert saved_data["slug"] == "legacy-project-name"
        assert saved_data["title"] == "Legacy Project Name"


def test_write_project_yaml_creates_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that write creates parent directory if needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.chdir(tmpdir)

        data = {
            "slug": "new-project",
            "title": "New Project",
            "stage": "capture",
            "description": "Test",
            "tags": [],
        }

        # Directory doesn't exist yet
        assert not Path("projects/new-project").exists()

        ProjectMeta.write_project_yaml("new-project", data)

        # Directory and file should now exist
        yaml_path = Path("projects/new-project/project.yaml")
        assert yaml_path.exists()

        # Verify content
        with open(yaml_path) as f:
            saved_data = yaml.safe_load(f)
        assert saved_data["slug"] == "new-project"
        assert saved_data["title"] == "New Project"
        assert "created" in saved_data  # Auto-added
        assert "metadata" in saved_data  # Auto-added


def test_write_project_yaml_atomic(
    monkeypatch: pytest.MonkeyPatch, sample_project_data: dict
) -> None:
    """Test that writes are atomic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.chdir(tmpdir)
        project_dir = Path("projects/test-project")
        project_dir.mkdir(parents=True)

        # Write initial data
        ProjectMeta.write_project_yaml("test-project", sample_project_data)

        # Modify and write again
        sample_project_data["description"] = "Updated description"
        ProjectMeta.write_project_yaml("test-project", sample_project_data)

        # Read back
        with open(project_dir / "project.yaml") as f:
            saved_data = yaml.safe_load(f)
        assert saved_data["description"] == "Updated description"


def test_set_project_stage_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setting project stage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.chdir(tmpdir)
        project_dir = Path("projects/test-project")
        project_dir.mkdir(parents=True)

        # Write initial data
        data = {
            "slug": "test-project",
            "title": "Test",
            "stage": "capture",
            "created": datetime.now().isoformat(),
            "description": "Test",
            "tags": [],
            "metadata": {"version": "1.0.0", "format": "brainstormbuddy-project"},
        }
        with open(project_dir / "project.yaml", "w") as f:
            yaml.safe_dump(data, f)

        # Update stage
        result = ProjectMeta.set_project_stage("test-project", "kernel")
        assert result is True

        # Verify update
        with open(project_dir / "project.yaml") as f:
            saved_data = yaml.safe_load(f)
        assert saved_data["stage"] == "kernel"


def test_set_project_stage_invalid_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setting invalid project stage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.chdir(tmpdir)
        project_dir = Path("projects/test-project")
        project_dir.mkdir(parents=True)

        # Write initial data
        data = {
            "slug": "test-project",
            "title": "Test",
            "stage": "capture",
            "created": datetime.now().isoformat(),
            "description": "Test",
            "tags": [],
            "metadata": {"version": "1.0.0", "format": "brainstormbuddy-project"},
        }
        with open(project_dir / "project.yaml", "w") as f:
            yaml.safe_dump(data, f)

        # Try invalid stage
        result = ProjectMeta.set_project_stage("test-project", "invalid")  # type: ignore
        assert result is False

        # Verify stage unchanged
        with open(project_dir / "project.yaml") as f:
            saved_data = yaml.safe_load(f)
        assert saved_data["stage"] == "capture"


def test_set_project_stage_missing_project(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setting stage for non-existent project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.chdir(tmpdir)
        Path("projects").mkdir()

        result = ProjectMeta.set_project_stage("nonexistent", "kernel")
        assert result is False


def test_all_stage_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test all valid stage values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.chdir(tmpdir)
        project_dir = Path("projects/test-project")
        project_dir.mkdir(parents=True)

        # Write initial data
        data = {
            "slug": "test-project",
            "title": "Test",
            "stage": "capture",
            "created": datetime.now().isoformat(),
            "description": "Test",
            "tags": [],
            "metadata": {"version": "1.0.0", "format": "brainstormbuddy-project"},
        }
        with open(project_dir / "project.yaml", "w") as f:
            yaml.safe_dump(data, f)

        # Test all valid stages
        valid_stages: list[Stage] = [
            "capture",
            "clarify",
            "kernel",
            "outline",
            "research",
            "synthesis",
        ]

        for stage in valid_stages:
            result = ProjectMeta.set_project_stage("test-project", stage)
            assert result is True

            # Verify
            with open(project_dir / "project.yaml") as f:
                saved_data = yaml.safe_load(f)
            assert saved_data["stage"] == stage
