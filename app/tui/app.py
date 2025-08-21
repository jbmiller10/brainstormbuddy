"""Textual App for Brainstorm Buddy with screen-based navigation."""

from textual.app import App
from textual.binding import Binding

from app.core.state import get_app_state
from app.tui.views.main_screen import MainScreen
from app.tui.views.welcome import WelcomeScreen


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
        Binding("ctrl+h", "go_home", "Home", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Initialize the app with the welcome screen."""
        from pathlib import Path

        # Check if there's already an active project
        app_state = get_app_state()
        if app_state.active_project:
            # Verify project still exists before navigation
            project_path = Path(f"projects/{app_state.active_project}")
            if project_path.exists() and (project_path / "project.yaml").exists():
                # Go directly to main screen if project is valid
                self.push_screen(MainScreen())
            else:
                # Clear orphaned active project
                app_state.set_active_project(None, reason="reset")
                # Show welcome screen for project selection
                self.push_screen(WelcomeScreen())
        else:
            # Show welcome screen for project selection
            self.push_screen(WelcomeScreen())

    def action_command_palette(self) -> None:
        """Show the command palette."""
        # Command palette is now per-screen
        if hasattr(self.screen, "show_command_palette"):
            self.screen.show_command_palette()

    def action_go_home(self) -> None:
        """Return to the welcome screen."""
        # Safely clear all screens and go back to welcome
        try:
            # Pop all screens except the base screen
            while len(self.screen_stack) > 1:
                self.pop_screen()
        except Exception:
            # If something goes wrong, just switch to welcome
            pass

        # Clear active project and switch to welcome screen
        app_state = get_app_state()
        if app_state.active_project:
            app_state.set_active_project(None, reason="reset")

        self.switch_screen(WelcomeScreen())


def main() -> None:
    """Run the Brainstorm Buddy app."""
    app = BrainstormBuddyApp()
    app.run()


if __name__ == "__main__":
    main()
