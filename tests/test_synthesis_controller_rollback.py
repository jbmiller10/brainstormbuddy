"""Tests for synthesis controller rollback and error handling."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.synthesis.controller import (
    SynthesisConfig,
    SynthesisController,
    SynthesisProgress,
    SynthesisResult,
)


class TestSynthesisControllerRollback:
    """Test rollback and error handling in synthesis controller."""

    @pytest.mark.asyncio
    async def test_apply_synthesis_with_existing_file_backup(self) -> None:
        """Test that apply_synthesis creates backup of existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "projects" / "test-project"
            elements_path = project_path / "elements"
            elements_path.mkdir(parents=True)

            # Create existing element file
            element_file = elements_path / "test-workstream.md"
            original_content = "# Original Content\n## Decisions\n- Old decision"
            element_file.write_text(original_content)

            controller = SynthesisController("test-project")
            controller.project_path = project_path

            result = SynthesisResult(
                workstream="test-workstream",
                proposal="# New Content\n## Decisions\n- New decision",
                validation_errors=[],
                critic_issues=None,
                diff_preview="",
                applied=False,
            )

            # Apply synthesis
            await controller.apply_synthesis(result)

            # Verify file was updated
            assert element_file.read_text() == result.proposal
            assert result.applied is True

    @pytest.mark.asyncio
    async def test_apply_synthesis_rollback_on_write_failure(self) -> None:
        """Test that apply_synthesis rolls back on write failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "projects" / "test-project"
            elements_path = project_path / "elements"
            elements_path.mkdir(parents=True)

            # Create existing element file
            element_file = elements_path / "test-workstream.md"
            original_content = "# Original Content"
            element_file.write_text(original_content)

            controller = SynthesisController("test-project")
            controller.project_path = project_path

            result = SynthesisResult(
                workstream="test-workstream",
                proposal="# New Content",
                validation_errors=[],
                critic_issues=None,
                diff_preview="",
                applied=False,
            )

            # Mock atomic_write_text to fail on first call, succeed on rollback
            with patch("app.synthesis.controller.atomic_write_text") as mock_write:
                mock_write.side_effect = [
                    Exception("Write failed"),  # First write fails
                    None,  # Rollback succeeds
                ]

                # Apply should raise the exception
                with pytest.raises(Exception, match="Write failed"):
                    await controller.apply_synthesis(result)

                # Verify rollback was attempted
                assert mock_write.call_count == 2
                # Second call should be the rollback with original content
                rollback_call = mock_write.call_args_list[1]
                assert rollback_call[0][1] == original_content

                # Result should not be marked as applied
                assert result.applied is False

    @pytest.mark.asyncio
    async def test_apply_synthesis_rollback_failure(self) -> None:
        """Test handling when both write and rollback fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "projects" / "test-project"
            elements_path = project_path / "elements"
            elements_path.mkdir(parents=True)

            # Create existing element file
            element_file = elements_path / "test-workstream.md"
            original_content = "# Original Content"
            element_file.write_text(original_content)

            controller = SynthesisController("test-project")
            controller.project_path = project_path

            result = SynthesisResult(
                workstream="test-workstream",
                proposal="# New Content",
                validation_errors=[],
                critic_issues=None,
                diff_preview="",
                applied=False,
            )

            # Mock atomic_write_text to fail on both attempts
            with patch("app.synthesis.controller.atomic_write_text") as mock_write:
                mock_write.side_effect = [
                    Exception("Write failed"),  # First write fails
                    Exception("Rollback failed"),  # Rollback also fails
                ]

                # Should raise the rollback exception
                with pytest.raises(Exception, match="Rollback failed"):
                    await controller.apply_synthesis(result)

                # Verify both writes were attempted
                assert mock_write.call_count == 2

                # Verify critical failure was logged
                log_events = []
                with patch.object(controller.logger, "log_event", new=AsyncMock()) as mock_log:
                    mock_log.side_effect = lambda **kwargs: log_events.append(kwargs)

                    with patch("app.synthesis.controller.atomic_write_text") as mock_write2:
                        mock_write2.side_effect = [
                            Exception("Write failed"),
                            Exception("Rollback failed"),
                        ]

                        with pytest.raises(Exception, match="Rollback failed"):
                            await controller.apply_synthesis(result)

    @pytest.mark.asyncio
    async def test_apply_synthesis_no_rollback_for_new_file(self) -> None:
        """Test that no rollback happens when creating a new file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "projects" / "test-project"
            elements_path = project_path / "elements"
            elements_path.mkdir(parents=True)

            controller = SynthesisController("test-project")
            controller.project_path = project_path

            result = SynthesisResult(
                workstream="new-workstream",
                proposal="# New Content",
                validation_errors=[],
                critic_issues=None,
                diff_preview="",
                applied=False,
            )

            # Mock atomic_write_text to fail
            with patch("app.synthesis.controller.atomic_write_text") as mock_write:
                mock_write.side_effect = Exception("Write failed")

                # Should raise the exception without attempting rollback
                with pytest.raises(Exception, match="Write failed"):
                    await controller.apply_synthesis(result)

                # Only one write attempt (no rollback)
                assert mock_write.call_count == 1

    @pytest.mark.asyncio
    async def test_synthesis_with_progress_callback(self) -> None:
        """Test synthesis with progress tracking enabled."""
        config = SynthesisConfig(enable_progress_tracking=True)
        controller = SynthesisController("test-project", config=config)

        # Track progress updates
        progress_updates = []

        def progress_callback(progress: SynthesisProgress) -> None:
            progress_updates.append(progress)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "projects" / "test-project"
            project_path.mkdir(parents=True)

            # Create kernel
            kernel_path = project_path / "kernel.md"
            kernel_path.write_text("# Test Kernel")

            controller.project_path = project_path

            # Mock the architect to return a simple proposal
            with patch.object(controller, "run_architect", new=AsyncMock()) as mock_architect:
                mock_architect.return_value = """# Test
## Decisions
## Requirements
## Open Questions
## Risks & Mitigations
## Acceptance Criteria
- AC-1: Test criteria"""

                await controller.synthesize_workstream(
                    workstream="test",
                    progress_callback=progress_callback,
                )

                # Verify progress was reported
                assert len(progress_updates) > 0

                # Check key progress steps
                steps = [p.step for p in progress_updates]
                assert "start" in steps
                assert "kernel" in steps
                assert "findings" in steps
                assert "architect" in steps
                assert "validation" in steps
                assert "complete" in steps

                # Verify progress values
                assert progress_updates[0].progress == 0  # Start
                assert progress_updates[-1].progress == 100  # Complete

    @pytest.mark.asyncio
    async def test_synthesis_with_progress_callback_disabled(self) -> None:
        """Test that progress callbacks are not called when disabled."""
        config = SynthesisConfig(enable_progress_tracking=False)
        controller = SynthesisController("test-project", config=config)

        progress_updates = []

        def progress_callback(progress: SynthesisProgress) -> None:
            progress_updates.append(progress)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "projects" / "test-project"
            project_path.mkdir(parents=True)

            kernel_path = project_path / "kernel.md"
            kernel_path.write_text("# Test Kernel")

            controller.project_path = project_path

            with patch.object(controller, "run_architect", new=AsyncMock()) as mock_architect:
                mock_architect.return_value = """# Test
## Decisions
## Requirements
## Open Questions
## Risks & Mitigations
## Acceptance Criteria"""

                await controller.synthesize_workstream(
                    workstream="test",
                    progress_callback=progress_callback,
                )

                # No progress updates when disabled
                assert len(progress_updates) == 0
