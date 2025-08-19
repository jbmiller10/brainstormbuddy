"""Batch diff builder and preview for atomic multi-file operations."""

from dataclasses import dataclass, field
from pathlib import Path

from app.files.diff import (
    Patch,
    apply_patches,
    compute_patch,
    generate_diff_preview,
    is_unchanged,
)


@dataclass
class FileChange:
    """Represents a pending change to a single file."""

    path: Path
    old_content: str
    new_content: str

    @property
    def is_new_file(self) -> bool:
        """Check if this represents a new file creation."""
        return self.old_content == ""

    @property
    def has_changes(self) -> bool:
        """Check if there are actual changes."""
        patch = compute_patch(self.old_content, self.new_content)
        return not is_unchanged(patch)


@dataclass
class BatchDiff:
    """Aggregates multiple file changes for atomic batch operations."""

    changes: list[FileChange] = field(default_factory=list)

    def add_file(self, path: Path | str, old_content: str, new_content: str) -> None:
        """
        Add a file change to the batch.

        Args:
            path: Path to the file
            old_content: Current content (empty string for new files)
            new_content: New content to write
        """
        file_path = Path(path) if isinstance(path, str) else path
        change = FileChange(file_path, old_content, new_content)

        # Only add if there are actual changes
        if change.has_changes:
            self.changes.append(change)

    def add_new_file(self, path: Path | str, content: str) -> None:
        """
        Convenience method to add a new file creation.

        Args:
            path: Path to the new file
            content: Content for the new file
        """
        self.add_file(path, "", content)

    def add_existing_file(self, path: Path | str, new_content: str) -> None:
        """
        Add an existing file modification, reading current content.

        Args:
            path: Path to the existing file
            new_content: New content to write

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        file_path = Path(path) if isinstance(path, str) else path

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            old_content = f.read()

        self.add_file(file_path, old_content, new_content)

    def generate_preview(self, context_lines: int = 3) -> str:
        """
        Generate a combined diff preview for all changes.

        Args:
            context_lines: Number of context lines around changes

        Returns:
            Combined diff preview as a string
        """
        if not self.changes:
            return "No changes to preview."

        previews = []

        for change in self.changes:
            # Generate individual diff with file path as label
            diff = generate_diff_preview(
                change.old_content,
                change.new_content,
                context_lines=context_lines,
                from_label=f"{change.path} (current)",
                to_label=f"{change.path} (proposed)",
            )

            # Add separator between files
            if diff != "No changes detected.":
                previews.append(f"{'=' * 60}")
                previews.append(f"File: {change.path}")
                if change.is_new_file:
                    previews.append("(new file)")
                previews.append(f"{'=' * 60}")
                previews.append(diff)

        if not previews:
            return "No changes to preview."

        return "\n".join(previews)

    def apply(self) -> list[Patch]:
        """
        Apply all changes atomically.

        Either all files are updated successfully, or none are modified.
        Uses temporary files and atomic replacement to ensure safety.

        Returns:
            List of Patch objects for applied changes

        Raises:
            IOError: If atomic replacement fails
            ValueError: If any file's current content doesn't match expected
        """
        if not self.changes:
            return []

        # Convert to format expected by apply_patches
        patches_list: list[tuple[Path | str, str, str]] = [
            (change.path, change.old_content, change.new_content) for change in self.changes
        ]

        # Apply all patches atomically
        return apply_patches(patches_list)

    def clear(self) -> None:
        """Clear all pending changes."""
        self.changes.clear()

    def __len__(self) -> int:
        """Return the number of pending changes."""
        return len(self.changes)

    def __bool__(self) -> bool:
        """Return True if there are pending changes."""
        return len(self.changes) > 0


def create_batch_from_dict(files: dict[str, str], base_path: Path | None = None) -> BatchDiff:
    """
    Create a BatchDiff from a dictionary of relative paths to content.

    Args:
        files: Dictionary mapping relative paths to file content
        base_path: Base directory for resolving relative paths

    Returns:
        BatchDiff instance with all file changes
    """
    batch = BatchDiff()

    for rel_path, content in files.items():
        full_path = base_path / rel_path if base_path else Path(rel_path)

        # Check if file exists to determine old content
        if full_path.exists():
            with open(full_path, encoding="utf-8") as f:
                old_content = f.read()
        else:
            old_content = ""

        batch.add_file(full_path, old_content, content)

    return batch
