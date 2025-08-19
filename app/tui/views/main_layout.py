"""Main layout view with three-pane structure."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from app.tui.widgets import CommandPalette, ContextPanel, FileTree, SessionViewer


class MainLayout:
    """Main three-pane layout for the application."""

    BINDINGS = [
        Binding(":", "command_palette", "Command Palette", priority=True),
        Binding("q", "quit", "Quit"),
    ]

    @staticmethod
    def compose() -> ComposeResult:
        """Compose the main three-pane layout."""
        yield Header()
        with Horizontal():
            yield FileTree()
            yield SessionViewer()
            yield ContextPanel()
        yield Footer()
        yield CommandPalette()

    @staticmethod
    def action_command_palette(app: object) -> None:
        """Show the command palette."""
        if hasattr(app, "query_one"):
            palette = app.query_one("#command-palette", CommandPalette)
            palette.show()
