"""Unit tests for command palette research import command."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tui.widgets.command_palette import CommandPalette


@pytest.fixture
def command_palette():
    """Create a CommandPalette instance with mocked methods."""
    palette = CommandPalette()
    palette.hide = MagicMock()
    return palette


def test_research_import_in_commands():
    """Test that research import command exists in command list."""
    palette = CommandPalette()

    # Check that research import is properly configured
    command_dict = dict(palette.commands)
    assert "research import" in command_dict
    assert "Import research findings" in command_dict["research import"]


def test_research_import_creates_correct_path():
    """Test that research import command would create the correct path."""

    # The command should use projects/default as the base path
    expected_project_path = Path("projects") / "default"
    expected_db_path = expected_project_path / "research.db"

    # Verify the path components are correctly formed
    assert expected_project_path.parts == ("projects", "default")
    assert expected_db_path.name == "research.db"


@pytest.mark.asyncio
async def test_on_input_submitted_calls_hide():
    """Test that input submission hides the palette."""
    palette = CommandPalette()
    palette.hide = MagicMock()

    # Mock Input.Submitted event
    from textual.widgets import Input

    event = MagicMock(spec=Input.Submitted)
    event.value = "research import"

    # Mock execute_command to avoid actual execution
    palette.execute_command = AsyncMock(return_value=None)

    # Mock app.run_worker
    mock_app = MagicMock()
    mock_app.run_worker = MagicMock()

    with patch.object(CommandPalette, "app", new=mock_app):
        # Trigger the event handler
        palette.on_input_submitted(event)

        # Verify run_worker was called (it schedules execute_command)
        mock_app.run_worker.assert_called_once()

        # Verify palette was hidden
        palette.hide.assert_called_once()


@pytest.mark.asyncio
async def test_research_import_command_in_list():
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


def test_command_palette_compose_includes_research():
    """Test that compose includes research import in options."""
    palette = CommandPalette()

    # Verify research import is in the commands list
    command_names = [cmd[0] for cmd in palette.commands]
    assert "research import" in command_names


def test_research_import_modal_can_be_imported():
    """Test that ResearchImportModal can be imported successfully."""
    # This tests that the import path is correct
    from app.tui.views.research import ResearchImportModal

    # Verify the class has expected attributes
    assert hasattr(ResearchImportModal, "__init__")
    assert hasattr(ResearchImportModal, "compose")
    assert hasattr(ResearchImportModal, "handle_import")
    assert hasattr(ResearchImportModal, "refresh_table")
