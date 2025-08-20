"""Research import view for pasting and storing external findings."""

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Static, TextArea

from app.research.db import ResearchDB
from app.research.ingest import Finding, parse_findings


class ResearchImportModal(ModalScreen[bool]):
    """Modal for importing research findings from external sources."""

    DEFAULT_CSS = """
    ResearchImportModal {
        align: center middle;
    }

    ResearchImportModal > Container {
        width: 95%;
        height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    .modal-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .paste-section {
        height: 12;
        margin-bottom: 1;
        border: solid $primary 50%;
        padding: 1;
    }

    .paste-area {
        height: 8;
        margin: 1 0;
    }

    .import-button-row {
        dock: bottom;
        height: 3;
        align: center middle;
    }

    .table-section {
        height: 1fr;
        margin-bottom: 1;
        border: solid $primary 50%;
        padding: 1;
    }

    .status-message {
        text-align: center;
        width: 100%;
        margin: 1 0;
        color: $success;
    }

    .button-row {
        dock: bottom;
        align: center middle;
        padding: 1 0;
    }

    .button-row Button {
        margin: 0 1;
    }

    .filter-section {
        height: auto;
        margin-bottom: 1;
        border: solid $primary 50%;
        padding: 1;
    }

    .filter-inputs {
        height: auto;
        margin: 1 0;
    }

    .filter-inputs Input {
        margin: 0 0 1 0;
    }

    .filter-button-row {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    .filter-button-row Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def __init__(
        self,
        workstream: str = "research",
        db_path: Path | None = None,
    ) -> None:
        """
        Initialize the research import modal.

        Args:
            workstream: Default workstream for imported findings
            db_path: Path to the research database
        """
        super().__init__()
        self.workstream = workstream
        self.db_path = db_path or Path("projects") / "default" / "research.db"
        self.status_message = ""
        self.findings: list[Finding] = []
        # Filter state
        self.filter_workstream: str = ""
        self.filter_tags: list[str] = []
        self.filter_min_confidence: float | None = None

    def compose(self) -> ComposeResult:
        """Create the research import UI."""
        with Container():
            yield Static("[bold]Import Research Findings[/bold]", classes="modal-title")
            yield Static(
                f"[dim]Default workstream: {self.workstream}[/dim]",
                classes="modal-subtitle",
            )

            # Paste area section
            with Container(classes="paste-section"):
                yield Static("[bold]Paste External Responses[/bold]", classes="section-title")
                yield Static(
                    "[dim]Supports markdown bullets or JSON array format[/dim]",
                    classes="section-subtitle",
                )
                yield TextArea(
                    "",
                    id="paste-area",
                    classes="paste-area",
                )
                with Horizontal(classes="import-button-row"):
                    yield Button("Import Findings", variant="primary", id="import-button")

            # Status message
            yield Static("", id="status-message", classes="status-message")

            # Filter section
            with Container(classes="filter-section"):
                yield Static("[bold]Filters[/bold]", classes="section-title")
                with Container(classes="filter-inputs"):
                    yield Input(
                        placeholder="Filter by workstream...",
                        id="filter-workstream",
                    )
                    yield Input(
                        placeholder="Filter by tags (comma-separated)...",
                        id="filter-tags",
                    )
                    yield Input(
                        placeholder="Minimum confidence (0.0-1.0)...",
                        id="filter-confidence",
                    )
                with Horizontal(classes="filter-button-row"):
                    yield Button("Apply Filters", variant="primary", id="apply-filters")
                    yield Button("Clear Filters", variant="default", id="clear-filters")

            # Table section
            with ScrollableContainer(classes="table-section"):
                yield Static("[bold]Current Findings[/bold]", classes="section-title")
                table = DataTable[str](id="findings-table")
                table.add_columns("Claim", "URL", "Confidence", "Tags", "Workstream")
                yield table

            # Action buttons
            with Horizontal(classes="button-row"):
                yield Button("Close", variant="default", id="close-button")

    async def on_mount(self) -> None:
        """Load existing findings when modal opens."""
        await self.refresh_table()

    async def refresh_table(self) -> None:
        """Refresh the findings table with data from the database."""
        table = self.query_one("#findings-table", DataTable)
        table.clear()

        # Load findings from database
        if self.db_path.exists():
            async with ResearchDB(self.db_path) as db:
                # Apply database-level filters
                findings = await db.list_findings(
                    workstream=self.filter_workstream if self.filter_workstream else None,
                    min_confidence=self.filter_min_confidence,
                    limit=100,
                )

                # Apply client-side tag filtering
                if self.filter_tags:
                    filtered_findings = []
                    for finding in findings:
                        finding_tags = finding.get("tags", [])
                        # Check if any filter tag is in the finding's tags
                        if any(tag in finding_tags for tag in self.filter_tags):
                            filtered_findings.append(finding)
                    findings = filtered_findings

                for finding in findings:
                    tags_str = ", ".join(finding.get("tags", []))
                    confidence_str = f"{finding['confidence']:.0%}"
                    table.add_row(
                        finding["claim"][:80] + ("..." if len(finding["claim"]) > 80 else ""),
                        finding["url"][:40] + ("..." if len(finding["url"]) > 40 else ""),
                        confidence_str,
                        tags_str[:30] + ("..." if len(tags_str) > 30 else ""),
                        finding.get("workstream", ""),
                    )

    @on(Button.Pressed, "#import-button")
    async def handle_import(self) -> None:
        """Process pasted content and import findings."""
        text_area = self.query_one("#paste-area", TextArea)
        content = text_area.text.strip()

        if not content:
            self.update_status("No content to import", is_error=True)
            return

        try:
            # Parse findings from pasted content
            parsed_findings = parse_findings(content, self.workstream)

            if not parsed_findings:
                self.update_status("No valid findings found in pasted content", is_error=True)
                return

            # Store findings in database
            added_count = 0
            skipped_count = 0

            async with ResearchDB(self.db_path) as db:
                # Get existing findings for duplicate check
                existing = await db.list_findings(limit=1000)
                existing_keys = {(f["claim"].lower().strip(), f["url"]) for f in existing}

                for finding in parsed_findings:
                    key = (finding.claim.lower().strip(), finding.url)
                    if key in existing_keys:
                        skipped_count += 1
                    else:
                        await db.insert_finding(
                            url=finding.url,
                            source_type=finding.source_type,
                            claim=finding.claim,
                            evidence=finding.evidence,
                            confidence=finding.confidence,
                            tags=finding.tags,
                            workstream=finding.workstream,
                        )
                        added_count += 1

            # Clear the text area
            text_area.text = ""

            # Update status and refresh table
            self.update_status(
                f"Import complete: {added_count} added, {skipped_count} skipped (duplicates)"
            )
            await self.refresh_table()

        except Exception as e:
            self.update_status(f"Import failed: {str(e)}", is_error=True)

    def update_status(self, message: str, is_error: bool = False) -> None:
        """Update the status message."""
        status_widget = self.query_one("#status-message", Static)
        if is_error:
            status_widget.update(f"[red]{message}[/red]")
        else:
            status_widget.update(f"[green]{message}[/green]")

    @on(Button.Pressed, "#close-button")
    def handle_close(self) -> None:
        """Close the modal."""
        self.dismiss(True)

    @on(Button.Pressed, "#apply-filters")
    async def handle_apply_filters(self) -> None:
        """Apply the current filter values."""
        # Get filter values from inputs
        workstream_input = self.query_one("#filter-workstream", Input)
        tags_input = self.query_one("#filter-tags", Input)
        confidence_input = self.query_one("#filter-confidence", Input)

        # Update filter state
        self.filter_workstream = workstream_input.value.strip()

        # Parse tags (comma-separated)
        tags_text = tags_input.value.strip()
        if tags_text:
            self.filter_tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        else:
            self.filter_tags = []

        # Parse confidence (validate it's between 0.0 and 1.0)
        confidence_text = confidence_input.value.strip()
        if confidence_text:
            try:
                confidence = float(confidence_text)
                if 0.0 <= confidence <= 1.0:
                    self.filter_min_confidence = confidence
                    self.update_status("Filters applied", is_error=False)
                else:
                    self.update_status("Confidence must be between 0.0 and 1.0", is_error=True)
                    return
            except ValueError:
                self.update_status("Invalid confidence value", is_error=True)
                return
        else:
            self.filter_min_confidence = None

        # Refresh the table with filters
        await self.refresh_table()

    @on(Button.Pressed, "#clear-filters")
    async def handle_clear_filters(self) -> None:
        """Clear all filters and reset inputs."""
        # Clear filter state
        self.filter_workstream = ""
        self.filter_tags = []
        self.filter_min_confidence = None

        # Clear input fields
        workstream_input = self.query_one("#filter-workstream", Input)
        tags_input = self.query_one("#filter-tags", Input)
        confidence_input = self.query_one("#filter-confidence", Input)

        workstream_input.value = ""
        tags_input.value = ""
        confidence_input.value = ""

        self.update_status("Filters cleared", is_error=False)

        # Refresh the table without filters
        await self.refresh_table()

    def action_close(self) -> None:
        """Handle escape key to close."""
        self.dismiss(True)
