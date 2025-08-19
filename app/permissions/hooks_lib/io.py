"""I/O utilities for hooks with durability guarantees."""

import os
import tempfile
from pathlib import Path


def atomic_replace_text(path: Path, text: str) -> None:
    """
    Atomically replace file contents with durability guarantees.

    Performs atomic write with flush+fsync on both file and parent directory.
    This ensures data is persisted to disk before returning.

    Args:
        path: Path to the file to write
        text: Text content to write (UTF-8 encoded)

    Raises:
        IOError: If there's an error during the atomic write operation
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve file mode if file exists
    file_mode = None
    if path.exists():
        file_mode = os.stat(path).st_mode

    # Write to temporary file first
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        suffix=".tmp",
    ) as tmp_file:
        tmp_file.write(text)
        tmp_file.flush()
        # Ensure data is written to disk
        os.fsync(tmp_file.fileno())
        tmp_path = Path(tmp_file.name)

    try:
        # Preserve file mode if original file existed
        if file_mode is not None:
            os.chmod(tmp_path, file_mode)

        # Atomically replace the original file
        tmp_path.replace(path)

        # Fsync parent directory for durability (best-effort)
        try:
            dfd = os.open(path.parent, os.O_DIRECTORY)
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
