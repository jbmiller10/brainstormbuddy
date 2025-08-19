"""Import tests for TUI modules to ensure no import errors."""


def test_tui_app_imports() -> None:
    """Test that the main TUI app module imports successfully."""
    from app.tui.app import BrainstormBuddyApp, main  # noqa: F401

    assert BrainstormBuddyApp is not None
    assert main is not None


def test_tui_views_imports() -> None:
    """Test that all view modules import successfully."""
    from app.tui.views import MainLayout  # noqa: F401
    from app.tui.views.main_layout import MainLayout as ML  # noqa: F401

    assert MainLayout is ML


def test_tui_widgets_imports() -> None:
    """Test that all widget modules import successfully."""
    from app.tui.widgets import (  # noqa: F401
        CommandPalette,
        ContextPanel,
        FileTree,
        SessionViewer,
    )
    from app.tui.widgets.command_palette import CommandPalette as CP  # noqa: F401
    from app.tui.widgets.context_panel import ContextPanel as CTX  # noqa: F401
    from app.tui.widgets.file_tree import FileTree as FT  # noqa: F401
    from app.tui.widgets.session_viewer import SessionViewer as SV  # noqa: F401

    assert CommandPalette is CP
    assert ContextPanel is CTX
    assert FileTree is FT
    assert SessionViewer is SV


def test_widget_instantiation() -> None:
    """Test that widgets can be instantiated without errors."""
    from app.tui.widgets import (
        CommandPalette,
        ContextPanel,
        FileTree,
        SessionViewer,
    )

    # Create instances to ensure no initialization errors
    file_tree = FileTree()
    session_viewer = SessionViewer()
    context_panel = ContextPanel()
    command_palette = CommandPalette()

    assert file_tree is not None
    assert session_viewer is not None
    assert context_panel is not None
    assert command_palette is not None
