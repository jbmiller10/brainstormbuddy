"""Tests for slug utilities."""

import tempfile
from pathlib import Path

import pytest

from app.files.slug import enforce_slug, ensure_unique_slug, slugify


class TestSlugify:
    """Test suite for the slugify function."""

    def test_basic_conversion(self) -> None:
        """Test basic title to slug conversion."""
        assert slugify("My Cool Project") == "my-cool-project"
        assert slugify("Hello World!") == "hello-world"
        assert slugify("Test 123") == "test-123"

    def test_special_characters(self) -> None:
        """Test handling of special characters."""
        assert slugify("Project #1") == "project-1"
        assert slugify("Hello@World.com") == "hello-world-com"
        assert slugify("Price: $99.99") == "price-99-99"
        assert slugify("C++ Programming") == "c-programming"

    def test_unicode_and_emoji(self) -> None:
        """Test handling of unicode characters and emojis."""
        assert slugify("ACME 🚀") == "acme"
        assert slugify("Café ☕") == "cafe"
        assert slugify("Björk") == "bjork"
        assert slugify("Москва") == "untitled"  # Cyrillic gets stripped
        assert slugify("北京") == "untitled"  # Chinese characters get stripped
        assert slugify("🎉🎊🎈") == "untitled"  # Only emojis

    def test_multiple_spaces_and_hyphens(self) -> None:
        """Test collapsing of multiple spaces and hyphens."""
        assert slugify("Too    Many    Spaces") == "too-many-spaces"
        assert slugify("Already---Has---Hyphens") == "already-has-hyphens"
        assert slugify("   Leading and Trailing   ") == "leading-and-trailing"

    def test_empty_and_whitespace(self) -> None:
        """Test empty and whitespace-only strings."""
        assert slugify("") == "untitled"
        assert slugify("   ") == "untitled"
        assert slugify("\t\n") == "untitled"

    def test_length_capping(self) -> None:
        """Test that slugs are capped at 64 characters."""
        long_title = "This is a very long title that exceeds the maximum allowed length for a slug"
        result = slugify(long_title)
        assert len(result) <= 64
        # The slug gets truncated to exactly 64 characters
        assert result == "this-is-a-very-long-title-that-exceeds-the-maximum-allowed-lengt"
        assert len(result) == 64

    def test_underscores_preserved(self) -> None:
        """Test that underscores are preserved."""
        assert slugify("snake_case_name") == "snake_case_name"
        assert slugify("Mix_of-Both") == "mix_of-both"

    def test_edge_cases(self) -> None:
        """Test various edge cases."""
        assert slugify("!!!") == "untitled"
        assert slugify("---") == "untitled"
        assert slugify("123") == "123"
        assert slugify("-start-with-hyphen") == "start-with-hyphen"
        assert slugify("end-with-hyphen-") == "end-with-hyphen"


class TestEnforceSlug:
    """Test suite for the enforce_slug function."""

    def test_valid_slugs(self) -> None:
        """Test that valid slugs pass through unchanged."""
        assert enforce_slug("my-project") == "my-project"
        assert enforce_slug("project123") == "project123"
        assert enforce_slug("snake_case") == "snake_case"
        assert enforce_slug("Mix-Of_Both") == "Mix-Of_Both"

    def test_empty_slug(self) -> None:
        """Test that empty slugs raise ValueError."""
        with pytest.raises(ValueError, match="Slug cannot be empty"):
            enforce_slug("")
        with pytest.raises(ValueError, match="Slug cannot be empty"):
            enforce_slug("   ")

    def test_path_traversal_attempts(self) -> None:
        """Test detection of path traversal attempts."""
        with pytest.raises(ValueError, match="path traversal"):
            enforce_slug("../etc/passwd")
        with pytest.raises(ValueError, match="path traversal"):
            enforce_slug("./hidden")
        with pytest.raises(ValueError, match="path traversal"):
            enforce_slug("~/home")
        with pytest.raises(ValueError, match="path traversal"):
            enforce_slug("some/nested/path")
        with pytest.raises(ValueError, match="path traversal"):
            enforce_slug("back\\slash")
        with pytest.raises(ValueError, match="path traversal"):
            enforce_slug("project/..")

    def test_reserved_names(self) -> None:
        """Test detection of Windows reserved names."""
        reserved = ["con", "prn", "aux", "nul", "com1", "lpt1"]
        for name in reserved:
            with pytest.raises(ValueError, match="reserved name"):
                enforce_slug(name)
            with pytest.raises(ValueError, match="reserved name"):
                enforce_slug(name.upper())  # Case insensitive

    def test_invalid_characters(self) -> None:
        """Test detection of invalid characters."""
        with pytest.raises(ValueError, match="invalid characters"):
            enforce_slug("hello world")  # Space
        with pytest.raises(ValueError, match="invalid characters"):
            enforce_slug("project!")
        with pytest.raises(ValueError, match="invalid characters"):
            enforce_slug("test@example")
        with pytest.raises(ValueError, match="invalid characters"):
            enforce_slug("price$99")

    def test_length_limit(self) -> None:
        """Test that overly long slugs are rejected."""
        long_slug = "a" * 256
        with pytest.raises(ValueError, match="too long"):
            enforce_slug(long_slug)

        # Just under the limit should pass
        ok_slug = "a" * 255
        assert enforce_slug(ok_slug) == ok_slug


class TestEnsureUniqueSlug:
    """Test suite for the ensure_unique_slug function."""

    def test_no_collision(self) -> None:
        """Test when no collision exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            slug = ensure_unique_slug("my-project", base)
            assert slug == "my-project"

    def test_single_collision(self) -> None:
        """Test handling of a single collision."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            # Create existing project
            (base / "my-project").mkdir()

            slug = ensure_unique_slug("my-project", base)
            assert slug == "my-project-2"

    def test_multiple_collisions(self) -> None:
        """Test handling of multiple collisions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            # Create existing projects
            (base / "my-project").mkdir()
            (base / "my-project-2").mkdir()
            (base / "my-project-3").mkdir()

            slug = ensure_unique_slug("my-project", base)
            assert slug == "my-project-4"

    def test_validates_base_slug(self) -> None:
        """Test that base slug is validated before checking uniqueness."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Invalid slug should raise error
            with pytest.raises(ValueError, match="path traversal"):
                ensure_unique_slug("../bad", base)

            with pytest.raises(ValueError, match="invalid characters"):
                ensure_unique_slug("bad slug", base)

    def test_string_base_path(self) -> None:
        """Test that base_path can be provided as string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pass as string instead of Path
            slug = ensure_unique_slug("test-project", tmpdir)
            assert slug == "test-project"

    def test_collision_with_file(self) -> None:
        """Test collision detection works with files, not just directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            # Create a file instead of directory
            (base / "my-project").touch()

            slug = ensure_unique_slug("my-project", base)
            assert slug == "my-project-2"

    def test_many_collisions_safety(self) -> None:
        """Test safety check for excessive collisions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Create many existing projects (simulate worst case)
            for i in range(1, 1001):
                if i == 1:
                    (base / "test").mkdir()
                else:
                    (base / f"test-{i}").mkdir()

            # Should raise after 1000 attempts
            with pytest.raises(ValueError, match="1000 attempts"):
                ensure_unique_slug("test", base)

    def test_preserves_valid_slug_format(self) -> None:
        """Test that uniqueness suffix maintains valid slug format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            (base / "my_project").mkdir()

            slug = ensure_unique_slug("my_project", base)
            assert slug == "my_project-2"
            # Verify the result is still a valid slug
            assert enforce_slug(slug) == slug
