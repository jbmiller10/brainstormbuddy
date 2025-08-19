"""Textual App for Brainstorm Buddy with three-pane layout."""

from textual.app import App, ComposeResult
from textual.binding import Binding

from app.tui.views import MainScreen
from app.tui.widgets import CommandPalette


class BrainstormBuddyApp(App[None]):
    """Main Textual application for Brainstorm Buddy."""

    TITLE = "Brainstorm Buddy"
    SUB_TITLE = "Terminal-first brainstorming app"
    CSS_PATH = None  # Use default CSS from widgets

    BINDINGS = [
        Binding(":", "command_palette", "Command", priority=True),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app with three-pane layout."""
        yield MainScreen()

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
