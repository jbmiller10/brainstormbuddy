"""Session viewer widget for displaying editor content or Claude streams."""

from textual.widgets import RichLog


class SessionViewer(RichLog):
    """Main content viewer for editing documents or viewing session output."""

    DEFAULT_CSS = """
    SessionViewer {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    """

    def __init__(self) -> None:
        """Initialize the session viewer."""
        super().__init__(id="session-viewer", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        """Display welcome message on mount."""
        self.write("[bold cyan]Welcome to Brainstorm Buddy[/bold cyan]\n")
        self.write("\nA terminal-first brainstorming app that guides you through:\n")
        self.write("• [yellow]Capture[/yellow] → [yellow]Clarify[/yellow] → ")
        self.write("[yellow]Kernel[/yellow] → [yellow]Outline[/yellow] → ")
        self.write("[yellow]Research[/yellow] → [yellow]Synthesis[/yellow] → ")
        self.write("[yellow]Export[/yellow]\n")
        self.write("\n[dim]Press ':' to open the command palette[/dim]")
