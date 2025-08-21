"""Welcome screen for project selection and creation."""

import contextlib
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, Static

from app.core.state import get_app_state
from app.files.project_meta import ProjectMeta
from app.tui.styles import get_common_css


class WelcomeScreen(Screen[None]):
    """Welcome screen that lists existing projects and allows creating new ones."""

    # Use shared styles with some customizations
    DEFAULT_CSS = get_common_css("WelcomeScreen", center_align=True) + """
    WelcomeScreen Button {
        width: 24;  /* Wider buttons for welcome screen */
    }

    WelcomeScreen .container-medium {
        /* Use medium container for welcome screen */
    }
    """

    BINDINGS = [
        Binding("n", "create_project", "New Project", priority=True),
        Binding("enter", "select_project", "Select", show=False),
        Binding("m", "load_more", "Load More", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        """Initialize the welcome screen."""
        super().__init__()
        self.projects: list[dict[str, str]] = []
        self.displayed_count = 0
        self.page_size = 30  # Number of projects to display at once
        self.has_more = False

    def compose(self) -> ComposeResult:
        """Compose the welcome screen UI."""
        yield Header()
        with Container(classes="container"):
            yield Label("Welcome to Brainstorm Buddy", classes="title")
            yield Label("Select an existing project or create a new one", classes="subtitle")

            with VerticalScroll(classes="project-list"):
                yield ListView(id="project-list")

            with Horizontal(classes="button-container"):
                yield Button(
                    "Create New Project (N)",
                    variant="success",
                    classes="create-button",
                    id="create-project",
                )
        yield Footer()

    def on_mount(self) -> None:
        """Load projects when screen mounts."""
        self.refresh_projects()

    def refresh_projects(self) -> None:
        """Scan projects directory and populate the list with pagination."""
        self.projects = self.find_projects()
        list_view = self.query_one("#project-list", ListView)
        list_view.clear()
        self.displayed_count = 0

        if self.projects:
            # Display first page of projects
            self._display_page(list_view)
        else:
            list_view.append(
                ListItem(
                    Static(
                        "[dim italic]No projects found. Create your first project![/dim italic]"
                    ),
                    id="empty-state",
                )
            )

    def _display_page(self, list_view: ListView) -> None:
        """Display next page of projects."""
        start_idx = self.displayed_count
        end_idx = min(start_idx + self.page_size, len(self.projects))

        for idx in range(start_idx, end_idx):
            project = self.projects[idx]
            # Lazy load description - truncate if too long
            description = project.get('description', 'No description')
            if len(description) > 100:
                description = description[:97] + "..."

            item = ListItem(
                Static(
                    f"[bold]{project['title']}[/bold] ({project['slug']})\n"
                    f"[dim]{description}[/dim]"
                ),
                id=f"project-{project['slug']}",
            )
            list_view.append(item)

        self.displayed_count = end_idx
        self.has_more = self.displayed_count < len(self.projects)

        # Add "Load More" indicator if there are more projects
        if self.has_more:
            list_view.append(
                ListItem(
                    Static(
                        f"[dim italic]Showing {self.displayed_count} of {len(self.projects)} projects. "
                        f"Press 'M' to load more...[/dim italic]"
                    ),
                    id="load-more-indicator",
                )
            )

    def find_projects(self) -> list[dict[str, str]]:
        """
        Find all valid projects in the projects directory.

        Returns:
            List of project metadata dictionaries
        """
        projects: list[dict[str, str]] = []
        project_base = Path("projects")

        if not project_base.exists():
            return projects

        try:
            # Wrap directory iteration in try/except for race conditions
            for project_dir in project_base.iterdir():
                try:
                    if not project_dir.is_dir():
                        continue

                    # Try to read project.yaml
                    project_data = ProjectMeta.read_project_yaml(project_dir.name)
                    if project_data:
                        # Ensure we have the essential fields
                        project_info = {
                            "slug": project_data.get("slug", project_dir.name),
                            "title": project_data.get(
                                "title", project_data.get("name", project_dir.name)
                            ),
                            "description": project_data.get("description", ""),
                            "stage": project_data.get("stage", "capture"),
                            "created": project_data.get("created", ""),
                        }
                        projects.append(project_info)
                except (FileNotFoundError, PermissionError, OSError):
                    # Skip projects that disappear or become inaccessible during iteration
                    continue
        except (FileNotFoundError, PermissionError, OSError):
            # Handle case where projects directory itself becomes inaccessible
            return projects

        # Sort by creation date (newest first)
        with contextlib.suppress(Exception):
            # If sorting fails for any reason, just return unsorted
            projects.sort(key=lambda p: p.get("created", ""), reverse=True)

        return projects

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "create-project":
            self.action_create_project()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle project selection from list."""
        if event.item.id and event.item.id != "empty-state":
            # Extract slug from item ID (format: "project-{slug}")
            slug = event.item.id.replace("project-", "")
            self.select_project(slug)

    def action_create_project(self) -> None:
        """Navigate to new project wizard."""
        from app.tui.views.new_project_wizard import NewProjectWizard

        self.app.push_screen(NewProjectWizard())

    def action_load_more(self) -> None:
        """Load more projects if available."""
        if not self.has_more:
            return

        list_view = self.query_one("#project-list", ListView)

        # Remove the "Load More" indicator
        try:
            for item in list_view.children:
                if isinstance(item, ListItem) and item.id == "load-more-indicator":
                    item.remove()
                    break
        except Exception:
            pass

        # Display next page
        self._display_page(list_view)

        # Scroll to the newly added items
        list_view.scroll_end(animate=True)

    def action_select_project(self) -> None:
        """Select the currently highlighted project."""
        list_view = self.query_one("#project-list", ListView)
        if (
            list_view.highlighted_child
            and list_view.highlighted_child.id
            and list_view.highlighted_child.id not in ["empty-state", "load-more-indicator"]
        ):
            slug = list_view.highlighted_child.id.replace("project-", "")
            self.select_project(slug)

    def select_project(self, slug: str) -> None:
        """
        Set the active project and navigate to main screen.

        Args:
            slug: Project slug to activate
        """
        # Set active project in app state
        app_state = get_app_state()
        app_state.set_active_project(slug, reason="project-switch")

        # Navigate to main screen
        from app.tui.views.main_screen import MainScreen

        self.app.switch_screen(MainScreen())
