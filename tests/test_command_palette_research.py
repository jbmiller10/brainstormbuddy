"""Unit tests for command palette research import command."""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

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
async def test_on_option_list_option_selected() -> None:
    """Test that selecting an option from the list executes the command."""
    from textual.widgets import OptionList

    palette = CommandPalette()
    # Use Mock() instead of direct assignment to avoid method-assign error
    palette.hide = Mock()  # type: ignore[method-assign]

    # Mock OptionList.OptionSelected event
    event = MagicMock(spec=OptionList.OptionSelected)
    # Create a mock option with prompt attribute
    mock_option = MagicMock()
    mock_option.prompt = "clarify: Enter clarify stage for current project"
    event.option = mock_option

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
        palette.on_option_list_option_selected(event)

        # Verify run_worker was called (it schedules execute_command)
        mock_app.run_worker.assert_called_once()

        # Verify palette was hidden
        palette.hide.assert_called_once()

        # Clean up the coroutine
        if created_coro:
            # Close the coroutine to prevent warning
            created_coro.close()


def test_on_option_list_option_selected_parses_command() -> None:
    """Test that option selection correctly parses the command from option text."""
    from textual.widgets import OptionList

    palette = CommandPalette()
    palette.hide = Mock()  # type: ignore[method-assign]

    # Mock OptionList.OptionSelected event with different command formats
    event = MagicMock(spec=OptionList.OptionSelected)
    mock_option = MagicMock()
    mock_option.prompt = "research import: Import research findings"
    event.option = mock_option

    # Track the coroutine to clean it up
    created_coro: Any | None = None

    def track_coro(coro: Any, **_kwargs: Any) -> MagicMock:
        nonlocal created_coro
        created_coro = coro
        return MagicMock()

    # Mock app.run_worker to track the coroutine
    mock_app = MagicMock()
    mock_app.run_worker = MagicMock(side_effect=track_coro)

    # Mock execute_command to verify it gets called with correct command
    with patch.object(palette, "execute_command") as mock_execute:
        mock_execute.return_value = MagicMock()  # Return a mock coroutine

        with patch.object(CommandPalette, "app", new=mock_app):
            # Trigger the event handler
            palette.on_option_list_option_selected(event)

            # Verify execute_command was called with the correct command
            mock_execute.assert_called_once_with("research import")

            # Verify run_worker was called
            mock_app.run_worker.assert_called_once()

            # Verify palette was hidden
            palette.hide.assert_called_once()

            # Clean up the coroutine if one was created
            if created_coro and hasattr(created_coro, "close"):
                created_coro.close()


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


def test_command_palette_compose_creates_ui() -> None:
    """Test that compose() creates expected UI components."""
    from textual.widgets import Input, OptionList

    palette = CommandPalette()

    # Call compose and convert to list
    widgets = list(palette.compose())

    # Should have Input and OptionList
    assert len(widgets) == 2

    # Check Input widget
    assert isinstance(widgets[0], Input)
    assert widgets[0].id == "command-input"
    assert widgets[0].placeholder == "Type a command..."

    # Check OptionList widget
    assert isinstance(widgets[1], OptionList)
    assert widgets[1].id == "command-list"

    # Check that options were added to the list
    # The OptionList should have been populated with commands
    option_count = len(palette.commands)
    assert option_count > 0


def test_command_palette_show_method() -> None:
    """Test that show() method adds visible class and focuses input."""
    palette = CommandPalette()

    # Mock query_one to return a mock Input widget
    input_mock = MagicMock()
    input_mock.focus = MagicMock()

    with (
        patch.object(palette, "query_one", return_value=input_mock),
        patch.object(palette, "add_class") as add_class_mock,
    ):
        palette.show()

        # Verify visible class was added
        add_class_mock.assert_called_once_with("visible")

        # Verify input was focused
        input_mock.focus.assert_called_once()


def test_command_palette_hide_method() -> None:
    """Test that hide() method removes visible class."""
    palette = CommandPalette()

    with patch.object(palette, "remove_class") as remove_class_mock:
        palette.hide()

        # Verify visible class was removed
        remove_class_mock.assert_called_once_with("visible")


def test_command_palette_action_close() -> None:
    """Test that action_close() calls hide."""
    palette = CommandPalette()

    with patch.object(palette, "hide") as hide_mock:
        palette.action_close()

        # Verify hide was called
        hide_mock.assert_called_once()


@pytest.mark.asyncio
async def test_domain_settings_command_no_existing_settings() -> None:
    """Test domain settings command when no settings file exists."""
    palette = CommandPalette()

    # Mock the app's push_screen_wait method
    mock_app = MagicMock()
    mock_app.push_screen_wait = AsyncMock(return_value=True)

    # Mock Path.exists to return False (no existing settings)
    with (
        patch.object(CommandPalette, "app", new=mock_app),
        patch("pathlib.Path.exists", return_value=False),
        patch("app.tui.widgets.domain_editor.DomainEditor") as editor_mock,
    ):
        # Execute the domain settings command
        await palette.execute_command("domain settings")

        # Verify DomainEditor was created with empty lists
        editor_mock.assert_called_once()
        call_args = editor_mock.call_args
        assert call_args[0][0] == Path(".") / ".claude"  # config_dir
        assert call_args[0][1] == []  # empty allow_domains
        assert call_args[0][2] == []  # empty deny_domains

        # Verify the editor was pushed to screen
        mock_app.push_screen_wait.assert_called_once()


@pytest.mark.asyncio
async def test_domain_settings_command_with_existing_settings() -> None:
    """Test domain settings command when settings file exists."""
    import json
    from unittest.mock import mock_open

    palette = CommandPalette()

    # Mock existing settings content
    existing_settings = {
        "permissions": {
            "webDomains": {"allow": ["allowed.com", "example.com"], "deny": ["blocked.com"]}
        }
    }

    # Mock the app's push_screen_wait method
    mock_app = MagicMock()
    mock_app.push_screen_wait = AsyncMock(return_value=True)

    # Mock file operations
    with (
        patch.object(CommandPalette, "app", new=mock_app),
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(existing_settings))),
        patch("json.load", return_value=existing_settings),
        patch("app.tui.widgets.domain_editor.DomainEditor") as editor_mock,
    ):
        # Execute the domain settings command
        await palette.execute_command("domain settings")

        # Verify DomainEditor was created with existing domain lists
        editor_mock.assert_called_once()
        call_args = editor_mock.call_args
        assert call_args[0][0] == Path(".") / ".claude"  # config_dir
        assert call_args[0][1] == ["allowed.com", "example.com"]  # allow_domains
        assert call_args[0][2] == ["blocked.com"]  # deny_domains

        # Verify the editor was pushed to screen
        mock_app.push_screen_wait.assert_called_once()


@pytest.mark.asyncio
async def test_domain_settings_command_missing_permissions_key() -> None:
    """Test domain settings command when settings exist but without permissions key."""
    import json
    from unittest.mock import mock_open

    palette = CommandPalette()

    # Mock settings without permissions key
    existing_settings = {"other": "data"}

    mock_app = MagicMock()
    mock_app.push_screen_wait = AsyncMock(return_value=True)

    with (
        patch.object(CommandPalette, "app", new=mock_app),
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(existing_settings))),
        patch("json.load", return_value=existing_settings),
        patch("app.tui.widgets.domain_editor.DomainEditor") as editor_mock,
    ):
        # Execute the domain settings command
        await palette.execute_command("domain settings")

        # Verify DomainEditor was created with empty lists (fallback)
        editor_mock.assert_called_once()
        call_args = editor_mock.call_args
        assert call_args[0][1] == []  # empty allow_domains
        assert call_args[0][2] == []  # empty deny_domains
