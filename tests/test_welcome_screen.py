"""Tests for WelcomeScreen."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest
from textual.widgets import ListView

from app.tui.views.welcome import WelcomeScreen


@pytest.fixture
def mock_app_state() -> Mock:
    """Create a mock AppState."""
    state = Mock()
    state.active_project = None
    state.set_active_project = Mock()
    return state


@pytest.fixture
def temp_projects_dir(tmp_path: Path) -> Path:
    """Create a temporary projects directory."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    return projects_dir


@pytest.fixture
def sample_project(temp_projects_dir: Path) -> Path:
    """Create a sample project with metadata."""
    import yaml

    project_dir = temp_projects_dir / "test-project"
    project_dir.mkdir()

    # Create project.yaml
    project_data = {
        "slug": "test-project",
        "title": "Test Project",
        "description": "A test project for unit tests",
        "stage": "kernel",
        "created": "2024-01-01T00:00:00",
        "tags": [],
        "metadata": {"version": "1.0.0", "format": "brainstormbuddy-project"},
    }

    with open(project_dir / "project.yaml", "w") as f:
        yaml.safe_dump(project_data, f)

    return project_dir


class TestWelcomeScreen:
    """Test suite for WelcomeScreen."""

    def test_initialization(self) -> None:
        """Test WelcomeScreen initializes correctly."""
        screen = WelcomeScreen()
        assert screen.projects == []
        assert hasattr(screen, "compose")
        assert hasattr(screen, "find_projects")
        assert hasattr(screen, "refresh_projects")

    def test_find_projects_empty(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test find_projects with no projects directory."""
        monkeypatch.chdir(tmp_path)
        screen = WelcomeScreen()
        projects = screen.find_projects()
        assert projects == []

    def test_find_projects_with_project(
        self, monkeypatch: pytest.MonkeyPatch, temp_projects_dir: Path, sample_project: Path
    ) -> None:
        """Test find_projects with a valid project."""
        # sample_project fixture creates the project, verify it exists
        assert sample_project.exists()
        monkeypatch.chdir(temp_projects_dir.parent)
        screen = WelcomeScreen()
        projects = screen.find_projects()

        assert len(projects) == 1
        assert projects[0]["slug"] == "test-project"
        assert projects[0]["title"] == "Test Project"
        assert projects[0]["description"] == "A test project for unit tests"

    def test_find_projects_multiple(
        self, monkeypatch: pytest.MonkeyPatch, temp_projects_dir: Path
    ) -> None:
        """Test find_projects with multiple projects."""
        import yaml

        monkeypatch.chdir(temp_projects_dir.parent)

        # Create multiple projects
        for i in range(3):
            project_dir = temp_projects_dir / f"project-{i}"
            project_dir.mkdir()

            project_data = {
                "slug": f"project-{i}",
                "title": f"Project {i}",
                "description": f"Description {i}",
                "stage": "capture",
                "created": f"2024-01-0{i+1}T00:00:00",
                "tags": [],
                "metadata": {"version": "1.0.0", "format": "brainstormbuddy-project"},
            }

            with open(project_dir / "project.yaml", "w") as f:
                yaml.safe_dump(project_data, f)

        screen = WelcomeScreen()
        projects = screen.find_projects()

        assert len(projects) == 3
        # Should be sorted by creation date (newest first)
        assert projects[0]["slug"] == "project-2"
        assert projects[1]["slug"] == "project-1"
        assert projects[2]["slug"] == "project-0"

    def test_find_projects_invalid_yaml(
        self, monkeypatch: pytest.MonkeyPatch, temp_projects_dir: Path
    ) -> None:
        """Test find_projects handles invalid YAML gracefully."""
        monkeypatch.chdir(temp_projects_dir.parent)

        # Create project with invalid YAML
        project_dir = temp_projects_dir / "bad-project"
        project_dir.mkdir()
        with open(project_dir / "project.yaml", "w") as f:
            f.write("invalid: yaml: content: {[}")

        screen = WelcomeScreen()
        projects = screen.find_projects()
        assert projects == []  # Invalid project should be skipped

    def test_find_projects_missing_yaml(
        self, monkeypatch: pytest.MonkeyPatch, temp_projects_dir: Path
    ) -> None:
        """Test find_projects handles missing project.yaml."""
        monkeypatch.chdir(temp_projects_dir.parent)

        # Create project directory without project.yaml
        project_dir = temp_projects_dir / "no-yaml-project"
        project_dir.mkdir()

        screen = WelcomeScreen()
        projects = screen.find_projects()
        assert projects == []  # Project without yaml should be skipped

    def test_find_projects_filesystem_race_condition(
        self, monkeypatch: pytest.MonkeyPatch, temp_projects_dir: Path
    ) -> None:
        """Test find_projects handles filesystem race conditions."""
        monkeypatch.chdir(temp_projects_dir.parent)

        screen = WelcomeScreen()

        # Mock Path.iterdir to simulate directory disappearing
        with patch.object(Path, "iterdir", side_effect=FileNotFoundError("Directory gone")):
            projects = screen.find_projects()
            assert projects == []  # Should handle gracefully

    def test_select_project(self, mock_app_state: Mock) -> None:
        """Test select_project sets app state and navigates."""
        from app.tui.views.main_screen import MainScreen

        screen = WelcomeScreen()

        # Mock the app property's return value
        mock_app = MagicMock()
        mock_app.switch_screen = Mock()

        with (
            patch("app.tui.views.welcome.get_app_state", return_value=mock_app_state),
            patch.object(WelcomeScreen, "app", new_callable=PropertyMock, return_value=mock_app),
        ):
            screen.select_project("test-project")

        mock_app_state.set_active_project.assert_called_once_with(
            "test-project", reason="project-switch"
        )
        mock_app.switch_screen.assert_called_once()
        # Check it's switching to MainScreen
        call_args = mock_app.switch_screen.call_args[0]
        assert isinstance(call_args[0], MainScreen)

    def test_action_create_project(self) -> None:
        """Test action_create_project navigates to wizard."""
        from app.tui.views.new_project_wizard import NewProjectWizard

        screen = WelcomeScreen()
        mock_app = MagicMock()
        mock_app.push_screen = Mock()

        with patch.object(WelcomeScreen, "app", new_callable=PropertyMock, return_value=mock_app):
            screen.action_create_project()

        mock_app.push_screen.assert_called_once()
        # Verify it's pushing a NewProjectWizard
        call_args = mock_app.push_screen.call_args[0]
        assert isinstance(call_args[0], NewProjectWizard)

    def test_action_select_project_no_selection(self) -> None:
        """Test action_select_project with no highlighted item."""
        screen = WelcomeScreen()
        mock_app = MagicMock()
        mock_app.switch_screen = Mock()

        # Mock query_one to return a ListView with no highlighted child
        list_view = MagicMock(spec=ListView)
        list_view.highlighted_child = None

        with (
            patch.object(WelcomeScreen, "app", new_callable=PropertyMock, return_value=mock_app),
            patch.object(screen, "query_one", return_value=list_view),
        ):
            screen.action_select_project()

        # Should not navigate
        mock_app.switch_screen.assert_not_called()

    def test_action_select_project_empty_state(self) -> None:
        """Test action_select_project with empty state selected."""
        screen = WelcomeScreen()
        mock_app = MagicMock()
        mock_app.switch_screen = Mock()

        # Mock query_one to return a ListView with empty state highlighted
        list_view = MagicMock(spec=ListView)
        highlighted = MagicMock()
        highlighted.id = "empty-state"
        list_view.highlighted_child = highlighted

        with (
            patch.object(WelcomeScreen, "app", new_callable=PropertyMock, return_value=mock_app),
            patch.object(screen, "query_one", return_value=list_view),
        ):
            screen.action_select_project()

        # Should not navigate
        mock_app.switch_screen.assert_not_called()

    def test_on_button_pressed_create(self) -> None:
        """Test button press handler for create project button."""
        screen = WelcomeScreen()
        mock_app = MagicMock()
        mock_app.push_screen = Mock()

        # Create mock button event
        event = MagicMock()
        event.button.id = "create-project"

        with patch.object(WelcomeScreen, "app", new_callable=PropertyMock, return_value=mock_app):
            screen.on_button_pressed(event)

        mock_app.push_screen.assert_called_once()

    def test_on_list_view_selected_valid_project(self, mock_app_state: Mock) -> None:
        """Test list view selection with valid project."""
        screen = WelcomeScreen()
        mock_app = MagicMock()
        mock_app.switch_screen = Mock()

        # Create mock event
        event = MagicMock()
        event.item.id = "project-test-slug"

        with (
            patch.object(WelcomeScreen, "app", new_callable=PropertyMock, return_value=mock_app),
            patch("app.tui.views.welcome.get_app_state", return_value=mock_app_state),
        ):
            screen.on_list_view_selected(event)

        mock_app_state.set_active_project.assert_called_once_with(
            "test-slug", reason="project-switch"
        )

    def test_on_list_view_selected_empty_state(self) -> None:
        """Test list view selection with empty state."""
        screen = WelcomeScreen()
        mock_app = MagicMock()
        mock_app.switch_screen = Mock()

        # Create mock event
        event = MagicMock()
        event.item.id = "empty-state"

        with patch.object(WelcomeScreen, "app", new_callable=PropertyMock, return_value=mock_app):
            screen.on_list_view_selected(event)

        # Should not navigate
        mock_app.switch_screen.assert_not_called()

    def test_refresh_projects_populates_list(
        self, monkeypatch: pytest.MonkeyPatch, temp_projects_dir: Path, sample_project: Path
    ) -> None:
        """Test refresh_projects populates ListView correctly."""
        # sample_project fixture creates the project, verify it exists
        assert sample_project.exists()
        monkeypatch.chdir(temp_projects_dir.parent)
        screen = WelcomeScreen()

        # Mock ListView
        list_view = MagicMock(spec=ListView)
        list_view.clear = MagicMock()
        list_view.append = MagicMock()

        with patch.object(screen, "query_one", return_value=list_view):
            screen.refresh_projects()

        list_view.clear.assert_called_once()
        # Should have appended one project
        assert list_view.append.call_count == 1

    def test_refresh_projects_empty_shows_message(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test refresh_projects shows empty state message."""
        monkeypatch.chdir(tmp_path)
        screen = WelcomeScreen()

        # Mock ListView
        list_view = MagicMock(spec=ListView)
        list_view.clear = MagicMock()
        list_view.append = MagicMock()

        with patch.object(screen, "query_one", return_value=list_view):
            screen.refresh_projects()

        list_view.clear.assert_called_once()
        # Should have appended empty state message
        assert list_view.append.call_count == 1
        call_args = list_view.append.call_args[0][0]
        assert call_args.id == "empty-state"
