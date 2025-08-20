"""Diff and patch utilities for atomic file operations."""

import difflib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.files.atomic import atomic_write_text


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
    # Delegate to atomic_write_text for the actual atomic write
    atomic_write_text(path, patch.modified)


def generate_diff_preview(
    old: str,
    new: str,
    context_lines: int = 3,
    from_label: str | None = None,
    to_label: str | None = None,
) -> str:
    """
    Generate a human-readable diff preview.

    Args:
        old: Original text content
        new: Modified text content
        context_lines: Number of context lines to show around changes
        from_label: Optional label for the original file (defaults to "before")
        to_label: Optional label for the modified file (defaults to "after")

    Returns:
        String representation of the diff suitable for display
    """
    # Split into lines while preserving line endings
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    # Generate unified diff with specified context
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=from_label if from_label is not None else "before",
        tofile=to_label if to_label is not None else "after",
        n=context_lines,
        lineterm="",
    )

    diff_lines = list(diff)

    if not diff_lines:
        return "No changes detected."

    # Join with newlines for readable output
    return "\n".join(diff_lines)


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


def apply_patches(patches: list[tuple[Path | str, str, str]]) -> list[Patch]:
    """
    Apply multiple file edits atomically (all-or-nothing).

    This function ensures that either all patches are applied successfully,
    or none are applied at all. It writes all temporary files first, then
    replaces all targets atomically. On any failure, all temporary files
    are cleaned up and original files remain unchanged.

    Args:
        patches: List of tuples containing (path, old_content, new_content)

    Returns:
        List of Patch objects for each changed file

    Raises:
        IOError: If there's an error during the atomic write operations
        ValueError: If any file's current content doesn't match expected
    """
    # Prepare all patches and temp files
    temp_files: list[tuple[Path, Path, int | None, str, bool]] = []
    computed_patches: list[Patch] = []
    backup_files: list[tuple[Path, Path]] = []

    try:
        for path_input, old_content, new_content in patches:
            file_path = Path(path_input) if isinstance(path_input, str) else path_input

            # Track whether file existed before operation
            existed_before = file_path.exists()

            # Read and verify current content if file exists
            if existed_before:
                with open(file_path, encoding="utf-8") as f:
                    current = f.read()
                if current != old_content:
                    raise ValueError(
                        f"Current content of {file_path} doesn't match expected old_content"
                    )
                # Preserve file mode
                file_mode = os.stat(file_path).st_mode
            else:
                file_mode = None
                current = ""
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Compute patch
            patch = compute_patch(old_content, new_content)

            # Skip unchanged files
            if is_unchanged(patch):
                continue

            computed_patches.append(patch)

            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=file_path.parent,
                delete=False,
                suffix=".tmp",
            ) as tmp_file:
                tmp_file.write(new_content)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                tmp_path = Path(tmp_file.name)

            # Store temp file info for later replacement
            temp_files.append((file_path, tmp_path, file_mode, current, existed_before))

        # Create backups of existing files before replacement
        for target_path, _, _, original_content, existed_before in temp_files:
            if existed_before:
                # Create backup file
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=target_path.parent,
                    delete=False,
                    suffix=".backup",
                ) as backup_file:
                    backup_file.write(original_content)
                    backup_file.flush()
                    os.fsync(backup_file.fileno())
                    backup_path = Path(backup_file.name)
                backup_files.append((target_path, backup_path))

        # Now replace all files
        completed_replacements = []
        try:
            for target_path, temp_path, file_mode, _, _ in temp_files:
                # Preserve file mode if it existed
                if file_mode is not None:
                    os.chmod(temp_path, file_mode)

                # Atomic replace
                temp_path.replace(target_path)
                completed_replacements.append(target_path)

            # Fsync parent directories for durability (best-effort)
            # Collect unique parent directories
            parent_dirs = set()
            for target_path, _, _, _, _ in temp_files:
                parent_dirs.add(target_path.parent)

            # Fsync each parent directory once
            for parent_dir in parent_dirs:
                try:
                    dfd = os.open(parent_dir, getattr(os, "O_DIRECTORY", 0))
                    try:
                        os.fsync(dfd)
                    finally:
                        os.close(dfd)
                except OSError:
                    # Platform/filesystem doesn't support directory fsync
                    pass

        except Exception as e:
            # Restore original files from backups or remove newly created files
            for target_path in completed_replacements:
                # Find if this file existed before the operation
                existed_before = False
                for file_path, _, _, _, file_existed in temp_files:
                    if file_path == target_path:
                        existed_before = file_existed
                        break

                if existed_before:
                    # Find the backup for this file and restore it
                    for orig_path, backup_path in backup_files:
                        if orig_path == target_path:
                            backup_path.replace(target_path)
                            break
                else:
                    # File didn't exist before, remove it
                    target_path.unlink(missing_ok=True)

            # Clean up any remaining temp files
            for target_path, temp_path, _, _, _ in temp_files:
                if target_path not in completed_replacements:
                    temp_path.unlink(missing_ok=True)

            # Clean up backup files
            for _, backup_path in backup_files:
                backup_path.unlink(missing_ok=True)

            raise OSError(f"Failed to atomically replace files: {e}") from e

        # Success - clean up backup files
        for _, backup_path in backup_files:
            backup_path.unlink(missing_ok=True)

    except Exception:
        # Clean up any temp files created before the error
        for _, temp_path, _, _, _ in temp_files:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
        raise

    return computed_patches
