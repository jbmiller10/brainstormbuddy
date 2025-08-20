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

    def write(
        self,
        content: object,
        width: int | None = None,
        expand: bool = False,
        shrink: bool = True,
        scroll_end: bool | None = None,
        animate: bool = False,
    ) -> "SessionViewer":
        """
        Write text to the viewer with optional scrolling.

        Args:
            content: Content to write (supports Rich markup)
            width: Width hint for content
            expand: Whether to expand content to full width
            shrink: Whether to shrink content to fit
            scroll_end: Whether to scroll to the end after writing
            animate: Whether to animate scrolling

        Returns:
            Self for chaining
        """
        super().write(
            content,
            width=width,
            expand=expand,
            shrink=shrink,
            scroll_end=scroll_end,
            animate=animate,
        )
        return self
