"""Tests for file locking mechanism."""

import concurrent.futures
import tempfile
import time
from pathlib import Path

import pytest

from app.files.lock import FileLock, project_creation_lock, slug_generation_lock


class TestFileLock:
    """Test FileLock class."""

    def test_basic_lock_acquire_release(self, tmp_path: Path) -> None:
        """Test basic lock acquisition and release."""
        lock = FileLock("test_lock", base_dir=tmp_path)

        # Should be able to acquire lock
        assert lock.acquire() is True

        # Should be able to release lock
        lock.release()

        # Should be able to acquire again after release
        assert lock.acquire() is True
        lock.release()

    def test_lock_timeout(self, tmp_path: Path) -> None:
        """Test lock timeout when already held."""
        lock1 = FileLock("test_lock", timeout=0.1, base_dir=tmp_path)
        lock2 = FileLock("test_lock", timeout=0.1, base_dir=tmp_path)

        # First lock should succeed
        assert lock1.acquire() is True

        # Second lock should timeout
        assert lock2.acquire() is False

        # Clean up
        lock1.release()

    def test_context_manager(self, tmp_path: Path) -> None:
        """Test lock as context manager."""
        with FileLock("test_lock", base_dir=tmp_path) as lock:
            assert lock.fd is not None

        # Lock should be released after context
        lock2 = FileLock("test_lock", timeout=0.1, base_dir=tmp_path)
        assert lock2.acquire() is True
        lock2.release()

    def test_context_manager_timeout(self, tmp_path: Path) -> None:
        """Test context manager timeout."""
        lock1 = FileLock("test_lock", base_dir=tmp_path)
        lock1.acquire()

        with pytest.raises(TimeoutError), FileLock("test_lock", timeout=0.1, base_dir=tmp_path):
            pass

        lock1.release()

    def test_concurrent_access(self, tmp_path: Path) -> None:
        """Test concurrent access protection."""
        counter = 0
        lock_name = "concurrent_test"

        def increment_counter() -> None:
            nonlocal counter
            with FileLock(lock_name, timeout=2.0, base_dir=tmp_path):
                # Simulate some work
                current = counter
                time.sleep(0.01)
                counter = current + 1

        # Run multiple threads trying to increment counter
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(increment_counter) for _ in range(10)]
            concurrent.futures.wait(futures)

        # Counter should be exactly 10 (no race conditions)
        assert counter == 10


class TestProjectLocks:
    """Test project-specific locking functions."""

    def test_project_creation_lock(self) -> None:
        """Test project creation lock."""
        with tempfile.TemporaryDirectory() as temp_dir, project_creation_lock("test-project"):
            # Simulate project creation
            project_path = Path(temp_dir) / "test-project"
            project_path.mkdir()
            assert project_path.exists()

    def test_slug_generation_lock(self) -> None:
        """Test slug generation lock."""
        results: list[str] = []

        def generate_slug(base: str) -> None:
            with slug_generation_lock(base):
                # Simulate slug generation with delay
                time.sleep(0.01)
                results.append(f"{base}-{len(results) + 1}")

        # Run concurrent slug generations
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(generate_slug, "project") for _ in range(5)]
            concurrent.futures.wait(futures)

        # All slugs should be unique
        assert len(set(results)) == 5

    def test_lock_prevents_duplicate_projects(self) -> None:
        """Test that locking prevents duplicate project creation."""
        project_count = 0

        def create_project(slug: str) -> bool:
            nonlocal project_count
            try:
                with project_creation_lock(slug, timeout=0.5):
                    # Check if project exists
                    if project_count > 0:
                        return False  # Already exists

                    # Simulate project creation
                    time.sleep(0.1)
                    project_count += 1
                    return True
            except TimeoutError:
                return False

        # Try to create same project concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_project, "same-project") for _ in range(3)]
            results = [f.result() for f in futures]

        # Only one should succeed
        assert sum(results) == 1
        assert project_count == 1
