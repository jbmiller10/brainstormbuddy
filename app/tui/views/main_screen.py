"""Main screen view with three-pane structure."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Tree

from app.core.state import get_app_state
from app.tui.widgets import CommandPalette, ContextPanel, FileTree, SessionViewer


class MainScreen(Screen[None]):
    """Main three-pane screen for the application."""

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }

    Horizontal {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the main three-pane layout."""
        yield Header()
        with Horizontal():
            yield FileTree()
            yield SessionViewer()
            yield ContextPanel()
        yield Footer()
        yield CommandPalette()

    def show_command_palette(self) -> None:
        """Show the command palette overlay."""
        command_palette = self.query_one(CommandPalette)
        command_palette.show()

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        """Handle file selection in the tree."""
        if event.node.is_expanded:
            return  # Don't load content for directories

        # Extract filename from the node label
        label = str(event.node.label)
        if not label:
            return

        # Remove emoji prefix if present
        filename = label.split(" ", 1)[-1] if " " in label else label

        # Get current project
        app_state = get_app_state()
        if not app_state.active_project:
            return

        # Build file path
        project_path = Path("projects") / app_state.active_project
        file_path = project_path / filename

        # Read and display file content
        try:
            if file_path.exists() and file_path.is_file():
                content = file_path.read_text()
                session_viewer = self.query_one(SessionViewer)
                session_viewer.clear()
                session_viewer.write(f"[bold]{filename}[/bold]\n" + "=" * 40 + "\n\n")
                session_viewer.write(content)
        except Exception as e:
            session_viewer = self.query_one(SessionViewer)
            session_viewer.clear()
            session_viewer.write(f"[red]Error reading file: {e}[/red]")
