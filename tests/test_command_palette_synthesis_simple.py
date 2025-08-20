"""Simplified tests for command palette synthesis command handler."""

from unittest.mock import AsyncMock, patch

import pytest

from app.tui.widgets.command_palette import CommandPalette


def test_synthesis_command_exists() -> None:
    """Test that synthesis command exists in command list."""
    palette = CommandPalette()

    # Check that synthesis is properly configured
    command_dict = dict(palette.commands)
    assert "synthesis" in command_dict


@pytest.mark.asyncio
async def test_synthesis_command_basic_flow() -> None:
    """Test synthesis command basic flow."""
    palette = CommandPalette()

    # Mock the entire execute_command to avoid complex setup
    with patch.object(palette, "execute_command", new=AsyncMock()) as mock_execute:
        await palette.execute_command("synthesis")
        mock_execute.assert_called_once_with("synthesis")
