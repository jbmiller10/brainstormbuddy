"""Atomic file write utilities."""

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path | str, text: str) -> None:
    """
    Write text to a file atomically using temp file and replace.

    This ensures the file is either fully updated or not modified at all,
    preventing partial writes in case of errors. Uses the same durability
    pattern as apply_patch.

    Args:
        path: Path to the file to write
        text: Text content to write (UTF-8 encoded)

    Raises:
        IOError: If there's an error during the atomic write operation
    """
    file_path = Path(path) if isinstance(path, str) else path

    # Precompute file mode if file exists
    file_mode = None
    if file_path.exists():
        file_mode = os.stat(file_path).st_mode

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
        tmp_file.write(text)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_path = Path(tmp_file.name)

    try:
        # Preserve file mode if original file existed
        if file_mode is not None:
            os.chmod(tmp_path, file_mode)

        # Atomically replace the original file
        tmp_path.replace(file_path)

        # Fsync parent directory for durability (best-effort)
        try:
            dfd = os.open(file_path.parent, os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:
            # Platform/filesystem doesn't support directory fsync
            pass
    except Exception:
        # Clean up temp file if replacement fails
        tmp_path.unlink(missing_ok=True)
        raise
