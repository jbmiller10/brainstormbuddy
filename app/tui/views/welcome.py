"""Welcome screen for project selection and creation."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, Static

from app.core.state import get_app_state
from app.files.project_meta import ProjectMeta


class WelcomeScreen(Screen[None]):
    """Welcome screen that lists existing projects and allows creating new ones."""

    DEFAULT_CSS = """
    WelcomeScreen {
        align: center middle;
    }

    WelcomeScreen .container {
        width: 80%;
        height: 80%;
        max-width: 100;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }

    WelcomeScreen .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    WelcomeScreen .subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    WelcomeScreen .project-list {
        height: 1fr;
        margin-bottom: 2;
        border: solid $primary;
    }

    WelcomeScreen .empty-state {
        align: center middle;
        height: 100%;
        color: $text-muted;
        text-align: center;
    }

    WelcomeScreen .button-container {
        height: 3;
        align: center middle;
    }

    WelcomeScreen Button {
        width: 24;
        margin: 0 1;
    }

    WelcomeScreen .create-button {
        background: $success;
    }
    """

    BINDINGS = [
        Binding("n", "create_project", "New Project", priority=True),
        Binding("enter", "select_project", "Select", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        """Initialize the welcome screen."""
        super().__init__()
        self.projects: list[dict[str, str]] = []

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
        """Scan projects directory and populate the list."""
        self.projects = self.find_projects()
        list_view = self.query_one("#project-list", ListView)
        list_view.clear()

        if self.projects:
            for project in self.projects:
                item = ListItem(
                    Static(
                        f"[bold]{project['title']}[/bold] ({project['slug']})\n"
                        f"[dim]{project.get('description', 'No description')}[/dim]"
                    ),
                    id=f"project-{project['slug']}",
                )
                list_view.append(item)
        else:
            list_view.append(
                ListItem(
                    Static(
                        "[dim italic]No projects found. Create your first project![/dim italic]"
                    ),
                    id="empty-state",
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

        for project_dir in project_base.iterdir():
            if not project_dir.is_dir():
                continue

            # Try to read project.yaml
            project_data = ProjectMeta.read_project_yaml(project_dir.name)
            if project_data:
                # Ensure we have the essential fields
                project_info = {
                    "slug": project_data.get("slug", project_dir.name),
                    "title": project_data.get("title", project_data.get("name", project_dir.name)),
                    "description": project_data.get("description", ""),
                    "stage": project_data.get("stage", "capture"),
                    "created": project_data.get("created", ""),
                }
                projects.append(project_info)

        # Sort by creation date (newest first)
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

    def action_select_project(self) -> None:
        """Select the currently highlighted project."""
        list_view = self.query_one("#project-list", ListView)
        if (
            list_view.highlighted_child
            and list_view.highlighted_child.id
            and list_view.highlighted_child.id != "empty-state"
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
