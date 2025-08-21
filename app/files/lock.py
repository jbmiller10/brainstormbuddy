"""File-based locking mechanism for preventing race conditions."""

import fcntl
import os
import tempfile
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


class FileLock:
    """File-based lock for preventing concurrent access to resources."""

    def __init__(self, lock_name: str, timeout: float = 5.0, base_dir: Path | str | None = None):
        """
        Initialize a file lock.

        Args:
            lock_name: Name of the lock (will be used for lock file name)
            timeout: Maximum time to wait for lock acquisition in seconds
            base_dir: Directory for lock files (defaults to system temp dir)
        """
        self.lock_name = lock_name
        self.timeout = timeout

        if base_dir is None:
            base_dir = Path(tempfile.gettempdir()) / "brainstormbuddy_locks"
        else:
            base_dir = Path(base_dir) if isinstance(base_dir, str) else base_dir

        # Ensure lock directory exists
        base_dir.mkdir(parents=True, exist_ok=True)

        self.lock_file = base_dir / f"{lock_name}.lock"
        self.fd: int | None = None

    def acquire(self) -> bool:
        """
        Acquire the lock.

        Returns:
            True if lock acquired, False if timeout occurred

        Raises:
            OSError: If there's an issue with the lock file
        """
        start_time = time.time()

        # Open or create the lock file
        self.fd = os.open(str(self.lock_file), os.O_CREAT | os.O_WRONLY)

        while True:
            try:
                # Try to acquire an exclusive lock (non-blocking)
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                # Lock is held by another process
                if time.time() - start_time > self.timeout:
                    # Timeout exceeded
                    os.close(self.fd)
                    self.fd = None
                    return False
                # Wait a bit before retrying
                time.sleep(0.01)

    def release(self) -> None:
        """Release the lock."""
        if self.fd is not None:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                os.close(self.fd)
            except OSError:
                # Best effort - lock may already be released
                pass
            finally:
                self.fd = None

    def __enter__(self) -> "FileLock":
        """Context manager entry."""
        if not self.acquire():
            raise TimeoutError(f"Could not acquire lock '{self.lock_name}' within {self.timeout} seconds")
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
        """Context manager exit."""
        self.release()


@contextmanager
def project_creation_lock(project_slug: str, timeout: float = 5.0) -> Generator[None, None, None]:
    """
    Context manager for locking project creation.

    Args:
        project_slug: The project identifier to lock
        timeout: Maximum time to wait for lock in seconds

    Yields:
        None when lock is acquired

    Raises:
        TimeoutError: If lock cannot be acquired within timeout

    Example:
        >>> with project_creation_lock("my-project"):
        ...     # Create project directories and files
        ...     scaffold_project("my-project")
    """
    lock = FileLock(f"project_{project_slug}", timeout=timeout)
    with lock:
        yield


@contextmanager
def slug_generation_lock(base_slug: str, timeout: float = 2.0) -> Generator[None, None, None]:
    """
    Context manager for locking slug generation to prevent duplicates.

    Args:
        base_slug: The base slug to lock
        timeout: Maximum time to wait for lock in seconds

    Yields:
        None when lock is acquired

    Raises:
        TimeoutError: If lock cannot be acquired within timeout

    Example:
        >>> with slug_generation_lock("my-project"):
        ...     unique_slug = ensure_unique_slug("my-project")
    """
    lock = FileLock(f"slug_{base_slug}", timeout=timeout)
    with lock:
        yield
