"""Context panel widget for displaying relevant cards and information."""

from collections.abc import Callable

from textual.containers import VerticalScroll
from textual.widgets import Static

from app.core.interfaces import Reason, Stage
from app.core.state import get_app_state
from app.files.project_meta import ProjectMeta


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

    # Stage to next action mapping
    STAGE_NEXT_ACTIONS: dict[Stage, str] = {
        "capture": "Run :clarify to refine your idea",
        "clarify": "Run :kernel to distill core concept",
        "kernel": "Run :workstreams to generate outline",
        "outline": "Run :research to gather findings",
        "research": "Run :synthesis to create final doc",
        "synthesis": "Run :export to generate deliverable",
    }

    def __init__(self) -> None:
        """Initialize the context panel."""
        super().__init__(id="context-panel")
        self._disposer: Callable[[], None] | None = None
        self._current_project: str | None = None
        # Store card references for updates
        self._stage_card: Static | None = None
        self._project_card: Static | None = None
        self._action_card: Static | None = None

    def on_mount(self) -> None:
        """Subscribe to AppState changes and create initial cards."""
        # Create initial cards
        self._stage_card = Static(
            "[bold]Current Stage[/bold]\n[dim]No project selected[/dim]",
            classes="context-card",
        )
        self._project_card = Static(
            "[bold]Project Info[/bold]\n[dim]No project selected[/dim]",
            classes="context-card",
        )
        self._action_card = Static(
            "[bold]Next Action[/bold]\n[dim]Select a project to begin[/dim]",
            classes="context-card",
        )

        self.mount(self._stage_card)
        self.mount(self._project_card)
        self.mount(self._action_card)

        # Subscribe to project changes
        app_state = get_app_state()
        self._disposer = app_state.subscribe(self._on_project_changed)

        # Load initial project if one is active
        if app_state.active_project:
            self.update_for_project(app_state.active_project)

    def on_unmount(self) -> None:
        """Clean up subscription when unmounted."""
        if self._disposer:
            self._disposer()
            self._disposer = None

    def _on_project_changed(
        self,
        new_slug: str | None,
        old_slug: str | None,  # noqa: ARG002
        reason: Reason,  # noqa: ARG002
    ) -> None:
        """Handle project change notifications."""
        if new_slug != self._current_project:
            if new_slug:
                self.update_for_project(new_slug)
            else:
                self._show_empty_state()

    def update_for_project(self, slug: str) -> None:
        """Update context panel for the specified project.

        Args:
            slug: Project slug to display context for
        """
        self._current_project = slug

        # Read project metadata
        project_data = ProjectMeta.read_project_yaml(slug)

        if not project_data:
            # Project exists but no metadata
            if self._project_card:
                self._project_card.update(
                    f"[bold]Project Info[/bold]\n"
                    f"[yellow]Project: {slug}[/yellow]\n"
                    f"[dim]No project.yaml found[/dim]"
                )
            if self._stage_card:
                self._stage_card.update("[bold]Current Stage[/bold]\n[dim]Unknown[/dim]")
            if self._action_card:
                self._action_card.update(
                    "[bold]Next Action[/bold]\n[dim]Create project.yaml first[/dim]"
                )
            return

        # Update project info card
        title = project_data.get("title", slug)
        description = project_data.get("description", "No description")
        if len(description) > 100:
            description = description[:97] + "..."

        if self._project_card:
            self._project_card.update(
                f"[bold]Project Info[/bold]\n[cyan]{title}[/cyan]\n[dim]{description}[/dim]"
            )

        # Update stage card
        stage = project_data.get("stage", "capture")
        stage_display = stage.title() if isinstance(stage, str) else "Unknown"

        if self._stage_card:
            self._stage_card.update(f"[bold]Current Stage[/bold]\n[green]{stage_display}[/green]")

        # Update next action card
        next_action = self.STAGE_NEXT_ACTIONS.get(stage, "Review project status")

        if self._action_card:
            self._action_card.update(f"[bold]Next Action[/bold]\n[yellow]{next_action}[/yellow]")

    def _show_empty_state(self) -> None:
        """Show empty state when no project is selected."""
        self._current_project = None

        if self._stage_card:
            self._stage_card.update("[bold]Current Stage[/bold]\n[dim]No project selected[/dim]")
        if self._project_card:
            self._project_card.update("[bold]Project Info[/bold]\n[dim]No project selected[/dim]")
        if self._action_card:
            self._action_card.update(
                "[bold]Next Action[/bold]\n[dim]Select a project to begin[/dim]"
            )
