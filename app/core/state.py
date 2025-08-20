"""Application state management with project switching support."""

import contextlib
import weakref
from collections.abc import Callable
from threading import Lock

from app.core.interfaces import AppStateProtocol, Reason

_instance: AppStateProtocol | None = None
_lock = Lock()


class AppState:
    """Singleton implementation of AppStateProtocol for managing application state."""

    def __init__(self) -> None:
        """Initialize AppState with no active project."""
        self._active_project: str | None = None
        self._subscribers: list[weakref.ref[Callable[[str | None, str | None, Reason], None]]] = []

    @property
    def active_project(self) -> str | None:
        """Currently active project slug, or None."""
        return self._active_project

    def set_active_project(self, slug: str | None, *, reason: Reason = "manual") -> None:
        """
        Set the active project and notify subscribers.

        Args:
            slug: Project slug to set as active, or None to clear
            reason: Reason for the change (manual, wizard-accept, project-switch, reset)
        """
        old_slug = self._active_project
        self._active_project = slug

        # Notify all subscribers, cleaning up dead references
        dead_refs = []
        for i, ref in enumerate(self._subscribers):
            callback = ref()
            if callback is None:
                dead_refs.append(i)
            else:
                # Ignore exceptions in callbacks to prevent one bad callback
                # from breaking all notifications
                with contextlib.suppress(Exception):
                    callback(slug, old_slug, reason)

        # Clean up dead references
        for i in reversed(dead_refs):
            del self._subscribers[i]

    def subscribe(
        self,
        callback: Callable[[str | None, str | None, Reason], None],
    ) -> Callable[[], None]:
        """
        Subscribe to project changes.

        Callback receives (new_slug, old_slug, reason).
        Returns an unsubscribe callable (disposer).

        Args:
            callback: Function to call when project changes

        Returns:
            Unsubscribe function that removes the callback
        """
        # Store weak reference to prevent memory leaks
        weak_callback = weakref.ref(callback)
        self._subscribers.append(weak_callback)

        def unsubscribe() -> None:
            """Remove the callback from subscribers."""
            # Find and remove the weak reference
            for i, ref in enumerate(self._subscribers):
                if ref() is callback:
                    del self._subscribers[i]
                    break

        return unsubscribe


def get_app_state() -> AppStateProtocol:
    """
    Get the singleton AppState instance.

    Thread-safe initialization ensures only one instance exists.

    Returns:
        The singleton AppState instance
    """
    global _instance
    if _instance is None:
        with _lock:
            # Double-check pattern for thread safety
            if _instance is None:
                _instance = AppState()
    return _instance
