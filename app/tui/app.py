"""Minimal Textual App for Brainstorm Buddy."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static


class BrainstormBuddyApp(App):
    """Main Textual application for Brainstorm Buddy."""

    TITLE = "Brainstorm Buddy"
    SUB_TITLE = "Terminal-first brainstorming app"

    def compose(self) -> ComposeResult:
        """Compose the app with placeholder widgets."""
        yield Header()
        yield Static("Welcome to Brainstorm Buddy!", id="placeholder")
        yield Footer()


def main() -> None:
    """Run the Brainstorm Buddy app."""
    app = BrainstormBuddyApp()
    app.run()


if __name__ == "__main__":
    main()