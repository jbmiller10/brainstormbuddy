"""Tests for kernel stage functionality."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.core.state import get_app_state
from app.files.diff import compute_patch, generate_diff_preview
from app.llm.claude_client import FakeClaudeClient, MessageDone, TextDelta
from app.tui.views.session import SessionController
from app.tui.widgets.kernel_approval import MODAL_CANCELLED, KernelApprovalModal
from app.tui.widgets.session_viewer import SessionViewer


@pytest.mark.asyncio
async def test_kernel_stage_fake_client_generates_content() -> None:
    """Test that FakeClaudeClient generates kernel content."""
    client = FakeClaudeClient()

    # Stream with kernel stage system prompt
    events = []
    async for event in client.stream(
        prompt="Build a todo app",
        system_prompt="You are in the kernel stage of brainstorming.",
    ):
        events.append(event)

    # Should have text deltas followed by MessageDone
    assert len(events) > 1
    assert any(isinstance(e, TextDelta) for e in events)
    assert isinstance(events[-1], MessageDone)

    # Check content includes expected sections
    full_text = "".join(e.text for e in events if isinstance(e, TextDelta))
    assert "## Core Concept" in full_text
    assert "## Key Questions" in full_text
    assert "## Success Criteria" in full_text
    assert "## Constraints" in full_text
    assert "## Primary Value Proposition" in full_text


@pytest.mark.asyncio
async def test_kernel_output_format_requirements() -> None:
    """Test that kernel output meets F1 ticket requirements."""
    client = FakeClaudeClient()

    # Stream with kernel stage system prompt
    events = []
    async for event in client.stream(
        prompt="Build an application",
        system_prompt="You are in the kernel stage of brainstorming.",
    ):
        events.append(event)

    # Get full text
    full_text = "".join(e.text for e in events if isinstance(e, TextDelta))

    # F1 Requirements:
    # 1. Output starts with "# Kernel"
    assert full_text.strip().startswith("# Kernel"), "Output must start with '# Kernel'"

    # 2. No diff markers, fences, or explanations
    assert "```" not in full_text, "Output must not contain code fences"
    assert "---" not in full_text, "Output must not contain diff markers"
    assert "+++" not in full_text, "Output must not contain diff markers"
    assert "@@" not in full_text, "Output must not contain diff markers"

    # 3. Exactly 5 sections in the specified order
    lines = full_text.strip().split("\n")
    section_headers = [line for line in lines if line.startswith("##")]
    expected_sections = [
        "## Core Concept",
        "## Key Questions",
        "## Success Criteria",
        "## Constraints",
        "## Primary Value Proposition",
    ]
    assert section_headers == expected_sections, f"Sections must be in order: {expected_sections}"


def test_kernel_diff_preview_generation() -> None:
    """Test that diff preview is generated correctly for kernel changes."""
    old_content = """## Core Concept
Old concept here.

## Key Questions
1. Old question
"""

    new_content = """## Core Concept
New and improved concept.

## Key Questions
1. Better question
2. Additional question

## Success Criteria
- New criteria added
"""

    diff = generate_diff_preview(
        old_content,
        new_content,
        from_label="kernel.md (current)",
        to_label="kernel.md (proposed)",
    )

    assert "--- kernel.md (current)" in diff
    assert "+++ kernel.md (proposed)" in diff
    assert "-Old concept here." in diff
    assert "+New and improved concept." in diff
    assert "+2. Additional question" in diff
    assert "+## Success Criteria" in diff


@pytest.mark.asyncio
async def test_session_controller_kernel_session() -> None:
    """Test SessionController.start_kernel_session method."""
    # Create mock viewer
    viewer = Mock(spec=SessionViewer)
    viewer.clear = Mock()
    viewer.write = Mock()
    viewer.app = Mock()

    controller = SessionController(viewer)

    # Mock the client to return test events
    mock_events = [
        TextDelta("## Core Concept\n"),
        TextDelta("Test kernel content\n"),
        MessageDone(),
    ]

    async def mock_stream(*args, **kwargs):  # type: ignore  # noqa: ARG001
        for event in mock_events:
            yield event

    controller.client.stream = mock_stream  # type: ignore

    # Mock the modal interaction
    with patch.object(controller, "_show_kernel_diff_preview", new_callable=AsyncMock) as mock_show:
        await controller.start_kernel_session("test-project", "Build something")

    # Verify controller state
    assert controller.current_stage == "kernel"
    assert controller.project_slug == "test-project"
    assert controller.pending_kernel_content == "## Core Concept\nTest kernel content\n"

    # Verify viewer was updated
    viewer.clear.assert_called_once()
    assert viewer.write.call_count >= 3

    # Verify diff preview was called
    mock_show.assert_called_once()


def test_session_controller_approve_kernel_changes(tmp_path: Path) -> None:
    """Test approving kernel changes writes file atomically."""
    # Create mock viewer
    viewer = Mock(spec=SessionViewer)
    viewer.write = Mock()

    controller = SessionController(viewer)
    controller.project_slug = "test-project"
    controller.pending_kernel_content = "# New Kernel\nContent here"

    # Set working directory to tmp_path for test
    with patch("app.tui.views.session.Path") as mock_path:
        # Make Path() return paths relative to tmp_path
        def path_side_effect(arg: str) -> Path:
            if arg == "projects":
                return tmp_path / "projects"
            return Path(arg)

        mock_path.side_effect = path_side_effect

        # Create projects directory
        projects_dir = tmp_path / "projects" / "test-project"
        projects_dir.mkdir(parents=True)

        # Approve changes
        result = controller.approve_kernel_changes()

    assert result is True

    # Verify file was written
    kernel_file = projects_dir / "kernel.md"
    assert kernel_file.exists()
    assert kernel_file.read_text() == "# New Kernel\nContent here"

    # Verify success message
    viewer.write.assert_called_with(
        "\n[green]✓ Kernel successfully written to projects/test-project/kernel.md[/green]\n"
    )


def test_session_controller_reject_kernel_changes() -> None:
    """Test rejecting kernel changes clears pending content."""
    # Create mock viewer
    viewer = Mock(spec=SessionViewer)
    viewer.write = Mock()

    controller = SessionController(viewer)
    controller.pending_kernel_content = "Some pending content"

    controller.reject_kernel_changes()

    assert controller.pending_kernel_content is None
    viewer.write.assert_called_with(
        "\n[yellow]Changes rejected. Kernel file remains unchanged.[/yellow]\n"
    )


def test_session_controller_approve_with_error(tmp_path: Path) -> None:  # noqa: ARG001
    """Test that approval handles errors gracefully."""
    # Create mock viewer
    viewer = Mock(spec=SessionViewer)
    viewer.write = Mock()

    controller = SessionController(viewer)
    controller.project_slug = "test-project"
    controller.pending_kernel_content = "# New Kernel\nContent"

    # Mock apply_patch to raise an error
    with patch("app.tui.views.session.apply_patch") as mock_apply:
        mock_apply.side_effect = PermissionError("Cannot write file")

        result = controller.approve_kernel_changes()

    assert result is False

    # Verify error message
    calls = viewer.write.call_args_list
    assert any("[red]Error applying changes:" in str(call) for call in calls)
    assert any("[yellow]Original file remains unchanged." in str(call) for call in calls)


def test_kernel_approval_modal_initialization() -> None:
    """Test KernelApprovalModal initialization."""
    diff_content = "--- before\n+++ after\n@@ -1 +1 @@\n-old\n+new"
    modal = KernelApprovalModal(diff_content, "test-project")

    assert modal.diff_content == diff_content
    assert modal.project_slug == "test-project"
    assert modal.mode == "diff"  # Default mode


def test_kernel_approval_modal_proposal_mode() -> None:
    """Test KernelApprovalModal in proposal mode."""
    proposal_content = """# Kernel

## Core Concept
This is the core concept.

## Key Questions
1. Question one
"""
    modal = KernelApprovalModal(proposal_content, "test-project", mode="proposal")

    assert modal.diff_content == proposal_content
    assert modal.project_slug == "test-project"
    assert modal.mode == "proposal"


def test_kernel_approval_modal_unfences_content() -> None:
    """Test that KernelApprovalModal unfences content in proposal mode."""
    fenced_content = """```markdown
# Kernel

## Core Concept
This is the core concept.
```"""

    expected_content = """# Kernel

## Core Concept
This is the core concept."""

    modal = KernelApprovalModal(fenced_content, "test-project", mode="proposal")

    assert modal.diff_content == expected_content
    assert modal.mode == "proposal"


@pytest.mark.asyncio
async def test_kernel_approval_modal_accept() -> None:
    """Test accepting changes in the modal."""
    modal = KernelApprovalModal("diff content", "test-project")
    modal.dismiss = MagicMock()  # type: ignore

    modal.action_accept()

    modal.dismiss.assert_called_once_with("accept")


@pytest.mark.asyncio
async def test_kernel_approval_modal_clarify() -> None:
    """Test requesting clarification in the modal."""
    modal = KernelApprovalModal("diff content", "test-project")
    modal.dismiss = MagicMock()  # type: ignore

    modal.action_clarify()

    modal.dismiss.assert_called_once_with("clarify")


@pytest.mark.asyncio
async def test_kernel_approval_modal_restart() -> None:
    """Test restart option in the modal."""
    modal = KernelApprovalModal("diff content", "test-project")
    modal.dismiss = MagicMock()  # type: ignore

    modal.action_restart()

    modal.dismiss.assert_called_once_with("restart")


@pytest.mark.asyncio
async def test_kernel_approval_modal_cancel() -> None:
    """Test cancel option in the modal."""
    modal = KernelApprovalModal("diff content", "test-project")
    modal.dismiss = MagicMock()  # type: ignore

    modal.action_cancel()

    modal.dismiss.assert_called_once_with(MODAL_CANCELLED)


def test_compute_patch_for_kernel_update() -> None:
    """Test computing patch for updating existing kernel."""
    old_kernel = """## Core Concept
Initial idea.

## Key Questions
1. Question one
"""

    new_kernel = """## Core Concept
Refined idea with more details.

## Key Questions
1. Question one
2. New question added

## Success Criteria
- Criterion 1
"""

    patch = compute_patch(old_kernel, new_kernel)

    assert patch.original == old_kernel
    assert patch.modified == new_kernel
    assert len(patch.diff_lines) > 0

    # Verify diff contains expected changes
    diff_text = "\n".join(patch.diff_lines)
    assert "-Initial idea." in diff_text
    assert "+Refined idea with more details." in diff_text
    assert "+2. New question added" in diff_text
    assert "+## Success Criteria" in diff_text


@pytest.mark.asyncio
async def test_session_controller_generate_workstreams_with_kernel(tmp_path: Path) -> None:
    """Test generating workstreams with existing kernel file."""
    # Create mock viewer
    viewer = Mock(spec=SessionViewer)
    viewer.clear = Mock()
    viewer.write = Mock()
    viewer.app = Mock()

    controller = SessionController(viewer)
    controller.project_slug = "test-project"

    # Create project directory with kernel file
    project_dir = tmp_path / "projects" / "test-project"
    project_dir.mkdir(parents=True)

    kernel_content = """## Core Concept
A revolutionary task management system.

## Key Questions
1. How to optimize workflows?
"""
    kernel_file = project_dir / "kernel.md"
    kernel_file.write_text(kernel_content)

    # Mock the modal to return approval
    viewer.app.push_screen_wait = AsyncMock(return_value=True)

    # Mock the actual batch creation and file operations
    with patch("app.tui.views.session.Path") as mock_path:
        # Make Path() return paths relative to tmp_path
        def path_side_effect(arg: str) -> Path:
            if arg == "projects":
                return tmp_path / "projects"
            return Path(arg)

        mock_path.side_effect = path_side_effect
        mock_path.return_value = tmp_path / "projects"

        # Mock division operator for Path objects
        def path_div(self: Path, other: str) -> Path:
            return self / other if isinstance(self, Path) else tmp_path / "projects" / other

        mock_path.__truediv__ = path_div

        # Set active project in AppState
        app_state = get_app_state()
        app_state.set_active_project("test-project")

        await controller.generate_workstreams()

    # Verify viewer was updated
    viewer.clear.assert_called_once()
    assert viewer.write.call_count >= 3  # Title, project, and status messages

    # Verify modal was shown
    viewer.app.push_screen_wait.assert_called_once()

    # Verify files were created
    assert (project_dir / "outline.md").exists()
    assert (project_dir / "elements").exists()
    assert (project_dir / "elements" / "requirements.md").exists()


@pytest.mark.asyncio
async def test_session_controller_generate_workstreams_without_kernel(tmp_path: Path) -> None:
    """Test generating workstreams without existing kernel file."""
    # Create mock viewer
    viewer = Mock(spec=SessionViewer)
    viewer.clear = Mock()
    viewer.write = Mock()
    viewer.app = Mock()

    controller = SessionController(viewer)

    # Create project directory without kernel
    project_dir = tmp_path / "projects" / "new-project"
    project_dir.mkdir(parents=True)

    # Mock the modal to return approval
    viewer.app.push_screen_wait = AsyncMock(return_value=True)

    with patch("app.tui.views.session.Path") as mock_path:
        # Make Path() return paths relative to tmp_path
        def path_side_effect(arg: str) -> Path:
            if arg == "projects":
                return tmp_path / "projects"
            return Path(arg)

        mock_path.side_effect = path_side_effect

        # Set active project in AppState
        app_state = get_app_state()
        app_state.set_active_project("new-project")

        await controller.generate_workstreams()

    # Verify viewer was updated
    viewer.clear.assert_called_once()
    assert viewer.write.call_count >= 3

    # Verify files were created (without kernel summary)
    assert (project_dir / "outline.md").exists()
    outline_content = (project_dir / "outline.md").read_text()
    assert "## From Kernel" not in outline_content  # No kernel section


@pytest.mark.asyncio
async def test_session_controller_generate_workstreams_rejection() -> None:
    """Test rejecting workstream generation."""
    # Create mock viewer
    viewer = Mock(spec=SessionViewer)
    viewer.clear = Mock()
    viewer.write = Mock()
    viewer.app = Mock()

    controller = SessionController(viewer)

    # Mock the modal to return rejection (False)
    viewer.app.push_screen_wait = AsyncMock(return_value=False)

    # Set active project in AppState
    app_state = get_app_state()
    app_state.set_active_project("test-project")

    await controller.generate_workstreams()

    # Verify rejection message was written
    viewer.clear.assert_called_once()
    calls = [str(call) for call in viewer.write.call_args_list]
    assert any("rejected" in call.lower() for call in calls)


@pytest.mark.asyncio
async def test_session_controller_generate_workstreams_error(tmp_path: Path) -> None:  # noqa: ARG001
    """Test error handling in workstream generation."""
    # Create mock viewer
    viewer = Mock(spec=SessionViewer)
    viewer.clear = Mock()
    viewer.write = Mock()
    viewer.app = Mock()

    controller = SessionController(viewer)

    # Mock create_workstream_batch to raise an error
    with patch("app.tui.views.session.create_workstream_batch") as mock_create:
        mock_create.side_effect = PermissionError("Cannot create files")

        # Set active project in AppState
        app_state = get_app_state()
        app_state.set_active_project("test-project")

        await controller.generate_workstreams()

    # Verify error message was written
    viewer.clear.assert_called_once()
    calls = [str(call) for call in viewer.write.call_args_list]
    assert any("Error generating workstreams" in str(call) for call in calls)
    assert any("No files were modified" in str(call) for call in calls)
