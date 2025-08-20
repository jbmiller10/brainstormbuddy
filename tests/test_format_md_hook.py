"""Test markdown formatting hook functionality using generated hooks."""

import importlib.util
import os
from pathlib import Path
from unittest.mock import patch

from app.permissions.hooks_lib.io import atomic_replace_text
from app.permissions.settings_writer import write_project_settings


def test_atomic_replace_text_with_fsync(tmp_path: Path) -> None:
    """Test that atomic_replace_text performs flush and fsync operations."""
    test_file = tmp_path / "test.md"
    content = "# Test Content\n\nThis is a test."

    # Track fsync calls
    fsync_calls = []
    original_fsync = os.fsync

    def mock_fsync(fd: int) -> None:
        fsync_calls.append(fd)
        original_fsync(fd)

    with patch("os.fsync", side_effect=mock_fsync):
        atomic_replace_text(test_file, content)

    # Should have called fsync at least once (for the temp file)
    assert len(fsync_calls) >= 1, "Should have called fsync on temp file"

    # Verify file was created with correct content
    assert test_file.exists()
    assert test_file.read_text() == content


def test_atomic_replace_text_preserves_file_mode(tmp_path: Path) -> None:
    """Test that atomic_replace_text preserves file permissions."""
    import sys

    if sys.platform == "win32":
        # Skip on Windows where file modes work differently
        return

    test_file = tmp_path / "test.md"
    test_file.write_text("Original content")
    os.chmod(test_file, 0o644)

    initial_mode = os.stat(test_file).st_mode & 0o777

    atomic_replace_text(test_file, "New content")

    # Verify content changed
    assert test_file.read_text() == "New content"

    # Verify mode preserved
    final_mode = os.stat(test_file).st_mode & 0o777
    assert final_mode == initial_mode


def test_atomic_replace_text_creates_parent_dirs(tmp_path: Path) -> None:
    """Test that atomic_replace_text creates parent directories if needed."""
    test_file = tmp_path / "deep" / "nested" / "dir" / "test.md"
    content = "# Nested file"

    atomic_replace_text(test_file, content)

    assert test_file.exists()
    assert test_file.read_text() == content


def test_atomic_replace_text_rollback_on_failure(tmp_path: Path) -> None:
    """Test that atomic_replace_text cleans up temp file on failure."""
    import contextlib

    test_file = tmp_path / "test.md"

    # Mock Path.replace to fail
    def mock_replace(self: Path, target: Path) -> None:  # noqa: ARG001
        raise PermissionError("Simulated failure")

    with patch.object(Path, "replace", mock_replace), contextlib.suppress(Exception):
        atomic_replace_text(test_file, "Test content")

    # Verify no temp files remain
    temp_files = list(tmp_path.glob("*.tmp"))
    assert len(temp_files) == 0, "Should have cleaned up temp files"


def test_format_markdown_text_via_generated_hook(tmp_path: Path) -> None:
    """Test markdown formatting through a generated hook file."""
    # Generate settings with hooks in temp directory
    config_dir = write_project_settings(
        repo_root=tmp_path, config_dir_name=".claude", import_hooks_from="app.permissions.hooks_lib"
    )

    # Load the generated format_md.py hook using importlib
    hook_path = config_dir / "hooks" / "format_md.py"
    assert hook_path.exists(), f"Hook file not found at {hook_path}"

    spec = importlib.util.spec_from_file_location("format_md_hook", str(hook_path))
    assert spec is not None and spec.loader is not None

    format_md_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(format_md_module)

    # Test the _format_markdown_text function from the generated hook
    raw = "#  Title\n\n-  item\n-  item2"
    out = format_md_module._format_markdown_text(raw)

    # Verify formatting worked
    assert isinstance(out, str)
    assert "# Title" in out  # normalized header

    # Test with more complex markdown
    complex_md = "#   Heading with spaces\n\n*  Unordered item\n*  Another item\n\n1.  Ordered item\n2.  Second item"

    formatted = format_md_module._format_markdown_text(complex_md)
    assert isinstance(formatted, str)
    assert "# Heading with spaces" in formatted  # normalized
    assert formatted != complex_md  # should be different after formatting


def test_generated_hook_imports_from_hooks_lib(tmp_path: Path) -> None:
    """Verify the generated hook correctly imports from hooks_lib."""
    # Generate settings
    config_dir = write_project_settings(
        repo_root=tmp_path, config_dir_name=".claude", import_hooks_from="app.permissions.hooks_lib"
    )

    # Read the generated hook file
    hook_path = config_dir / "hooks" / "format_md.py"
    hook_content = hook_path.read_text()

    # Verify it imports from the correct module
    assert "from app.permissions.hooks_lib.format_md import _format_markdown_text" in hook_content
    assert "from app.permissions.hooks_lib.io import atomic_replace_text" in hook_content
    assert "def main() -> None:" in hook_content
    assert "PostToolUse" in hook_content


def test_generated_hook_uses_atomic_replace_text(tmp_path: Path) -> None:
    """Verify the generated hook uses atomic_replace_text for writing."""
    # Generate settings
    config_dir = write_project_settings(
        repo_root=tmp_path, config_dir_name=".claude", import_hooks_from="app.permissions.hooks_lib"
    )

    # Read the generated hook file
    hook_path = config_dir / "hooks" / "format_md.py"
    hook_content = hook_path.read_text()

    # Verify it uses atomic_replace_text instead of temp file logic
    assert "atomic_replace_text(path, formatted)" in hook_content
    assert "tmp.write_text" not in hook_content  # Should not have old temp logic
    assert "tmp.replace" not in hook_content  # Should not have old replace logic
