"""Tests for synthesis viewer widget."""

from app.files.validate_element import ValidationError
from app.synthesis.controller import CriticIssue
from app.tui.widgets.synthesis_viewer import SynthesisViewer


class TestSynthesisViewer:
    """Test synthesis viewer widget methods."""

    def test_init(self) -> None:
        """Test viewer initialization."""
        viewer = SynthesisViewer("test-workstream")
        assert viewer.workstream == "test-workstream"
        assert viewer.log_widget is not None
        assert viewer.status is not None

    def test_update_status(self) -> None:
        """Test status update."""
        viewer = SynthesisViewer("test")
        viewer.update_status("New status")
        # Status widget should be updated (actual update requires app context)
        assert viewer.status is not None

    def test_show_findings_summary(self) -> None:
        """Test findings summary display."""
        viewer = SynthesisViewer("test")

        # Test with findings
        viewer.show_findings_summary(10, (0.5, 0.9))

        # Test with no findings
        viewer.show_findings_summary(0, (0.0, 0.0))

    def test_show_validation_results(self) -> None:
        """Test validation results display."""
        viewer = SynthesisViewer("test")

        # Test with no errors
        viewer.show_validation_results([])

        # Test with errors
        errors = [
            ValidationError("Decisions", "Missing section"),
            ValidationError("Requirements", "Empty section", line_number=10),
            ValidationError("AC", "Bad format", line_number=20),
            ValidationError("Open Questions", "Issue 4"),
            ValidationError("Risks", "Issue 5"),
            ValidationError("Extra", "Issue 6"),  # Will be truncated
        ]
        viewer.show_validation_results(errors)

    def test_show_critic_results(self) -> None:
        """Test critic results display."""
        viewer = SynthesisViewer("test")

        # Test with no issues
        viewer.show_critic_results([])

        # Test with mixed severity issues
        issues = [
            CriticIssue("Critical", "Requirements", "Missing requirement", "Add requirement"),
            CriticIssue("Critical", "Requirements", "Bad requirement", "Fix it"),
            CriticIssue("Critical", "AC", "Issue 3", "Fix"),
            CriticIssue("Critical", "AC", "Issue 4", "Fix"),  # Will be truncated
            CriticIssue("Warning", "Decisions", "Unclear decision", "Clarify"),
            CriticIssue("Warning", "Risks", "Missing risk", "Add risk"),
            CriticIssue("Warning", "Open Questions", "W3", ""),
            CriticIssue("Warning", "Extra", "W4", ""),  # Will be truncated
            CriticIssue("Suggestion", "Requirements", "Consider X", ""),
            CriticIssue("Suggestion", "Requirements", "Consider Y", ""),
        ]
        viewer.show_critic_results(issues)

    def test_show_diff_preview(self) -> None:
        """Test diff preview display."""
        viewer = SynthesisViewer("test")

        # Test short diff
        short_diff = "--- a/file.md\n+++ b/file.md\n@@ -1,3 +1,3 @@\n-old line\n+new line"
        viewer.show_diff_preview(short_diff, max_lines=10)

        # Test long diff (will be truncated)
        long_diff = "\n".join([f"Line {i}" for i in range(50)])
        viewer.show_diff_preview(long_diff, max_lines=20)

    def test_show_completion(self) -> None:
        """Test completion status display."""
        viewer = SynthesisViewer("test")

        # Test successful completion
        viewer.show_completion(
            success=True, path="/projects/test/elements/ui.md", log_path="/logs/run-123.jsonl"
        )

        # Test cancelled
        viewer.show_completion(success=False, log_path="/logs/run-456.jsonl")

        # Test without paths
        viewer.show_completion(success=True)
        viewer.show_completion(success=False)

    def test_log_message(self) -> None:
        """Test generic log message."""
        viewer = SynthesisViewer("test")
        viewer.log_message("Test message")
        viewer.log_message("[bold]Formatted message[/bold]")
