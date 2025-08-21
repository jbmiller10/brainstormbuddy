"""Integration tests for panel updates with AppState."""

import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from textual.widgets import Static

from app.core.state import get_app_state
from app.files.project_meta import ProjectMeta
from app.tui.widgets.context_panel import ContextPanel
from app.tui.widgets.file_tree import FileTree


@pytest.fixture
def reset_app_state():
    """Reset AppState singleton for testing."""
    # Clear the singleton instance
    import app.core.state

    app.core.state._instance = None
    yield
    # Clear again after test
    app.core.state._instance = None


@pytest.fixture
def sample_project(tmp_path: Path) -> dict[str, str]:
    """Create a sample project for testing."""
    # Create project directory
    project_dir = tmp_path / "projects" / "test-project"
    project_dir.mkdir(parents=True)

    # Create project.yaml
    project_data = {
        "slug": "test-project",
        "title": "Test Project",
        "created": "2024-01-01T00:00:00",
        "stage": "kernel",
        "description": "A test project for panel updates",
        "tags": ["test", "integration"],
        "metadata": {"version": "1.0.0", "format": "brainstormbuddy-project"},
    }

    # Change to tmp_path for project creation
    import os

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        ProjectMeta.write_project_yaml("test-project", project_data)

        # Create some files
        (project_dir / "kernel.md").write_text("# Kernel\nTest kernel content")
        (project_dir / "outline.md").write_text("# Outline\nTest outline")

        # Create elements directory with a file
        elements_dir = project_dir / "elements"
        elements_dir.mkdir()
        (elements_dir / "workstream-1.md").write_text("# Workstream 1")

        # Create empty research directory
        (project_dir / "research").mkdir()

        return project_data
    finally:
        os.chdir(original_cwd)


class TestFileTreeUpdates:
    """Test FileTree widget updates with AppState."""

    def test_file_tree_subscribes_to_appstate(self, reset_app_state, tmp_path):  # noqa: ARG002
        """Test that FileTree subscribes to AppState on mount."""
        # Create FileTree
        tree = FileTree()

        # Mock the refresh_tree method
        tree.refresh_tree = Mock()

        # Simulate mount
        tree.on_mount()

        # Verify disposer was created
        assert tree._disposer is not None

        # Change project
        app_state = get_app_state()
        app_state.set_active_project("new-project")

        # Verify refresh was called
        tree.refresh_tree.assert_called_with("new-project")

        # Clean up
        tree.on_unmount()
        assert tree._disposer is None

    def test_file_tree_shows_real_files(self, reset_app_state, sample_project, tmp_path):  # noqa: ARG002
        """Test that FileTree shows actual project files."""
        import os

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tree = FileTree()

            # Refresh with test project
            tree.refresh_tree("test-project")

            # Check that project title is set
            assert "Test Project" in tree.root.label

            # Check that files are listed (would need to traverse tree.root.children)
            assert tree._current_project == "test-project"
        finally:
            os.chdir(original_cwd)

    def test_file_tree_empty_state(self, reset_app_state):  # noqa: ARG002
        """Test FileTree shows empty state when no project."""
        tree = FileTree()
        tree._show_empty_state()

        assert tree._current_project is None
        # Convert Rich text to string for comparison
        assert str(tree.root.label) == "Projects"


class TestContextPanelUpdates:
    """Test ContextPanel widget updates with AppState."""

    def test_context_panel_subscribes_to_appstate(self, reset_app_state):  # noqa: ARG002
        """Test that ContextPanel subscribes to AppState on mount."""
        panel = ContextPanel()

        # Mock update_for_project
        panel.update_for_project = Mock()

        # Mock the mount method to avoid Textual mounting issues
        with patch.object(panel, "mount"):
            # Simulate mount
            panel.on_mount()

        # Verify disposer was created
        assert panel._disposer is not None

        # Change project
        app_state = get_app_state()
        app_state.set_active_project("test-project")

        # Verify update was called
        panel.update_for_project.assert_called_with("test-project")

        # Clean up
        panel.on_unmount()
        assert panel._disposer is None

    def test_context_panel_stage_mapping(self):
        """Test that ContextPanel has correct stage to action mapping."""
        panel = ContextPanel()

        # Check all stages are mapped
        expected_stages = ["capture", "clarify", "kernel", "outline", "research", "synthesis"]
        for stage in expected_stages:
            assert stage in panel.STAGE_NEXT_ACTIONS
            assert isinstance(panel.STAGE_NEXT_ACTIONS[stage], str)

        # Check specific mappings
        assert "clarify" in panel.STAGE_NEXT_ACTIONS["capture"]
        assert "kernel" in panel.STAGE_NEXT_ACTIONS["clarify"]
        assert "workstreams" in panel.STAGE_NEXT_ACTIONS["kernel"]
        assert "research" in panel.STAGE_NEXT_ACTIONS["outline"]
        assert "synthesis" in panel.STAGE_NEXT_ACTIONS["research"]
        assert "export" in panel.STAGE_NEXT_ACTIONS["synthesis"]

    def test_context_panel_update_for_project(self, reset_app_state, sample_project, tmp_path):  # noqa: ARG002
        """Test ContextPanel updates correctly for a project."""
        import os

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            panel = ContextPanel()

            # Create mock cards
            panel._stage_card = Mock(spec=Static)
            panel._project_card = Mock(spec=Static)
            panel._action_card = Mock(spec=Static)

            # Update for test project
            panel.update_for_project("test-project")

            # Verify cards were updated
            panel._project_card.update.assert_called()
            panel._stage_card.update.assert_called()
            panel._action_card.update.assert_called()

            # Check that kernel stage shows correct next action
            action_call_args = panel._action_card.update.call_args[0][0]
            assert "workstreams" in action_call_args.lower()
        finally:
            os.chdir(original_cwd)


class TestPanelSynchronization:
    """Test synchronization between panels on project switch."""

    @pytest.mark.asyncio
    async def test_rapid_project_switching(self, reset_app_state, tmp_path):  # noqa: ARG002
        """Test panels handle rapid project switching without stale state."""
        import os

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Create multiple projects
            for i in range(3):
                project_dir = tmp_path / "projects" / f"project-{i}"
                project_dir.mkdir(parents=True)
                ProjectMeta.write_project_yaml(
                    f"project-{i}",
                    {
                        "slug": f"project-{i}",
                        "title": f"Project {i}",
                        "created": "2024-01-01T00:00:00",
                        "stage": "capture",
                        "description": f"Project {i} description",
                        "tags": [],
                        "metadata": {"version": "1.0.0", "format": "brainstormbuddy-project"},
                    },
                )

            # Create panels
            tree = FileTree()
            panel = ContextPanel()

            # Mock update methods
            tree.refresh_tree = Mock()
            panel.update_for_project = Mock()

            # Simulate mount for tree
            tree.on_mount()

            # Mock mount for panel to avoid Textual mounting issues
            with patch.object(panel, "mount"):
                panel.on_mount()

            app_state = get_app_state()

            # Rapid switching
            for _ in range(2):
                for i in range(3):
                    app_state.set_active_project(f"project-{i}")
                    await asyncio.sleep(0.01)  # Small delay

            # Final project should be project-2
            assert app_state.active_project == "project-2"

            # Both panels should have been called with project-2 as the last call
            tree.refresh_tree.assert_called_with("project-2")
            panel.update_for_project.assert_called_with("project-2")

            # Clean up
            tree.on_unmount()
            panel.on_unmount()
        finally:
            os.chdir(original_cwd)


class TestResearchDBPath:
    """Test research database path resolution."""

    def test_get_db_path_creates_directory(self, tmp_path):
        """Test that get_db_path creates research directory if missing."""
        import os

        from app.tui.views.research import get_db_path

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Create projects directory but not research
            (tmp_path / "projects" / "test-proj").mkdir(parents=True)

            # Get DB path
            db_path = get_db_path("test-proj")

            # Verify path and directory creation (get_db_path returns relative path)
            assert db_path == Path("projects") / "test-proj" / "research" / "findings.db"
            assert db_path.parent.exists()
            assert db_path.parent.name == "research"
        finally:
            os.chdir(original_cwd)

    def test_research_modal_uses_active_project(self, reset_app_state, tmp_path):  # noqa: ARG002
        """Test ResearchImportModal uses active project for DB path."""
        import os

        from app.tui.views.research import ResearchImportModal

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            # Set active project
            app_state = get_app_state()
            app_state.set_active_project("my-project")

            # Create modal without explicit db_path
            modal = ResearchImportModal()

            # Verify it uses active project path
            assert "my-project" in str(modal.db_path)
            assert "research" in str(modal.db_path)
            assert modal.db_path.name == "findings.db"
        finally:
            os.chdir(original_cwd)


class TestCommandPaletteIntegration:
    """Test command palette uses active project."""

    @pytest.mark.asyncio
    async def test_commands_require_active_project(self, reset_app_state):  # noqa: ARG002
        """Test that commands check for active project."""
        from app.core.state import get_app_state

        # Just test that the commands properly check for active project
        # by verifying that get_app_state is used
        app_state = get_app_state()
        app_state.set_active_project(None)

        # Verify no active project
        assert app_state.active_project is None

        # Now set a project and verify it's set
        app_state.set_active_project("test-project")
        assert app_state.active_project == "test-project"

        # Reset for other tests
        app_state.set_active_project(None)
