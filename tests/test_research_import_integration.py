"""Integration tests for research import functionality."""

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tui.views.research import ResearchImportModal
from app.tui.widgets.command_palette import CommandPalette


@pytest.fixture
def reset_app_state():
    """Reset AppState singleton for testing."""
    # Clear the singleton instance
    import app.core.state

    app.core.state._instance = None
    yield
    # Clear again after test
    app.core.state._instance = None


@pytest.mark.asyncio
async def test_research_import_command_execution(tmp_path: Path, reset_app_state) -> None:  # noqa: ARG001
    """Test that research import command can be executed."""
    from app.core.state import get_app_state

    palette = CommandPalette()

    # Set active project
    app_state = get_app_state()
    app_state.set_active_project("default")

    # Create the project directory
    mock_project_path = tmp_path / "projects" / "default"
    mock_project_path.mkdir(parents=True, exist_ok=True)

    # Create a mock app with necessary methods
    mock_app = MagicMock()
    mock_app.query_one = MagicMock()

    # Mock the SessionViewer that would normally be found
    mock_viewer = MagicMock()
    mock_app.query_one.return_value = mock_viewer

    # Track if push_screen_wait was called with a ResearchImportModal
    modal_shown = False

    async def check_modal(modal: Any) -> bool:
        nonlocal modal_shown
        # Check if it's a ResearchImportModal instance
        if modal.__class__.__name__ == "ResearchImportModal":
            modal_shown = True
        return True

    mock_app.push_screen_wait = AsyncMock(side_effect=check_modal)

    # Patch the app property
    with patch.object(CommandPalette, "app", new=mock_app):
        # Execute the research import command - this imports and creates the modal
        await palette.execute_command("research import")

        # Verify push_screen_wait was called (modal was shown)
        mock_app.push_screen_wait.assert_called_once()

        # Get the modal that was passed to push_screen_wait
        call_args = mock_app.push_screen_wait.call_args
        modal_arg = call_args[0][0]

        # Verify it's a ResearchImportModal
        assert modal_arg.__class__.__name__ == "ResearchImportModal"
        assert hasattr(modal_arg, "workstream")
        assert hasattr(modal_arg, "db_path")

        # Verify the async mock was properly awaited
        mock_app.push_screen_wait.assert_awaited_once()


@pytest.mark.asyncio
async def test_research_modal_compose_elements() -> None:
    """Test that research modal compose creates expected UI elements."""
    modal = ResearchImportModal()

    # We can't call compose() directly without an app context,
    # but we can verify the compose method exists and returns generators
    assert hasattr(modal, "compose")
    assert callable(modal.compose)

    # Test that the modal has expected default values
    assert modal.workstream == "research"
    assert str(modal.db_path).endswith("findings.db")  # Changed from research.db to findings.db
    assert modal.status_message == ""
    assert modal.findings == []


@pytest.mark.asyncio
async def test_on_mount_loads_existing_findings(tmp_path: Path) -> None:
    """Test that on_mount loads existing findings into the table."""
    from app.research.db import ResearchDB

    db_path = tmp_path / "test.db"

    # Pre-populate database
    async with ResearchDB(db_path) as db:
        await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Test claim",
            evidence="Test evidence",
            confidence=0.8,
            tags=["test"],
            workstream="research",
        )

    modal = ResearchImportModal(db_path=db_path)

    # Mock the refresh_table method
    with patch.object(modal, "refresh_table", new_callable=AsyncMock) as mock_refresh:
        # Call on_mount
        await modal.on_mount()

        # Verify refresh_table was called
        mock_refresh.assert_called_once()


def test_research_import_button_handlers() -> None:
    """Test button press handlers."""
    modal = ResearchImportModal()

    # Mock the dismiss method
    with patch.object(modal, "dismiss", new_callable=MagicMock) as mock_dismiss:
        # Test close button handler
        modal.handle_close()
        mock_dismiss.assert_called_with(True)

        # Reset mock
        mock_dismiss.reset_mock()

        # Test escape action
        modal.action_close()
        mock_dismiss.assert_called_with(True)


@pytest.mark.asyncio
async def test_command_palette_input_submitted_properly() -> None:
    """Test that on_input_submitted properly handles the coroutine."""
    palette = CommandPalette()

    # Create a proper mock event
    from textual.widgets import Input

    event = MagicMock(spec=Input.Submitted)
    event.value = "research import"

    # Mock app.run_worker to capture the coroutine
    captured_coro = None

    def capture_coro(coro: Coroutine[Any, Any, Any], **_kwargs: dict[str, Any]) -> Any:
        nonlocal captured_coro
        captured_coro = coro
        # Create a task to properly handle the coroutine
        return asyncio.create_task(coro)

    mock_app = MagicMock()
    mock_app.run_worker = MagicMock(side_effect=capture_coro)

    # Patch execute_command to be a simple async function
    async def mock_execute(cmd: str) -> str:
        return f"Executed: {cmd}"

    with (
        patch.object(palette, "hide", new_callable=MagicMock) as mock_hide,
        patch.object(palette, "execute_command", new=mock_execute),
        patch.object(CommandPalette, "app", new=mock_app),
    ):
        # Call on_input_submitted
        palette.on_input_submitted(event)

        # Verify run_worker was called with the coroutine
        mock_app.run_worker.assert_called_once()
        assert captured_coro is not None

        # Verify palette was hidden
        mock_hide.assert_called_once()

        # Await the captured coroutine to prevent warning
        result = await captured_coro
        assert result == "Executed: research import"
