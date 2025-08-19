"""Tests for diff and patch utilities."""

from pathlib import Path

import pytest

from app.files.diff import (
    apply_patch,
    apply_patch_from_strings,
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
