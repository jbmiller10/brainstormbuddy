"""Modal widget for approving kernel changes with diff preview."""

from typing import Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class KernelApprovalModal(ModalScreen[bool]):
    """Modal for reviewing and approving kernel changes."""

    DEFAULT_CSS = """
    KernelApprovalModal {
        align: center middle;
    }

    KernelApprovalModal > Container {
        background: $surface;
        width: 90%;
        height: 80%;
        border: thick $primary;
        padding: 1;
    }

    KernelApprovalModal .diff-container {
        height: 1fr;
        margin-bottom: 1;
        border: solid $primary;
        padding: 1;
    }

    KernelApprovalModal .button-container {
        height: 3;
        align: center middle;
    }

    KernelApprovalModal Button {
        margin: 0 1;
        width: 16;
    }

    KernelApprovalModal .accept-button {
        background: $success;
    }

    KernelApprovalModal .reject-button {
        background: $warning;
    }
    """

    BINDINGS = [
        Binding("y", "accept", "Accept", priority=True),
        Binding("n", "reject", "Reject", priority=True),
        Binding("escape", "reject", "Cancel"),
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
                    "Accept (Y)",
                    variant="success",
                    classes="accept-button",
                    id="accept",
                )
                yield Button(
                    "Reject (N)",
                    variant="warning",
                    classes="reject-button",
                    id="reject",
                )

    def action_accept(self) -> None:
        """Accept the changes."""
        self.dismiss(True)

    def action_reject(self) -> None:
        """Reject the changes."""
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "accept":
            self.action_accept()
        elif event.button.id == "reject":
            self.action_reject()
