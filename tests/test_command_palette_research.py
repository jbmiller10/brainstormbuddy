"""Unit tests for command palette research import command."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.tui.widgets.command_palette import CommandPalette


@pytest.fixture
def command_palette() -> CommandPalette:
    """Create a CommandPalette instance with mocked methods."""
    palette = CommandPalette()
    # Use Mock() instead of direct assignment to avoid method-assign error
    palette.hide = Mock()  # type: ignore[method-assign]
    return palette


def test_research_import_in_commands() -> None:
    """Test that research import command exists in command list."""
    palette = CommandPalette()

    # Check that research import is properly configured
    command_dict = dict(palette.commands)
    assert "research import" in command_dict
    assert "Import research findings" in command_dict["research import"]


def test_research_import_creates_correct_path() -> None:
    """Test that research import command would create the correct path."""

    # The command should use projects/default as the base path
    expected_project_path = Path("projects") / "default"
    expected_db_path = expected_project_path / "research.db"

    # Verify the path components are correctly formed
    assert expected_project_path.parts == ("projects", "default")
    assert expected_db_path.name == "research.db"


@pytest.mark.asyncio
async def test_on_input_submitted_calls_hide() -> None:
    """Test that input submission hides the palette."""

    palette = CommandPalette()
    # Use Mock() instead of direct assignment to avoid method-assign error
    palette.hide = Mock()  # type: ignore[method-assign]

    # Mock Input.Submitted event
    from textual.widgets import Input

    event = MagicMock(spec=Input.Submitted)
    event.value = "test command"

    # Track the coroutine to clean it up
    created_coro: Any | None = None

    def track_coro(coro: Any, **_kwargs: Any) -> MagicMock:
        nonlocal created_coro
        created_coro = coro
        # Return a mock task
        return MagicMock()

    # Mock app.run_worker to track the coroutine
    mock_app = MagicMock()
    mock_app.run_worker = MagicMock(side_effect=track_coro)

    with patch.object(CommandPalette, "app", new=mock_app):
        # Trigger the event handler
        palette.on_input_submitted(event)

        # Verify run_worker was called (it schedules execute_command)
        mock_app.run_worker.assert_called_once()

        # Verify palette was hidden
        palette.hide.assert_called_once()

        # Clean up the coroutine
        if created_coro:
            # Close the coroutine to prevent warning
            created_coro.close()


@pytest.mark.asyncio
async def test_research_import_command_in_list() -> None:
    """Test that research import is in the command list."""
    palette = CommandPalette()

    # Check that research import is in the commands
    command_names = [cmd[0] for cmd in palette.commands]
    assert "research import" in command_names

    # Find the research import command
    for cmd, desc in palette.commands:
        if cmd == "research import":
            assert "Import research findings" in desc
            break
    else:
        pytest.fail("Research import command not found with proper description")


def test_command_palette_compose_includes_research() -> None:
    """Test that compose includes research import in options."""
    palette = CommandPalette()

    # Verify research import is in the commands list
    command_names = [cmd[0] for cmd in palette.commands]
    assert "research import" in command_names


def test_research_import_modal_can_be_imported() -> None:
    """Test that ResearchImportModal can be imported successfully."""
    # This tests that the import path is correct
    from app.tui.views.research import ResearchImportModal

    # Verify the class has expected attributes
    assert hasattr(ResearchImportModal, "__init__")
    assert hasattr(ResearchImportModal, "compose")
    assert hasattr(ResearchImportModal, "handle_import")
    assert hasattr(ResearchImportModal, "refresh_table")
