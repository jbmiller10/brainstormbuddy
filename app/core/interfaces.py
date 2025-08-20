"""Interface contracts for shared components.

This module defines protocol definitions and type contracts that all implementations must follow.
These are contracts only — no implementation logic.
"""

from collections.abc import Callable
from typing import Any, Literal, Protocol

# Type aliases for stage and reason
Stage = Literal["capture", "clarify", "kernel", "outline", "research", "synthesis"]
Reason = Literal["manual", "wizard-accept", "project-switch", "reset"]


class AppStateProtocol(Protocol):
    """Protocol for application state management with project switching."""

    @property
    def active_project(self) -> str | None:
        """Currently active project slug, or None."""
        ...

    def set_active_project(self, slug: str | None, *, reason: Reason = "manual") -> None:
        """Set the active project and notify subscribers."""
        ...

    def subscribe(
        self,
        callback: Callable[[str | None, str | None, Reason], None],
    ) -> Callable[[], None]:
        """
        Subscribe to project changes. Callback receives (new_slug, old_slug, reason).
        Returns an unsubscribe callable (disposer).
        """
        ...


# Module-level function signature that implementations should provide
def get_app_state() -> AppStateProtocol:
    """Get the singleton AppState instance."""
    raise NotImplementedError("This is a protocol definition only")


class ProjectMetaProtocol(Protocol):
    """Protocol for project metadata operations."""

    @staticmethod
    def read_project_yaml(slug: str) -> dict[str, Any] | None:
        """Read project.yaml for given slug. Returns None if invalid/missing."""
        ...

    @staticmethod
    def write_project_yaml(slug: str, data: dict[str, Any]) -> None:
        """Write project.yaml atomically."""
        ...

    @staticmethod
    def set_project_stage(slug: str, stage: Stage) -> bool:
        """Update project stage. Returns success status."""
        ...

    @staticmethod
    def validate_project_yaml(data: dict[str, Any]) -> bool:
        """
        Validate YAML has required fields:
        - slug: str   (machine-safe)
        - title: str  (human-friendly)
        - created: ISO timestamp
        - stage: Stage
        - description: str
        - tags: list[str]
        - metadata: {version: "1.0.0", format: "brainstormbuddy-project"}
        """
        ...


class OnboardingControllerProtocol(Protocol):
    """Protocol for onboarding orchestration logic."""

    def generate_clarify_questions(self, braindump: str, *, count: int = 5) -> list[str]:
        """Generate exactly `count` clarifying questions (default 5)."""
        ...

    def orchestrate_kernel_generation(self, braindump: str, answers_text: str) -> str:
        """Generate kernel.md content from braindump and a single consolidated answer string."""
        ...
