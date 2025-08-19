"""Context panel widget for displaying relevant cards and information."""

from textual.containers import VerticalScroll
from textual.widgets import Static


class ContextPanel(VerticalScroll):
    """Right-side panel for context cards and relevant information."""

    DEFAULT_CSS = """
    ContextPanel {
        width: 35;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    .context-card {
        background: $panel;
        border: solid $primary-lighten-2;
        padding: 1;
        margin-bottom: 1;
    }
    """

    def __init__(self) -> None:
        """Initialize the context panel."""
        super().__init__(id="context-panel")

    def on_mount(self) -> None:
        """Add placeholder context cards."""
        self.mount(
            Static(
                "[bold]Current Stage[/bold]\n[dim]Capture[/dim]",
                classes="context-card",
            )
        )
        self.mount(
            Static(
                "[bold]Project Info[/bold]\n[dim]No project selected[/dim]",
                classes="context-card",
            )
        )
        self.mount(
            Static(
                "[bold]Recent Actions[/bold]\n[dim]• App started\n• Waiting for command[/dim]",
                classes="context-card",
            )
        )
