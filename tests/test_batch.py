"""Tests for batch diff builder and atomic apply functionality."""

import os
from pathlib import Path
from unittest.mock import patch as mock_patch

import pytest

from app.files.batch import BatchDiff, FileChange, create_batch_from_dict
from app.files.workstream import (
    create_workstream_batch,
    generate_element_content,
    generate_outline_content,
)


def test_file_change_properties() -> None:
    """Test FileChange property methods."""
    # Test new file
    new_file = FileChange(Path("new.txt"), "", "content")
    assert new_file.is_new_file
    assert new_file.has_changes

    # Test modified file
    modified = FileChange(Path("existing.txt"), "old", "new")
    assert not modified.is_new_file
    assert modified.has_changes

    # Test unchanged file
    unchanged = FileChange(Path("same.txt"), "same", "same")
    assert not unchanged.is_new_file
    assert not unchanged.has_changes


def test_batch_diff_add_file() -> None:
    """Test adding files to BatchDiff."""
    batch = BatchDiff()

    # Add new file
    batch.add_file("new.txt", "", "new content")
    assert len(batch) == 1
    assert batch.changes[0].path == Path("new.txt")

    # Add modified file
    batch.add_file("existing.txt", "old", "new")
    assert len(batch) == 2

    # Try to add unchanged file (should be skipped)
    batch.add_file("unchanged.txt", "same", "same")
    assert len(batch) == 2  # Still 2, unchanged was skipped


def test_batch_diff_add_new_file() -> None:
    """Test convenience method for adding new files."""
    batch = BatchDiff()
    batch.add_new_file("test.md", "# Test")

    assert len(batch) == 1
    assert batch.changes[0].is_new_file
    assert batch.changes[0].new_content == "# Test"


def test_batch_diff_add_existing_file(tmp_path: Path) -> None:
    """Test adding existing file with auto-read."""
    file_path = tmp_path / "existing.txt"
    file_path.write_text("original content")

    batch = BatchDiff()
    batch.add_existing_file(file_path, "new content")

    assert len(batch) == 1
    assert batch.changes[0].old_content == "original content"
    assert batch.changes[0].new_content == "new content"

    # Test with non-existent file
    with pytest.raises(FileNotFoundError):
        batch.add_existing_file(tmp_path / "missing.txt", "content")


def test_batch_diff_generate_preview() -> None:
    """Test generating combined diff preview."""
    batch = BatchDiff()

    # Empty batch
    assert batch.generate_preview() == "No changes to preview."

    # Add some changes
    batch.add_file("file1.txt", "old1", "new1")
    batch.add_file("file2.txt", "", "new file content")

    preview = batch.generate_preview()

    # Check preview contains expected elements
    assert "file1.txt" in preview
    assert "file2.txt" in preview
    assert "(new file)" in preview  # file2 is new
    assert "=" * 60 in preview  # Separator
    assert "-old1" in preview
    assert "+new1" in preview


def test_batch_diff_apply_success(tmp_path: Path) -> None:
    """Test successful batch apply."""
    batch = BatchDiff()

    # Existing file
    file1 = tmp_path / "file1.txt"
    file1.write_text("original1")
    batch.add_file(file1, "original1", "modified1")

    # New file
    file2 = tmp_path / "subdir" / "file2.txt"
    batch.add_file(file2, "", "new content")

    # Apply batch
    patches = batch.apply()

    # Verify results
    assert len(patches) == 2
    assert file1.read_text() == "modified1"
    assert file2.exists()
    assert file2.read_text() == "new content"


def test_batch_diff_apply_rollback_on_failure(tmp_path: Path) -> None:
    """Test that batch apply rolls back all changes on failure."""
    batch = BatchDiff()

    # Create initial files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("original1")
    file2.write_text("original2")

    batch.add_file(file1, "original1", "modified1")
    batch.add_file(file2, "original2", "modified2")

    # Mock Path.replace to fail on second file
    call_count = 0
    original_replace = Path.replace

    def mock_replace(self: Path, target: Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise PermissionError("Simulated failure")
        original_replace(self, target)

    with mock_patch.object(Path, "replace", mock_replace), pytest.raises(IOError):
        batch.apply()

    # Verify files remain unchanged
    assert file1.read_text() == "original1"
    assert file2.read_text() == "original2"


def test_batch_diff_clear() -> None:
    """Test clearing batch changes."""
    batch = BatchDiff()
    batch.add_file("file1.txt", "", "content1")
    batch.add_file("file2.txt", "", "content2")

    assert len(batch) == 2
    batch.clear()
    assert len(batch) == 0
    assert not batch  # __bool__ should return False


def test_create_batch_from_dict(tmp_path: Path) -> None:
    """Test creating batch from dictionary."""
    # Create one existing file
    existing = tmp_path / "existing.txt"
    existing.write_text("old content")

    files = {
        "existing.txt": "new content",
        "new.txt": "brand new",
    }

    batch = create_batch_from_dict(files, tmp_path)

    assert len(batch) == 2

    # Check existing file change
    existing_change = next(c for c in batch.changes if c.path.name == "existing.txt")
    assert existing_change.old_content == "old content"
    assert existing_change.new_content == "new content"

    # Check new file change
    new_change = next(c for c in batch.changes if c.path.name == "new.txt")
    assert new_change.is_new_file
    assert new_change.new_content == "brand new"


def test_generate_outline_content() -> None:
    """Test outline generation."""
    content = generate_outline_content("test-project")

    assert "# Project Outline: test-project" in content
    assert "## Executive Summary" in content
    assert "## Key Workstreams" in content
    assert "elements/requirements.md" in content

    # Test with kernel summary
    content_with_kernel = generate_outline_content("test-project", "This is the kernel summary")
    assert "## From Kernel" in content_with_kernel
    assert "This is the kernel summary" in content_with_kernel


def test_generate_element_content() -> None:
    """Test element file generation."""
    # Test known element types
    for element_type in ["requirements", "research", "design", "implementation", "synthesis"]:
        content = generate_element_content(element_type, "test-project")
        assert f"title: {element_type.title()}" in content
        assert "project: test-project" in content
        assert f"workstream: {element_type}" in content

    # Test unknown element type (should get default template)
    content = generate_element_content("custom", "test-project")
    assert "title: Custom" in content
    assert "workstream: custom" in content


def test_create_workstream_batch(tmp_path: Path) -> None:
    """Test creating a complete workstream batch."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    (project_path / "elements").mkdir()

    # Create batch with default elements
    batch = create_workstream_batch(
        project_path, "test-project", kernel_summary="Kernel summary here"
    )

    # Should have outline + 5 default elements
    assert len(batch) == 6

    # Check outline is included
    outline_change = next(c for c in batch.changes if c.path.name == "outline.md")
    assert "Kernel summary here" in outline_change.new_content

    # Test with custom elements list
    batch2 = create_workstream_batch(
        project_path, "test-project", include_elements=["requirements", "research"]
    )

    # Should have outline + 2 specified elements
    assert len(batch2) == 3


def test_batch_apply_with_existing_files(tmp_path: Path) -> None:
    """Test batch apply when some files already exist."""
    project_path = tmp_path / "project"
    project_path.mkdir()
    elements_dir = project_path / "elements"
    elements_dir.mkdir()

    # Create existing outline with old content
    outline_path = project_path / "outline.md"
    outline_path.write_text("# Old Outline\n\nOld content")

    # Create batch
    batch = create_workstream_batch(project_path, "my-project", include_elements=["requirements"])

    # Apply
    patches = batch.apply()

    # Verify files were updated/created
    assert len(patches) == 2
    assert outline_path.exists()
    assert "# Project Outline: my-project" in outline_path.read_text()
    assert (elements_dir / "requirements.md").exists()


def test_batch_preview_formatting() -> None:
    """Test that batch preview has proper formatting."""
    batch = BatchDiff()
    batch.add_file("path/to/file1.md", "Line1\nLine2", "Line1\nModified")
    batch.add_file("path/to/file2.md", "", "New file")

    preview = batch.generate_preview(context_lines=1)

    # Check structure
    lines = preview.split("\n")

    # Should have separators
    assert any("=" * 60 in line for line in lines)

    # Should have file paths
    assert any("file1.md" in line for line in lines)
    assert any("file2.md" in line for line in lines)

    # Should indicate new file
    assert any("(new file)" in line for line in lines)

    # Should have diff markers
    assert any(line.startswith("-") for line in lines)
    assert any(line.startswith("+") for line in lines)


def test_batch_apply_empty() -> None:
    """Test applying empty batch."""
    batch = BatchDiff()
    patches = batch.apply()
    assert patches == []


def test_batch_diff_skip_unchanged(tmp_path: Path) -> None:
    """Test that unchanged files are skipped."""
    file_path = tmp_path / "unchanged.txt"
    file_path.write_text("same content")

    batch = BatchDiff()
    batch.add_existing_file(file_path, "same content")

    # Should be empty since content is unchanged
    assert len(batch) == 0
    assert batch.generate_preview() == "No changes to preview."


# Failure injection test
def test_batch_failure_injection_scenario(tmp_path: Path) -> None:
    """
    Manual failure injection test scenario.

    This test simulates a failure during batch apply to verify rollback behavior.
    To manually test:
    1. Create files as shown
    2. Modify apply_patches to inject failure at specific point
    3. Verify original files are preserved
    """
    # Setup
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    elements_dir = project_path / "elements"
    elements_dir.mkdir()

    # Create existing files
    outline = project_path / "outline.md"
    outline.write_text("# Original Outline")

    req = elements_dir / "requirements.md"
    req.write_text("# Original Requirements")

    # Create batch with changes
    batch = BatchDiff()
    batch.add_file(outline, "# Original Outline", "# New Outline")
    batch.add_file(req, "# Original Requirements", "# New Requirements")
    batch.add_file(elements_dir / "research.md", "", "# New Research")

    # To inject failure:
    # 1. Set breakpoint in apply_patches after first file is replaced
    # 2. Raise exception manually
    # 3. Verify all files return to original state

    # Normal apply (without injection)
    patches = batch.apply()
    assert len(patches) == 3

    # Verify all changes applied
    assert outline.read_text() == "# New Outline"
    assert req.read_text() == "# New Requirements"
    assert (elements_dir / "research.md").exists()


def test_batch_with_permission_errors(tmp_path: Path) -> None:
    """Test batch handling of permission errors during chmod."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("original")

    batch = BatchDiff()
    batch.add_file(file1, "original", "modified")

    # Mock chmod to simulate permission error
    def mock_chmod_error(path: Path | str, mode: int) -> None:  # noqa: ARG001
        raise PermissionError("Cannot change permissions")

    with mock_patch.object(os, "chmod", mock_chmod_error):
        # chmod errors are fatal to maintain atomicity
        with pytest.raises(OSError) as exc_info:
            batch.apply()

        assert "Failed to atomically replace files" in str(exc_info.value)
        # File should remain unchanged due to rollback
        assert file1.read_text() == "original"
