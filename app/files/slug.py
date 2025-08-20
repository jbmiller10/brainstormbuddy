"""Slug utilities for safe filesystem operations."""

import re
import unicodedata
from pathlib import Path


def slugify(title: str) -> str:
    """
    Convert a title string to a safe filesystem slug.

    Args:
        title: Human-readable title to convert

    Returns:
        Safe slug suitable for filesystem operations

    Examples:
        >>> slugify("My Cool Project!")
        'my-cool-project'
        >>> slugify("ACME 🚀 Inc.")
        'acme-inc'
        >>> slugify("")
        'untitled'
    """
    # Handle empty or whitespace-only strings
    if not title or not title.strip():
        return "untitled"

    # Normalize unicode and remove accents
    title = unicodedata.normalize("NFKD", title)
    title = "".join(c for c in title if unicodedata.category(c) != "Mn")

    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = title.lower().strip()

    # Replace any non-alphanumeric characters (except hyphens/underscores) with hyphens
    slug = re.sub(r"[^a-z0-9_-]+", "-", slug)

    # Collapse multiple hyphens into single hyphen
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Handle edge case where everything was stripped
    if not slug:
        return "untitled"

    # Cap at 64 characters
    if len(slug) > 64:
        slug = slug[:64].rstrip("-")

    return slug


def enforce_slug(slug: str) -> str:
    """
    Validate and enforce slug safety.

    Args:
        slug: Slug string to validate

    Returns:
        The validated slug

    Raises:
        ValueError: If slug is invalid or contains dangerous patterns

    Examples:
        >>> enforce_slug("my-project")
        'my-project'
        >>> enforce_slug("../etc/passwd")
        Traceback (most recent call last):
        ...
        ValueError: Slug contains path traversal attempt: ../etc/passwd
    """
    # Check for empty slug
    if not slug or not slug.strip():
        raise ValueError("Slug cannot be empty")

    # Check for path traversal attempts
    dangerous_patterns = ["..", ".", "~", "/", "\\"]
    for pattern in dangerous_patterns:
        if pattern in slug:
            raise ValueError(f"Slug contains path traversal attempt: {slug}")

    # Check for reserved names (Windows compatibility)
    reserved_names = {
        "con",
        "prn",
        "aux",
        "nul",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
    }

    slug_lower = slug.lower()
    base_name = slug_lower.split(".")[0] if "." in slug_lower else slug_lower

    if base_name in reserved_names:
        raise ValueError(f"Slug uses reserved name: {slug}")

    # Ensure slug only contains safe characters
    if not re.match(r"^[a-zA-Z0-9_-]+$", slug):
        raise ValueError(f"Slug contains invalid characters: {slug}")

    # Check length
    if len(slug) > 255:
        raise ValueError(f"Slug is too long (max 255 characters): {slug}")

    return slug


def ensure_unique_slug(base_slug: str, base_path: Path | str = "projects") -> str:
    """
    Ensure a slug is unique by appending a suffix if necessary.

    Args:
        base_slug: The desired slug
        base_path: Base directory to check for collisions (default: "projects")

    Returns:
        A unique slug, possibly with -2, -3, etc. appended

    Examples:
        If "my-project" exists:
        >>> ensure_unique_slug("my-project")
        'my-project-2'

        If "my-project" and "my-project-2" exist:
        >>> ensure_unique_slug("my-project")
        'my-project-3'
    """
    # Validate the base slug first
    base_slug = enforce_slug(base_slug)

    # Convert base_path to Path object
    base = Path(base_path) if isinstance(base_path, str) else base_path

    # Check if the base slug is already unique
    if not (base / base_slug).exists():
        return base_slug

    # Find a unique suffix
    counter = 2
    while True:
        candidate = f"{base_slug}-{counter}"
        if not (base / candidate).exists():
            return candidate
        counter += 1

        # Safety check to prevent infinite loops
        if counter > 1000:
            raise ValueError(f"Could not find unique slug after 1000 attempts for: {base_slug}")
