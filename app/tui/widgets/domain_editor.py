"""Domain editor widget for managing web domain allow/deny lists."""

import json
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from app.permissions.settings_writer import write_project_settings


class DomainEditor(ModalScreen[bool]):
    """Modal for editing domain allow/deny lists."""

    DEFAULT_CSS = """
    DomainEditor {
        align: center middle;
    }

    DomainEditor > Container {
        width: 80;
        height: 40;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    .modal-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .config-path {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        color: $text-muted;
    }

    .domain-section {
        height: 12;
        margin-bottom: 1;
        border: solid $primary 50%;
        padding: 1;
    }

    .section-title {
        margin-bottom: 0;
    }

    .domain-list {
        height: 8;
        margin: 1 0;
    }

    .domain-input-row {
        dock: bottom;
        height: 3;
    }

    .button-row {
        dock: bottom;
        align: center middle;
        padding: 1 0;
    }

    .button-row Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        config_dir: Path | None = None,
        allow_domains: list[str] | None = None,
        deny_domains: list[str] | None = None,
    ) -> None:
        """
        Initialize the domain editor.

        Args:
            config_dir: Path to the configuration directory
            allow_domains: Initial list of allowed domains
            deny_domains: Initial list of denied domains
        """
        super().__init__()
        self.config_dir = config_dir or Path(".") / ".claude"
        self.allow_domains = allow_domains or []
        self.deny_domains = deny_domains or []

    def compose(self) -> ComposeResult:
        """Create the domain editor UI."""
        with Container():
            yield Static("[bold]Domain Allow/Deny Policy Editor[/bold]", classes="modal-title")
            yield Static(
                f"[dim]Config directory: {self.config_dir}[/dim]",
                classes="config-path",
            )

            # Allow domains section
            with Container(classes="domain-section"):
                yield Static("[bold]Allowed Domains[/bold]", classes="section-title")
                yield Static(
                    "[dim]Empty list means allow all domains (if web tools enabled)[/dim]",
                    classes="section-subtitle",
                )
                allow_list = ListView(id="allow-list", classes="domain-list")
                for domain in self.allow_domains:
                    allow_list.append(ListItem(Label(domain)))
                yield allow_list
                with Horizontal(classes="domain-input-row"):
                    yield Input(
                        placeholder="Add domain to allow list...",
                        id="allow-input",
                    )
                    yield Button("Add", variant="primary", id="add-allow")

            # Deny domains section
            with Container(classes="domain-section"):
                yield Static("[bold]Denied Domains[/bold]", classes="section-title")
                yield Static(
                    "[dim]Domains to explicitly deny even if allowed[/dim]",
                    classes="section-subtitle",
                )
                deny_list = ListView(id="deny-list", classes="domain-list")
                for domain in self.deny_domains:
                    deny_list.append(ListItem(Label(domain)))
                yield deny_list
                with Horizontal(classes="domain-input-row"):
                    yield Input(
                        placeholder="Add domain to deny list...",
                        id="deny-input",
                    )
                    yield Button("Add", variant="primary", id="add-deny")

            # Action buttons
            with Horizontal(classes="button-row"):
                yield Button("Save", variant="primary", id="save-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    @on(Button.Pressed, "#add-allow")
    def handle_add_allow(self) -> None:
        """Add domain to allow list."""
        input_widget = self.query_one("#allow-input", Input)
        domain = input_widget.value.strip()
        if domain and domain not in self.allow_domains:
            self.allow_domains.append(domain)
            allow_list = self.query_one("#allow-list", ListView)
            allow_list.append(ListItem(Label(domain)))
            input_widget.value = ""

    @on(Button.Pressed, "#add-deny")
    def handle_add_deny(self) -> None:
        """Add domain to deny list."""
        input_widget = self.query_one("#deny-input", Input)
        domain = input_widget.value.strip()
        if domain and domain not in self.deny_domains:
            self.deny_domains.append(domain)
            deny_list = self.query_one("#deny-list", ListView)
            deny_list.append(ListItem(Label(domain)))
            input_widget.value = ""

    @on(ListView.Selected)
    def handle_list_select(self, event: ListView.Selected) -> None:
        """Remove domain when clicked in list."""
        if event.list_view.id == "allow-list":
            if event.item:
                # Find index of the item to remove
                index = event.list_view.index
                if index is not None and index < len(self.allow_domains):
                    del self.allow_domains[index]
                    event.item.remove()
        elif event.list_view.id == "deny-list" and event.item:
            # Find index of the item to remove
            index = event.list_view.index
            if index is not None and index < len(self.deny_domains):
                del self.deny_domains[index]
                event.item.remove()

    @on(Button.Pressed, "#save-button")
    def handle_save(self) -> None:
        """Save domain settings."""
        # Update the settings file with new domain lists
        self._update_settings_with_domains()
        self.dismiss(True)

    @on(Button.Pressed, "#cancel-button")
    def handle_cancel(self) -> None:
        """Cancel without saving."""
        self.dismiss(False)

    def _update_settings_with_domains(self) -> None:
        """Update the settings file with the current domain lists."""
        # First, create/update the settings with our writer
        repo_root = self.config_dir.parent
        config_dir_name = self.config_dir.name

        # Write the base settings
        config_dir = write_project_settings(
            repo_root=repo_root,
            config_dir_name=config_dir_name,
        )

        # Now read the settings, update with our domains, and write back
        settings_path = config_dir / "settings.json"
        with open(settings_path, encoding="utf-8") as f:
            settings = json.load(f)

        # Update webDomains
        settings["permissions"]["webDomains"]["allow"] = self.allow_domains
        settings["permissions"]["webDomains"]["deny"] = self.deny_domains

        # Write back
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
