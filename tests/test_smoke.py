"""Smoke tests to verify basic imports and structure."""


def test_app_imports():
    """Test that the app module can be imported."""
    import app
    assert app is not None
    assert hasattr(app, "__version__")


def test_tui_app_imports():
    """Test that the TUI app can be imported."""
    from app.tui import app as tui_module
    from app.tui.app import BrainstormBuddyApp
    
    assert tui_module is not None
    assert BrainstormBuddyApp is not None
    assert hasattr(BrainstormBuddyApp, "TITLE")
    assert BrainstormBuddyApp.TITLE == "Brainstorm Buddy"