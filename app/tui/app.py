"""Textual App for Brainstorm Buddy with three-pane layout."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from app.tui.widgets import CommandPalette, ContextPanel, FileTree, SessionViewer


class BrainstormBuddyApp(App[None]):
    """Main Textual application for Brainstorm Buddy."""

    TITLE = "Brainstorm Buddy"
    SUB_TITLE = "Terminal-first brainstorming app"

    DEFAULT_CSS = """
    Screen {
        background: $surface;
    }

    Header {
        background: $primary;
    }

    Horizontal {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding(":", "command_palette", "Command", priority=True),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app with three-pane layout."""
        yield Header()
        with Horizontal():
            yield FileTree()
            yield SessionViewer()
            yield ContextPanel()
        yield Footer()
        yield CommandPalette()

    def action_command_palette(self) -> None:
        """Show the command palette."""
        palette = self.query_one("#command-palette", CommandPalette)
        palette.show()


def main() -> None:
    """Run the Brainstorm Buddy app."""
    app = BrainstormBuddyApp()
    app.run()


if __name__ == "__main__":
    main()
