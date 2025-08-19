"""Diff and patch utilities for atomic file operations."""

import difflib
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Patch:
    """Represents a patch to be applied to a file."""

    original: str
    modified: str
    diff_lines: list[str]


def compute_patch(old: str, new: str) -> Patch:
    """
    Compute a patch representing the difference between two strings.

    Args:
        old: Original text content
        new: Modified text content

    Returns:
        Patch object containing the diff information
    """
    # Split into lines while preserving line endings
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    # Generate unified diff
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        lineterm="",
    )

    return Patch(
        original=old,
        modified=new,
        diff_lines=list(diff),
    )


def apply_patch(path: Path | str, patch: Patch) -> None:
    """
    Apply a patch to a file atomically using temp file and replace.

    This ensures the file is either fully updated or not modified at all,
    preventing partial writes in case of errors.

    Args:
        path: Path to the file to patch
        patch: Patch object to apply

    Raises:
        IOError: If there's an error during the atomic write operation
    """
    file_path = Path(path) if isinstance(path, str) else path

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary file first
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=file_path.parent,
        delete=False,
        suffix=".tmp",
    ) as tmp_file:
        tmp_file.write(patch.modified)
        tmp_path = Path(tmp_file.name)

    try:
        # Atomically replace the original file
        tmp_path.replace(file_path)
    except Exception:
        # Clean up temp file if replacement fails
        tmp_path.unlink(missing_ok=True)
        raise


def generate_diff_preview(old: str, new: str, context_lines: int = 3) -> str:
    """
    Generate a human-readable diff preview.

    Args:
        old: Original text content
        new: Modified text content
        context_lines: Number of context lines to show around changes

    Returns:
        String representation of the diff suitable for display
    """
    # context_lines parameter kept for API compatibility but not used in simple implementation
    _ = context_lines
    patch = compute_patch(old, new)

    if not patch.diff_lines:
        return "No changes detected."

    return "".join(patch.diff_lines)


def is_unchanged(patch: Patch) -> bool:
    """
    Check if a patch represents no changes.

    Args:
        patch: Patch object to check

    Returns:
        True if the patch represents no changes, False otherwise
    """
    return patch.original == patch.modified or len(patch.diff_lines) == 0


def apply_patch_from_strings(path: Path | str, old_content: str, new_content: str) -> Patch | None:
    """
    Helper function to compute and apply a patch in one operation.

    Args:
        path: Path to the file to patch
        old_content: Expected current content (for verification)
        new_content: New content to write

    Returns:
        The applied Patch object, or None if no changes were needed

    Raises:
        ValueError: If the current file content doesn't match old_content
        IOError: If there's an error during the write operation
    """
    file_path = Path(path) if isinstance(path, str) else path

    # Read current content if file exists
    if file_path.exists():
        with open(file_path, encoding="utf-8") as f:
            current = f.read()
        if current != old_content:
            raise ValueError(f"Current content of {file_path} doesn't match expected old_content")

    # Compute patch
    patch = compute_patch(old_content, new_content)

    # Only apply if there are changes
    if not is_unchanged(patch):
        apply_patch(file_path, patch)
        return patch

    return None
