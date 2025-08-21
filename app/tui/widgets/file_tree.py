"""File tree widget for project navigation."""

from collections.abc import Callable
from pathlib import Path

from textual.widgets import Tree

from app.core.interfaces import Reason
from app.core.state import get_app_state
from app.files.project_meta import ProjectMeta


class FileTree(Tree[str]):
    """File tree for navigating project documents."""

    DEFAULT_CSS = """
    FileTree {
        width: 30;
        background: $surface;
        border: solid $primary;
    }
    """

    def __init__(self) -> None:
        """Initialize the file tree."""
        super().__init__("Projects", id="file-tree")
        self._disposer: Callable[[], None] | None = None
        self._current_project: str | None = None

    def on_mount(self) -> None:
        """Subscribe to AppState changes when mounted."""
        app_state = get_app_state()

        # Subscribe to project changes
        self._disposer = app_state.subscribe(self._on_project_changed)

        # Load initial project if one is active
        if app_state.active_project:
            self.refresh_tree(app_state.active_project)

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
                self.refresh_tree(new_slug)
            else:
                self._show_empty_state()

    def refresh_tree(self, slug: str) -> None:
        """Refresh the tree with actual project files.

        Args:
            slug: Project slug to display files for
        """
        self._current_project = slug

        # Clear existing tree
        self.root.remove_children()

        # Update root label
        project_data = ProjectMeta.read_project_yaml(slug)
        if project_data:
            project_title = project_data.get("title", slug)
            self.root.label = f"📁 {project_title}"
        else:
            self.root.label = f"📁 {slug}"

        self.root.expand()

        # Build tree from actual files
        project_path = Path("projects") / slug

        if not project_path.exists():
            self._show_empty_state()
            return

        # Known file structure
        files_to_check = [
            ("kernel.md", "📄 kernel.md"),
            ("outline.md", "📄 outline.md"),
            ("project.yaml", "⚙️ project.yaml"),
        ]

        # Add top-level files
        for filename, display_name in files_to_check:
            file_path = project_path / filename
            if file_path.exists():
                self.root.add_leaf(display_name)

        # Add directories if they exist and have content
        dirs_to_check = [
            ("elements", "📁 elements"),
            ("research", "📁 research"),
            ("exports", "📁 exports"),
        ]

        for dirname, display_name in dirs_to_check:
            dir_path = project_path / dirname
            if dir_path.exists() and dir_path.is_dir():
                # Check if directory has any files
                has_files = any(dir_path.iterdir())
                if has_files:
                    dir_node = self.root.add(display_name, expand=False)
                    # Add files in the directory
                    for file_path in sorted(dir_path.iterdir()):
                        if file_path.is_file():
                            file_icon = "📄" if file_path.suffix == ".md" else "📋"
                            dir_node.add_leaf(f"{file_icon} {file_path.name}")

        # If no files found, show empty state
        if not self.root.children:
            self.root.add_leaf("[dim]No files yet[/dim]")

    def _show_empty_state(self) -> None:
        """Show empty state when no project is selected."""
        self._current_project = None
        self.root.remove_children()
        self.root.label = "Projects"
        self.root.add_leaf("[dim]No project selected[/dim]")
