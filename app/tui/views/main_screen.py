"""Main screen view with three-pane structure."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header

from app.tui.widgets import CommandPalette, ContextPanel, FileTree, SessionViewer


class MainScreen(Screen[None]):
    """Main three-pane screen for the application."""

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }

    Horizontal {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the main three-pane layout."""
        yield Header()
        with Horizontal():
            yield FileTree()
            yield SessionViewer()
            yield ContextPanel()
        yield Footer()
        yield CommandPalette()
