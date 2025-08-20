"""Tests for interface protocols to verify they can be properly implemented."""

from collections.abc import Callable
from typing import Any

from app.core.interfaces import (
    AppStateProtocol,
    OnboardingControllerProtocol,
    ProjectMetaProtocol,
    Reason,
    Stage,
)


class MockAppState:
    """Mock implementation of AppStateProtocol for testing."""

    def __init__(self) -> None:
        self._active_project: str | None = None
        self._subscribers: list[Callable[[str | None, str | None, Reason], None]] = []

    @property
    def active_project(self) -> str | None:
        """Currently active project slug, or None."""
        return self._active_project

    def set_active_project(self, slug: str | None, *, reason: Reason = "manual") -> None:
        """Set the active project and notify subscribers."""
        old_slug = self._active_project
        self._active_project = slug
        for callback in self._subscribers:
            callback(slug, old_slug, reason)

    def subscribe(
        self,
        callback: Callable[[str | None, str | None, Reason], None],
    ) -> Callable[[], None]:
        """
        Subscribe to project changes. Callback receives (new_slug, old_slug, reason).
        Returns an unsubscribe callable (disposer).
        """
        self._subscribers.append(callback)

        def unsubscribe() -> None:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

        return unsubscribe


class MockProjectMeta:
    """Mock implementation of ProjectMetaProtocol for testing."""

    @staticmethod
    def read_project_yaml(slug: str) -> dict[str, Any] | None:
        """Read project.yaml for given slug. Returns None if invalid/missing."""
        if slug == "test-project":
            return {
                "slug": slug,
                "title": "Test Project",
                "created": "2024-01-01T00:00:00Z",
                "stage": "capture",
                "description": "Test description",
                "tags": ["test"],
                "metadata": {"version": "1.0.0", "format": "brainstormbuddy-project"},
            }
        return None

    @staticmethod
    def write_project_yaml(slug: str, data: dict[str, Any]) -> None:
        """Write project.yaml atomically."""
        # Mock implementation - just validate structure
        _ = slug  # Acknowledge parameter for protocol compliance
        assert "slug" in data
        assert "title" in data

    @staticmethod
    def set_project_stage(slug: str, stage: Stage) -> bool:
        """Update project stage. Returns success status."""
        _ = slug  # Acknowledge parameter for protocol compliance
        valid_stages: set[Stage] = {
            "capture",
            "clarify",
            "kernel",
            "outline",
            "research",
            "synthesis",
        }
        return stage in valid_stages

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
        required_fields = {"slug", "title", "created", "stage", "description", "tags", "metadata"}
        return all(field in data for field in required_fields)


class MockOnboardingController:
    """Mock implementation of OnboardingControllerProtocol for testing."""

    def generate_clarify_questions(self, braindump: str, *, count: int = 5) -> list[str]:
        """Generate exactly `count` clarifying questions (default 5)."""
        return [f"Question {i + 1} about: {braindump[:20]}..." for i in range(count)]

    def orchestrate_kernel_generation(self, braindump: str, answers_text: str) -> str:
        """Generate kernel.md content from braindump and a single consolidated answer string."""
        return f"""# Kernel

## Core Concept
Based on: {braindump[:30]}...

## Key Questions
From answers: {answers_text[:30]}...

## Success Criteria
- Criteria 1
- Criteria 2

## Constraints
- Constraint 1
- Constraint 2

## Primary Value Proposition
Value prop here."""


def test_appstate_protocol_implementation() -> None:
    """Test that MockAppState properly implements AppStateProtocol."""
    mock = MockAppState()

    # Test it satisfies the protocol by using it
    assert mock.active_project is None

    # Test setting project
    mock.set_active_project("test-project", reason="manual")
    assert mock.active_project == "test-project"

    # Test subscription
    callback_called = False
    received_args: tuple[str | None, str | None, Reason] | None = None

    def callback(new: str | None, old: str | None, reason: Reason) -> None:
        nonlocal callback_called, received_args
        callback_called = True
        received_args = (new, old, reason)

    unsubscribe = mock.subscribe(callback)
    mock.set_active_project("new-project", reason="wizard-accept")

    assert callback_called
    assert received_args == ("new-project", "test-project", "wizard-accept")

    # Test unsubscribe
    callback_called = False
    unsubscribe()
    mock.set_active_project("another-project")
    assert not callback_called


def test_projectmeta_protocol_implementation() -> None:
    """Test that MockProjectMeta properly implements ProjectMetaProtocol."""
    # Test read
    data = MockProjectMeta.read_project_yaml("test-project")
    assert data is not None
    assert data["slug"] == "test-project"
    assert data["title"] == "Test Project"

    # Test validation
    assert MockProjectMeta.validate_project_yaml(data)

    # Test invalid data
    invalid_data = {"slug": "test"}
    assert not MockProjectMeta.validate_project_yaml(invalid_data)

    # Test write (mock just validates)
    MockProjectMeta.write_project_yaml("test", {"slug": "test", "title": "Test"})

    # Test set stage
    assert MockProjectMeta.set_project_stage("test", "kernel")
    assert not MockProjectMeta.set_project_stage("test", "invalid")  # type: ignore


def test_onboarding_controller_protocol_implementation() -> None:
    """Test that MockOnboardingController properly implements OnboardingControllerProtocol."""
    controller = MockOnboardingController()

    # Test question generation with default count
    questions = controller.generate_clarify_questions("This is my braindump")
    assert len(questions) == 5
    assert all("Question" in q for q in questions)

    # Test question generation with custom count
    questions = controller.generate_clarify_questions("Another braindump", count=3)
    assert len(questions) == 3

    # Test kernel generation
    kernel = controller.orchestrate_kernel_generation(
        "My braindump text", "My consolidated answers"
    )
    assert "# Kernel" in kernel
    assert "Core Concept" in kernel
    assert "Key Questions" in kernel
    assert "Success Criteria" in kernel
    assert "Constraints" in kernel
    assert "Primary Value Proposition" in kernel


def test_stage_type_alias() -> None:
    """Test that Stage type alias works correctly."""
    valid_stages: list[Stage] = ["capture", "clarify", "kernel", "outline", "research", "synthesis"]

    for stage in valid_stages:
        # This should type check correctly
        current_stage: Stage = stage
        assert current_stage in valid_stages


def test_reason_type_alias() -> None:
    """Test that Reason type alias works correctly."""
    valid_reasons: list[Reason] = ["manual", "wizard-accept", "project-switch", "reset"]

    for reason in valid_reasons:
        # This should type check correctly
        current_reason: Reason = reason
        assert current_reason in valid_reasons


def test_protocol_type_checking() -> None:
    """Verify that protocol implementations satisfy type checking."""
    # These should satisfy the protocol types
    app_state: AppStateProtocol = MockAppState()
    project_meta: type[ProjectMetaProtocol] = MockProjectMeta
    controller: OnboardingControllerProtocol = MockOnboardingController()

    # Basic smoke test that they work
    assert app_state.active_project is None
    assert project_meta.read_project_yaml("test-project") is not None
    assert len(controller.generate_clarify_questions("test")) == 5
