"""Widget for displaying synthesis progress and results."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import RichLog, Static

from app.files.validate_element import ValidationError
from app.synthesis.controller import CriticIssue


class SynthesisViewer(VerticalScroll):
    """Widget to display synthesis operation progress and results."""

    DEFAULT_CSS = """
    SynthesisViewer {
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    SynthesisViewer > Static {
        margin-bottom: 1;
    }

    SynthesisViewer RichLog {
        height: auto;
        max-height: 20;
        border: solid $secondary;
        padding: 1;
    }
    """

    def __init__(self, workstream: str) -> None:
        """
        Initialize synthesis viewer.

        Args:
            workstream: The workstream being synthesized
        """
        super().__init__()
        self.workstream = workstream
        self.log_widget = RichLog(highlight=True, markup=False)
        self.status = Static(f"[bold]Synthesizing: {workstream}[/bold]")

    def compose(self) -> ComposeResult:
        """Compose the synthesis viewer UI."""
        yield self.status
        yield self.log_widget

    def update_status(self, message: str) -> None:
        """
        Update the status message.

        Args:
            message: New status message
        """
        self.status.update(message)

    def log_message(self, message: str) -> None:
        """
        Add a message to the log.

        Args:
            message: Message to log
        """
        self.log_widget.write(message)

    def show_findings_summary(
        self, findings_count: int, confidence_range: tuple[float, float]
    ) -> None:
        """
        Display summary of findings being used.

        Args:
            findings_count: Number of findings
            confidence_range: Min and max confidence values
        """
        self.log_widget.write("\n[bold]Research Findings:[/bold]")
        self.log_widget.write(f"  • Total findings: {findings_count}")
        if findings_count > 0:
            self.log_widget.write(
                f"  • Confidence range: {confidence_range[0]:.2f} - {confidence_range[1]:.2f}"
            )

    def show_validation_results(self, errors: list[ValidationError]) -> None:
        """
        Display validation results.

        Args:
            errors: List of validation errors
        """
        if not errors:
            self.log_widget.write("\n[green]✓ Document structure is valid[/green]")
        else:
            self.log_widget.write("\n[yellow]⚠ Validation issues:[/yellow]")
            for error in errors[:5]:  # Show first 5 errors
                if error.line_number:
                    self.log_widget.write(f"  Line {error.line_number}: {error.message}")
                else:
                    self.log_widget.write(f"  {error.section}: {error.message}")
            if len(errors) > 5:
                self.log_widget.write(f"  [dim](and {len(errors) - 5} more issues)[/dim]")

    def show_critic_results(self, issues: list[CriticIssue]) -> None:
        """
        Display critic review results.

        Args:
            issues: List of critic issues
        """
        if not issues:
            self.log_widget.write("\n[green]✓ Critic found no issues[/green]")
            return

        self.log_widget.write("\n[bold]Critic Review:[/bold]")

        # Group by severity
        critical = [i for i in issues if i.severity == "Critical"]
        warnings = [i for i in issues if i.severity == "Warning"]
        suggestions = [i for i in issues if i.severity == "Suggestion"]

        if critical:
            self.log_widget.write("\n[red]Critical Issues:[/red]")
            for issue in critical[:3]:
                self.log_widget.write(f"  • {issue.section}: {issue.message}")
                if issue.action:
                    self.log_widget.write(f"    → {issue.action}")
            if len(critical) > 3:
                self.log_widget.write(
                    f"  [dim](and {len(critical) - 3} more critical issues)[/dim]"
                )

        if warnings:
            self.log_widget.write("\n[yellow]Warnings:[/yellow]")
            for issue in warnings[:3]:
                self.log_widget.write(f"  • {issue.section}: {issue.message}")
            if len(warnings) > 3:
                self.log_widget.write(f"  [dim](and {len(warnings) - 3} more warnings)[/dim]")

        if suggestions:
            self.log_widget.write(f"\n[dim]{len(suggestions)} suggestions available[/dim]")

    def show_diff_preview(self, diff_text: str, max_lines: int = 30) -> None:
        """
        Display diff preview with safe rendering.

        Args:
            diff_text: Unified diff text
            max_lines: Maximum lines to show
        """
        self.log_widget.write("\n[bold]Changes Preview:[/bold]")

        lines = diff_text.split("\n")
        shown_lines = lines[:max_lines]

        # Display diff without markup to avoid rendering issues
        for line in shown_lines:
            # Use plain text for diffs to avoid markup issues
            self.log_widget.write(line)

        if len(lines) > max_lines:
            self.log_widget.write(f"\n[dim]... ({len(lines) - max_lines} more lines) ...[/dim]")

    def show_completion(
        self, success: bool, path: str | None = None, log_path: str | None = None
    ) -> None:
        """
        Show completion status.

        Args:
            success: Whether synthesis was successful
            path: Path to the created/updated file
            log_path: Path to the log file
        """
        if success:
            self.log_widget.write("\n[green bold]✓ Synthesis Complete[/green bold]")
            if path:
                self.log_widget.write(f"  File: {path}")
        else:
            self.log_widget.write("\n[yellow]⚠ Synthesis cancelled[/yellow]")

        if log_path:
            self.log_widget.write(f"\n[dim]Log: {log_path}[/dim]")
