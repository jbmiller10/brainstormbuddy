"""Modal widget for approving kernel changes with diff preview."""

from typing import Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from app.tui.styles import get_modal_css


class KernelApprovalModal(ModalScreen[str | None]):
    """Modal for reviewing and approving kernel changes.

    Returns:
        "accept" - User accepts the kernel
        "clarify" - User wants to provide feedback and refine
        "restart" - User wants to start over from the beginning
        None - User cancelled the modal (ESC key)
    """

    # Use shared modal styles
    DEFAULT_CSS = get_modal_css("KernelApprovalModal")

    BINDINGS = [
        Binding("a", "accept", "Accept", priority=True),
        Binding("c", "clarify", "Clarify", priority=True),
        Binding("r", "restart", "Start Over", priority=True),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        diff_content: str,
        project_slug: str,
        mode: Literal["diff", "proposal"] = "diff",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Initialize the kernel approval modal.

        Args:
            diff_content: The diff preview or proposal content to display
            project_slug: The project identifier
            mode: Display mode - "diff" for diff preview, "proposal" for full content
            name: Optional widget name
            id: Optional widget ID
            classes: Optional CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.diff_content = diff_content
        self.project_slug = project_slug
        self.mode = mode

        # Un-fence content if it's wrapped in code fences
        if mode == "proposal" and self.diff_content.strip().startswith("```"):
            lines = self.diff_content.strip().split("\n")
            if lines[0].startswith("```") and lines[-1] == "```":
                # Remove first and last lines (fences)
                self.diff_content = "\n".join(lines[1:-1])

    def compose(self) -> ComposeResult:
        """Compose the modal UI."""
        with Container():
            if self.mode == "proposal":
                yield Label(f"[bold]Kernel Proposal for Project: {self.project_slug}[/bold]")
                yield Label("[dim]Review the kernel proposal below and approve or reject[/dim]")
            else:
                yield Label(f"[bold]Kernel Changes for Project: {self.project_slug}[/bold]")
                yield Label("[dim]Review the changes below and approve or reject[/dim]")

            with ScrollableContainer(classes="diff-container"):
                yield Static(self.diff_content, markup=False)

            with Horizontal(classes="button-container"):
                yield Button(
                    "Accept (A)",
                    variant="success",
                    classes="accept-button",
                    id="accept",
                )
                yield Button(
                    "Clarify (C)",
                    variant="warning",
                    classes="clarify-button",
                    id="clarify",
                )
                yield Button(
                    "Start Over (R)",
                    variant="error",
                    classes="restart-button",
                    id="restart",
                )

    def action_accept(self) -> None:
        """Accept the changes."""
        self.dismiss("accept")

    def action_clarify(self) -> None:
        """Request clarification or refinement."""
        self.dismiss("clarify")

    def action_restart(self) -> None:
        """Start over from the beginning."""
        self.dismiss("restart")

    def action_cancel(self) -> None:
        """Cancel the modal without making a decision."""
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "accept":
            self.action_accept()
        elif event.button.id == "clarify":
            self.action_clarify()
        elif event.button.id == "restart":
            self.action_restart()
