"""File tree widget for project navigation."""

from textual.widgets import Tree


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
        """Initialize the file tree with placeholder content."""
        super().__init__("Projects", id="file-tree")

    def on_mount(self) -> None:
        """Populate the tree with placeholder project structure."""
        root = self.root
        root.expand()

        # Add placeholder project structure
        project1 = root.add("📁 example-project", expand=False)
        project1.add_leaf("📄 kernel.md")
        project1.add_leaf("📄 outline.md")
        project1.add_leaf("📄 project.yaml")

        elements = project1.add("📁 elements", expand=False)
        elements.add_leaf("📄 workstream-1.md")
        elements.add_leaf("📄 workstream-2.md")

        research = project1.add("📁 research", expand=False)
        research.add_leaf("📄 findings.md")

        exports = project1.add("📁 exports", expand=False)
        exports.add_leaf("📄 synthesis.md")
