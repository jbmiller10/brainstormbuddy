"""Tests for AppState singleton and observer pattern."""

import gc
import threading

from app.core.interfaces import Reason
from app.core.state import get_app_state


def test_singleton_pattern() -> None:
    """Test that get_app_state returns the same instance."""
    state1 = get_app_state()
    state2 = get_app_state()
    assert state1 is state2
    # Protocol type checking is compile-time only, not runtime
    assert hasattr(state1, "active_project")
    assert hasattr(state1, "set_active_project")
    assert hasattr(state1, "subscribe")


def test_singleton_thread_safety() -> None:
    """Test that singleton is thread-safe."""
    instances = []

    def get_instance() -> None:
        instances.append(get_app_state())

    threads = [threading.Thread(target=get_instance) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All instances should be the same
    assert all(inst is instances[0] for inst in instances)


def test_initial_state() -> None:
    """Test that initial active_project is None."""
    state = get_app_state()
    # Reset state for testing
    state._active_project = None  # type: ignore
    assert state.active_project is None


def test_set_active_project() -> None:
    """Test setting active project."""
    state = get_app_state()
    state.set_active_project("test-project")
    assert state.active_project == "test-project"

    state.set_active_project(None)
    assert state.active_project is None


def test_observer_notification() -> None:
    """Test that observers are notified on project change."""
    state = get_app_state()
    state._active_project = None  # type: ignore
    state._subscribers.clear()  # type: ignore

    notifications: list[tuple[str | None, str | None, Reason]] = []

    def observer(new: str | None, old: str | None, reason: Reason) -> None:
        notifications.append((new, old, reason))

    unsubscribe = state.subscribe(observer)

    # Change project
    state.set_active_project("project-1", reason="manual")
    assert len(notifications) == 1
    assert notifications[0] == ("project-1", None, "manual")

    # Change again
    state.set_active_project("project-2", reason="project-switch")
    assert len(notifications) == 2
    assert notifications[1] == ("project-2", "project-1", "project-switch")

    # Unsubscribe and verify no more notifications
    unsubscribe()
    state.set_active_project("project-3")
    assert len(notifications) == 2  # No new notification


def test_multiple_observers() -> None:
    """Test that multiple observers work correctly."""
    state = get_app_state()
    state._active_project = None  # type: ignore
    state._subscribers.clear()  # type: ignore

    notifications1: list[tuple[str | None, str | None, Reason]] = []
    notifications2: list[tuple[str | None, str | None, Reason]] = []

    def observer1(new: str | None, old: str | None, reason: Reason) -> None:
        notifications1.append((new, old, reason))

    def observer2(new: str | None, old: str | None, reason: Reason) -> None:
        notifications2.append((new, old, reason))

    unsub1 = state.subscribe(observer1)
    unsub2 = state.subscribe(observer2)

    state.set_active_project("test", reason="wizard-accept")

    assert len(notifications1) == 1
    assert len(notifications2) == 1
    assert notifications1[0] == ("test", None, "wizard-accept")
    assert notifications2[0] == ("test", None, "wizard-accept")

    # Unsubscribe one
    unsub1()
    state.set_active_project("test2")

    assert len(notifications1) == 1  # No new notification
    assert len(notifications2) == 2  # Got notification

    unsub2()


def test_weak_reference_cleanup() -> None:
    """Test that weak references prevent memory leaks."""
    import asyncio
    import warnings

    # Close any existing event loops to prevent resource warnings
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.close()
    except RuntimeError:
        pass  # No event loop exists

    state = get_app_state()
    state._subscribers.clear()  # type: ignore

    class Observer:
        def __init__(self) -> None:
            self.notifications: list[tuple[str | None, str | None, Reason]] = []

        def callback(self, new: str | None, old: str | None, reason: Reason) -> None:
            self.notifications.append((new, old, reason))

    # Create observer and subscribe
    observer = Observer()
    state.subscribe(observer.callback)
    assert len(state._subscribers) == 1  # type: ignore

    # Delete observer and force garbage collection
    del observer

    # Suppress resource warnings during gc.collect() as they're from previous tests
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ResourceWarning)
        gc.collect()

    # The callback should be cleaned up on next notification
    state.set_active_project("cleanup-test")
    # Weak reference should be dead and cleaned up
    assert len(state._subscribers) == 0  # type: ignore


def test_observer_exception_handling() -> None:
    """Test that exceptions in observers don't break notifications."""
    state = get_app_state()
    state._active_project = None  # type: ignore
    state._subscribers.clear()  # type: ignore

    notifications: list[tuple[str | None, str | None, Reason]] = []

    def bad_observer(new: str | None, old: str | None, reason: Reason) -> None:  # noqa: ARG001
        raise ValueError("Test exception")

    def good_observer(new: str | None, old: str | None, reason: Reason) -> None:
        notifications.append((new, old, reason))

    state.subscribe(bad_observer)
    state.subscribe(good_observer)

    # Bad observer throws, but good observer should still be notified
    state.set_active_project("test", reason="reset")
    assert len(notifications) == 1
    assert notifications[0] == ("test", None, "reset")


def test_reason_values() -> None:
    """Test all valid reason values."""
    state = get_app_state()
    state._active_project = None  # type: ignore

    reasons: list[Reason] = ["manual", "wizard-accept", "project-switch", "reset"]
    notifications: list[Reason] = []

    def observer(new: str | None, old: str | None, reason: Reason) -> None:  # noqa: ARG001
        notifications.append(reason)

    state.subscribe(observer)

    for i, reason in enumerate(reasons):
        state.set_active_project(f"project-{i}", reason=reason)

    assert notifications == reasons


def test_unsubscribe_idempotency() -> None:
    """Test that calling unsubscribe multiple times is safe."""
    state = get_app_state()
    state._subscribers.clear()  # type: ignore

    def observer(new: str | None, old: str | None, reason: Reason) -> None:
        pass

    unsubscribe = state.subscribe(observer)

    # Should work fine
    unsubscribe()
    unsubscribe()  # Second call should not error
    unsubscribe()  # Third call should not error
