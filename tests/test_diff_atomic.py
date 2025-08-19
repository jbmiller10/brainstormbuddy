"""Tests for atomic diff operations with fsync guarantees."""

import os
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch as mock_patch

import pytest

from app.files.diff import apply_patch, apply_patches, compute_patch


def test_apply_patch_uses_atomic_write_text(tmp_path: Path) -> None:
    """Test that apply_patch delegates to atomic_write_text."""
    file_path = tmp_path / "test.txt"
    content = "Test content"
    patch = compute_patch("", content)

    # Apply patch to create new file
    apply_patch(file_path, patch)

    # Verify file was created with correct content
    assert file_path.exists()
    assert file_path.read_text() == content


def test_apply_patches_calls_fsync_on_temp_files(tmp_path: Path) -> None:
    """Test that apply_patches calls flush and fsync on temporary files."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    # Track fsync calls
    fsync_calls = []
    original_fsync = os.fsync

    def mock_fsync(fd: int) -> None:
        fsync_calls.append(fd)
        original_fsync(fd)

    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "", "Content 1"),
        (file2, "", "Content 2"),
    ]

    with mock_patch("os.fsync", side_effect=mock_fsync):
        apply_patches(patches_list)

    # Should have called fsync for each temp file plus directory fsyncs
    # At minimum, we should have 2 temp file fsyncs
    temp_file_fsyncs = [c for c in fsync_calls if c > 0]  # File descriptors are positive
    assert len(temp_file_fsyncs) >= 2, "Should have called fsync on at least 2 temp files"

    # Verify files were created
    assert file1.read_text() == "Content 1"
    assert file2.read_text() == "Content 2"


def test_apply_patches_calls_directory_fsync(tmp_path: Path) -> None:
    """Test that apply_patches calls fsync on parent directories after successful batch."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file1 = subdir / "file1.txt"
    file2 = subdir / "file2.txt"

    # Track os.open calls for directories
    open_calls = []
    original_open = os.open

    def mock_open(path: str | Path, flags: int, *args: int) -> int:
        if flags & os.O_DIRECTORY:
            open_calls.append(str(path))
        return original_open(path, flags, *args)

    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "", "Content 1"),
        (file2, "", "Content 2"),
    ]

    with mock_patch("os.open", side_effect=mock_open):
        apply_patches(patches_list)

    # Should have opened the parent directory for fsync
    assert str(subdir) in open_calls, f"Should have opened {subdir} for directory fsync"

    # Verify files were created
    assert file1.read_text() == "Content 1"
    assert file2.read_text() == "Content 2"


def test_apply_patches_rollback_on_failure_restores_originals(tmp_path: Path) -> None:
    """Test that apply_patches restores original files on failure during replacement."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    # Create initial files
    file1.write_text("Original 1")
    file2.write_text("Original 2")

    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "Original 1", "Modified 1"),
        (file2, "Original 2", "Modified 2"),
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
        with pytest.raises(OSError) as exc_info:
            apply_patches(patches_list)

        assert "Failed to atomically replace files" in str(exc_info.value)

    # Verify original files are restored
    assert file1.read_text() == "Original 1"
    assert file2.read_text() == "Original 2"

    # Verify no temp or backup files remain
    temp_files = list(tmp_path.glob("*.tmp"))
    backup_files = list(tmp_path.glob("*.backup"))
    assert len(temp_files) == 0
    assert len(backup_files) == 0


def test_apply_patches_rollback_removes_new_files(tmp_path: Path) -> None:
    """Test that rollback removes files that didn't exist before the batch operation."""
    file1 = tmp_path / "existing.txt"
    file2 = tmp_path / "new_file.txt"

    # Only create file1
    file1.write_text("Existing content")

    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "Existing content", "Modified content"),
        (file2, "", "New file content"),  # This file doesn't exist yet
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
        with pytest.raises(OSError) as exc_info:
            apply_patches(patches_list)

        assert "Failed to atomically replace files" in str(exc_info.value)

    # Verify file1 is restored to original content
    assert file1.read_text() == "Existing content"

    # Verify file2 does not exist (was removed during rollback)
    assert not file2.exists()

    # Verify no temp or backup files remain
    temp_files = list(tmp_path.glob("*.tmp"))
    backup_files = list(tmp_path.glob("*.backup"))
    assert len(temp_files) == 0
    assert len(backup_files) == 0


def test_apply_patches_skips_unchanged_files(tmp_path: Path) -> None:
    """Test that apply_patches skips files with no changes."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file3 = tmp_path / "file3.txt"

    # Create initial files
    file1.write_text("Content 1")
    file2.write_text("Content 2")
    file3.write_text("Content 3")

    # Track which files are actually replaced
    replaced_files = []
    original_replace = Path.replace

    def mock_replace(self: Path, target: Path) -> None:
        replaced_files.append(target.name)
        original_replace(self, target)

    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "Content 1", "Modified 1"),  # Changed
        (file2, "Content 2", "Content 2"),  # Unchanged
        (file3, "Content 3", "Modified 3"),  # Changed
    ]

    with mock_patch.object(Path, "replace", mock_replace):
        result = apply_patches(patches_list)

    # Should only have 2 patches in result (unchanged file skipped)
    assert len(result) == 2

    # Should only have replaced 2 files
    assert len(replaced_files) == 2
    assert "file1.txt" in replaced_files
    assert "file3.txt" in replaced_files
    assert "file2.txt" not in replaced_files

    # Verify final content
    assert file1.read_text() == "Modified 1"
    assert file2.read_text() == "Content 2"  # Unchanged
    assert file3.read_text() == "Modified 3"


def test_apply_patches_with_fsync_mock_verification(tmp_path: Path) -> None:
    """Test comprehensive fsync behavior with detailed mock verification."""
    file1 = tmp_path / "dir1" / "file1.txt"
    file2 = tmp_path / "dir2" / "file2.txt"

    # Create parent directories
    file1.parent.mkdir(parents=True)
    file2.parent.mkdir(parents=True)

    # Create a mock to track all fsync calls with context
    fsync_mock = MagicMock(side_effect=lambda _: None)

    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "", "Content 1"),
        (file2, "", "Content 2"),
    ]

    with mock_patch("os.fsync", fsync_mock):
        apply_patches(patches_list)

    # Verify fsync was called multiple times (for temp files and directories)
    assert fsync_mock.call_count >= 2, (
        f"Expected at least 2 fsync calls, got {fsync_mock.call_count}"
    )

    # Verify files were created successfully
    assert file1.read_text() == "Content 1"
    assert file2.read_text() == "Content 2"


def test_apply_patches_content_verification_error(tmp_path: Path) -> None:
    """Test that apply_patches raises ValueError when current content doesn't match expected."""
    file1 = tmp_path / "file1.txt"

    # Create file with unexpected content
    file1.write_text("Unexpected content")

    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "Expected content", "New content"),
    ]

    with pytest.raises(ValueError) as exc_info:
        apply_patches(patches_list)

    assert "doesn't match expected old_content" in str(exc_info.value)

    # File should remain unchanged
    assert file1.read_text() == "Unexpected content"


def test_apply_patch_creates_parent_directories(tmp_path: Path) -> None:
    """Test that apply_patch creates parent directories via atomic_write_text."""
    file_path = tmp_path / "deep" / "nested" / "dir" / "file.txt"
    content = "Test content"
    patch = compute_patch("", content)

    # Apply patch - should create all parent directories
    apply_patch(file_path, patch)

    assert file_path.exists()
    assert file_path.read_text() == content


def test_apply_patches_preserves_file_mode(tmp_path: Path) -> None:
    """Test that apply_patches preserves file permissions."""
    import sys

    if sys.platform == "win32":
        pytest.skip("File mode preservation test not applicable on Windows")

    file1 = tmp_path / "file1.txt"
    file1.write_text("Original")
    os.chmod(file1, 0o644)

    initial_mode = os.stat(file1).st_mode & 0o777

    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "Original", "Modified"),
    ]

    apply_patches(patches_list)

    # Verify content changed
    assert file1.read_text() == "Modified"

    # Verify mode preserved
    final_mode = os.stat(file1).st_mode & 0o777
    assert final_mode == initial_mode
