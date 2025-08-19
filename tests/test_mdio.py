"""Unit tests for Markdown I/O utilities."""

import tempfile
from pathlib import Path

import pytest

from app.files.mdio import read_md, write_md


def test_write_md_creates_nested_directories() -> None:
    """Test that write_md creates parent directories if they don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write to a deeply nested path that doesn't exist
        nested_path = Path(tmpdir) / "level1" / "level2" / "level3" / "test.md"
        content = "# Test Content\n\nThis is a test."

        write_md(nested_path, content)

        # Verify file was created and content is correct
        assert nested_path.exists()
        assert read_md(nested_path) == content


def test_write_md_overwrites_existing_file() -> None:
    """Test that write_md correctly overwrites an existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"

        # Write initial content
        initial_content = "# Initial\n\nFirst version."
        write_md(file_path, initial_content)
        assert read_md(file_path) == initial_content

        # Overwrite with new content
        new_content = "# Updated\n\nSecond version."
        write_md(file_path, new_content)
        assert read_md(file_path) == new_content


def test_unicode_content_roundtrip() -> None:
    """Test that Unicode content is correctly written and read back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "unicode_test.md"

        # Test various Unicode characters
        unicode_content = (
            "# Unicode Test æøå—π🙂\n\n"
            + "Chinese: 你好世界\n"
            + "Japanese: こんにちは\n"
            + "Arabic: مرحبا بالعالم\n"
            + "Emoji: 🚀 🌟 ✨\n"
            + "Math: ∑ ∫ √ ∞ π"
        )

        write_md(file_path, unicode_content)
        read_content = read_md(file_path)

        assert read_content == unicode_content


def test_idempotent_write_same_content() -> None:
    """Test that writing the same content twice is idempotent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "idempotent_test.md"
        content = "# Idempotent Test\n\nSame content written twice."

        # First write
        write_md(file_path, content)
        first_content = read_md(file_path)

        # Second write with identical content
        write_md(file_path, content)
        second_content = read_md(file_path)

        # Content should be identical
        assert first_content == second_content == content
        # File should exist and have been replaced (mtime may differ)
        assert file_path.exists()


def test_read_md_with_string_path() -> None:
    """Test that read_md works with string paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"
        content = "# String Path Test"

        write_md(str(file_path), content)
        assert read_md(str(file_path)) == content


def test_write_md_with_string_path() -> None:
    """Test that write_md works with string paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"
        content = "# String Path Test"

        write_md(str(file_path), content)
        assert read_md(file_path) == content


def test_read_md_nonexistent_file() -> None:
    """Test that read_md raises FileNotFoundError for non-existent files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_path = Path(tmpdir) / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            read_md(nonexistent_path)


def test_empty_file_roundtrip() -> None:
    """Test that empty files are handled correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "empty.md"

        write_md(file_path, "")
        assert read_md(file_path) == ""


def test_large_content_roundtrip() -> None:
    """Test that large content is correctly written and read back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "large.md"

        # Create a large content string (1MB+)
        large_content = "# Large File\n\n" + ("This is a line of text. " * 100 + "\n") * 5000

        write_md(file_path, large_content)
        read_content = read_md(file_path)

        assert read_content == large_content


def test_special_characters_in_content() -> None:
    """Test that special characters are preserved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "special.md"

        special_content = (
            "# Special Characters\n\n"
            + "Quotes: \"double\" 'single'\n"
            + "Backslash: \\ \\\\ \\\\\\\n"
            + "Tabs: \t\t\tindented\n"
            + "NULL char exclusion test (should work without null)"
        )

        write_md(file_path, special_content)
        assert read_md(file_path) == special_content


def test_preserve_exact_content() -> None:
    """Test that content with no trailing newline is preserved exactly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "exact.md"

        # Content with no trailing newline
        content_no_newline = "# No trailing newline"
        write_md(file_path, content_no_newline)
        assert read_md(file_path) == content_no_newline

        # Content with trailing newline
        content_with_newline = "# With trailing newline\n"
        write_md(file_path, content_with_newline)
        assert read_md(file_path) == content_with_newline
