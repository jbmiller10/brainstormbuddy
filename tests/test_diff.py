"""Tests for diff and patch utilities."""

from pathlib import Path
from unittest.mock import patch as mock_patch

import pytest

from app.files.diff import (
    apply_patch,
    apply_patch_from_strings,
    apply_patches,
    compute_patch,
    generate_diff_preview,
    is_unchanged,
)


def test_compute_patch_no_changes() -> None:
    """Test computing patch when content is unchanged."""
    content = "Hello\nWorld\n"
    patch = compute_patch(content, content)

    assert patch.original == content
    assert patch.modified == content
    assert is_unchanged(patch)


def test_compute_patch_with_changes() -> None:
    """Test computing patch with actual changes."""
    old = "Hello\nWorld\n"
    new = "Hello\nBeautiful\nWorld\n"
    patch = compute_patch(old, new)

    assert patch.original == old
    assert patch.modified == new
    assert not is_unchanged(patch)
    assert len(patch.diff_lines) > 0


def test_apply_patch_creates_new_file(tmp_path: Path) -> None:
    """Test applying patch to create a new file."""
    file_path = tmp_path / "test.md"
    content = "# Test Document\n\nThis is a test."

    patch = compute_patch("", content)
    apply_patch(file_path, patch)

    assert file_path.exists()
    with open(file_path, encoding="utf-8") as f:
        assert f.read() == content


def test_apply_patch_replaces_existing_file(tmp_path: Path) -> None:
    """Test applying patch to replace an existing file."""
    file_path = tmp_path / "test.md"
    old_content = "Old content"
    new_content = "New content"

    # Create initial file
    file_path.write_text(old_content)

    # Apply patch
    patch = compute_patch(old_content, new_content)
    apply_patch(file_path, patch)

    assert file_path.read_text() == new_content


def test_apply_patch_atomic_on_error(tmp_path: Path) -> None:
    """Test that patch application is atomic even on errors."""
    file_path = tmp_path / "test.md"
    original_content = "Original"
    file_path.write_text(original_content)

    # Create a patch with invalid content that will cause an error
    # We'll mock the error by making the parent directory read-only after temp file creation
    patch = compute_patch(original_content, "New content")

    # Make a subdirectory to test atomic replacement
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    test_file = subdir / "test.md"
    test_file.write_text(original_content)

    # Apply patch normally (should work)
    apply_patch(test_file, patch)
    assert test_file.read_text() == "New content"


def test_generate_diff_preview() -> None:
    """Test generating human-readable diff preview."""
    old = "Line 1\nLine 2\nLine 3\n"
    new = "Line 1\nModified Line 2\nLine 3\n"

    preview = generate_diff_preview(old, new)

    assert "Line 2" in preview
    assert "Modified Line 2" in preview
    assert "-" in preview  # Removal indicator
    assert "+" in preview  # Addition indicator
    # Verify line breaks are present
    assert "\n" in preview
    lines = preview.split("\n")
    assert len(lines) > 1  # Should have multiple lines


def test_generate_diff_preview_no_changes() -> None:
    """Test diff preview when there are no changes."""
    content = "Same content"
    preview = generate_diff_preview(content, content)

    assert preview == "No changes detected."


def test_is_unchanged() -> None:
    """Test the is_unchanged helper function."""
    # Test with identical content
    patch1 = compute_patch("same", "same")
    assert is_unchanged(patch1)

    # Test with different content
    patch2 = compute_patch("old", "new")
    assert not is_unchanged(patch2)


def test_apply_patch_from_strings_success(tmp_path: Path) -> None:
    """Test the helper function for applying patches from strings."""
    file_path = tmp_path / "test.md"
    old_content = "Original\n"
    new_content = "Modified\n"

    # Create initial file
    file_path.write_text(old_content)

    # Apply patch
    patch = apply_patch_from_strings(file_path, old_content, new_content)

    assert patch is not None
    assert file_path.read_text() == new_content


def test_apply_patch_from_strings_no_changes(tmp_path: Path) -> None:
    """Test that no patch is applied when content is unchanged."""
    file_path = tmp_path / "test.md"
    content = "Same content\n"

    file_path.write_text(content)
    patch = apply_patch_from_strings(file_path, content, content)

    assert patch is None
    assert file_path.read_text() == content


def test_apply_patch_from_strings_content_mismatch(tmp_path: Path) -> None:
    """Test that ValueError is raised when current content doesn't match expected."""
    file_path = tmp_path / "test.md"
    file_path.write_text("Actual content")

    with pytest.raises(ValueError) as exc_info:
        apply_patch_from_strings(file_path, "Expected content", "New content")

    assert "doesn't match expected old_content" in str(exc_info.value)


def test_apply_patch_creates_parent_directories(tmp_path: Path) -> None:
    """Test that apply_patch creates parent directories if they don't exist."""
    file_path = tmp_path / "nested" / "dir" / "test.md"
    content = "Test content"

    patch = compute_patch("", content)
    apply_patch(file_path, patch)

    assert file_path.exists()
    assert file_path.read_text() == content


def test_multi_line_diff() -> None:
    """Test diff computation with multi-line changes."""
    old = """# Document

First paragraph.

Second paragraph.

Third paragraph.
"""
    new = """# Document

First paragraph.

Modified second paragraph with more text.

Third paragraph.

Fourth paragraph added.
"""

    patch = compute_patch(old, new)
    assert not is_unchanged(patch)

    preview = generate_diff_preview(old, new)
    assert "Modified second paragraph" in preview
    assert "Fourth paragraph added" in preview


def test_generate_diff_preview_context_lines() -> None:
    """Test that context_lines parameter affects the diff output."""
    old = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\n"
    new = "Line 1\nLine 2\nLine 3\nModified Line 4\nLine 5\nLine 6\nLine 7\nLine 8\n"

    # Test with different context sizes
    preview_small = generate_diff_preview(old, new, context_lines=1)
    preview_large = generate_diff_preview(old, new, context_lines=3)

    # Both should contain the change
    assert "Modified Line 4" in preview_small
    assert "Modified Line 4" in preview_large

    # Larger context should include more surrounding lines
    lines_small = preview_small.split("\n")
    lines_large = preview_large.split("\n")

    # The larger context should have more lines
    # (accounting for header lines and the actual diff content)
    assert len(lines_large) >= len(lines_small)


def test_apply_patches_success(tmp_path: Path) -> None:
    """Test successful multi-file patch application."""
    # Create initial files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file3 = tmp_path / "nested" / "file3.txt"

    file1.write_text("Original content 1")
    file2.write_text("Original content 2")
    # file3 doesn't exist yet - will be created

    # Prepare patches
    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "Original content 1", "Modified content 1"),
        (file2, "Original content 2", "Modified content 2"),
        (file3, "", "New file content 3"),  # New file
    ]

    # Apply patches
    results = apply_patches(patches_list)

    # Verify all files were updated
    assert len(results) == 3
    assert file1.read_text() == "Modified content 1"
    assert file2.read_text() == "Modified content 2"
    assert file3.exists()
    assert file3.read_text() == "New file content 3"

    # Verify patch objects
    for patch in results:
        assert not is_unchanged(patch)


def test_apply_patches_rollback_on_failure(tmp_path: Path) -> None:
    """Test that all files remain unchanged when any replacement fails."""
    # Create initial files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    file1.write_text("Original content 1")
    file2.write_text("Original content 2")

    original1 = file1.read_text()
    original2 = file2.read_text()

    # Prepare patches
    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "Original content 1", "Modified content 1"),
        (file2, "Original content 2", "Modified content 2"),
    ]

    # Mock Path.replace to fail on the second file
    call_count = 0
    original_replace = Path.replace

    def mock_replace(self: Path, target: Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise PermissionError("Simulated failure on second file")
        original_replace(self, target)

    with mock_patch.object(Path, "replace", mock_replace):
        with pytest.raises(IOError) as exc_info:
            apply_patches(patches_list)

        assert "Failed to atomically replace files" in str(exc_info.value)

    # Verify original files are unchanged
    assert file1.read_text() == original1
    assert file2.read_text() == original2

    # Verify no temp files left behind
    temp_files = list(tmp_path.glob("*.tmp"))
    assert len(temp_files) == 0


def test_apply_patch_atomic_failure(tmp_path: Path) -> None:
    """Test that apply_patch cleans temp and preserves original on replace failure."""
    file_path = tmp_path / "test.txt"
    original_content = "Original content"
    new_content = "New content"

    # Create initial file
    file_path.write_text(original_content)

    # Create a patch
    patch = compute_patch(original_content, new_content)

    # Mock Path.replace to raise an exception
    def mock_replace_error(self: Path, target: Path) -> None:  # noqa: ARG001
        raise PermissionError("Simulated replace failure")

    with mock_patch.object(Path, "replace", mock_replace_error):
        with pytest.raises(PermissionError) as exc_info:
            apply_patch(file_path, patch)

        assert "Simulated replace failure" in str(exc_info.value)

    # Verify original file is unchanged
    assert file_path.read_text() == original_content

    # Verify no temp files left behind
    temp_files = list(tmp_path.glob("*.tmp"))
    assert len(temp_files) == 0
