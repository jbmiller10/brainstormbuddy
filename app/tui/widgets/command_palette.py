"""Command palette widget for executing app commands."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, OptionList


class CommandPalette(Container):
    """Command palette overlay for executing commands."""

    DEFAULT_CSS = """
    CommandPalette {
        layer: modal;
        align: center middle;
        width: 60;
        height: auto;
        max-height: 20;
        background: $panel;
        border: thick $primary;
        padding: 1;
        display: none;
    }

    CommandPalette.visible {
        display: block;
    }

    CommandPalette Input {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close palette"),
    ]

    def __init__(self) -> None:
        """Initialize the command palette."""
        super().__init__(id="command-palette")
        self.commands = [
            ("new project", "Create a new brainstorming project"),
            ("clarify", "Enter clarify stage for current project"),
            ("kernel", "Define the kernel of your idea"),
            ("outline", "Create workstream outline"),
            ("generate workstreams", "Generate outline and element documents"),
            ("research import", "Import research findings"),
            ("synthesis", "Synthesize findings into final output"),
            ("export", "Export project to various formats"),
        ]

    def compose(self) -> ComposeResult:
        """Compose the command palette UI."""
        yield Input(placeholder="Type a command...", id="command-input")
        options = [f"{cmd}: {desc}" for cmd, desc in self.commands]
        yield OptionList(*options, id="command-list")

    def show(self) -> None:
        """Show the command palette."""
        self.add_class("visible")
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

    def hide(self) -> None:
        """Hide the command palette."""
        self.remove_class("visible")

    def action_close(self) -> None:
        """Close the command palette."""
        self.hide()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        command = event.value.lower().strip()
        self.execute_command(command)
        self.hide()

    def execute_command(self, command: str) -> None:
        """Execute the selected command."""
        from textual import log

        log(f"Executing command: {command}")

        # Import here to avoid circular imports
        from app.tui.views.session import SessionController
        from app.tui.widgets.session_viewer import SessionViewer

        # Get the session viewer from the main screen
        viewer = self.app.query_one("#session-viewer", SessionViewer)

        # Create controller
        controller = SessionController(viewer)

        # Handle clarify command
        if command == "clarify":
            # Run the async task using Textual's worker system
            self.app.run_worker(controller.start_clarify_session(), exclusive=True)

        # Handle kernel command
        elif command == "kernel":
            # For now, use a default project slug - in production, this would prompt for it
            project_slug = "default-project"
            initial_idea = "Build a better brainstorming app"

            # Run the async task using Textual's worker system
            self.app.run_worker(
                controller.start_kernel_session(project_slug, initial_idea), exclusive=True
            )

        # Handle generate workstreams command
        elif command == "generate workstreams":
            # Run the async task using Textual's worker system
            self.app.run_worker(controller.generate_workstreams(), exclusive=True)
