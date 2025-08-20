"""Command palette widget for executing app commands."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, OptionList


class CommandPalette(Container):
    """Command palette overlay for executing commands."""

    OPTION_FORMAT = "command: description"  # Expected format for option text

    DEFAULT_CSS = """
    CommandPalette {
        layer: modal;
        align: center middle;
        width: 60;
        height: auto;
        max-height: 20;
        background: $panel;
        border: thick $primary;
        padding: 1;
        display: none;
    }

    CommandPalette.visible {
        display: block;
    }

    CommandPalette Input {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close palette"),
    ]

    def __init__(self) -> None:
        """Initialize the command palette."""
        super().__init__(id="command-palette")
        self.commands = [
            ("new project", "Create a new brainstorming project"),
            ("clarify", "Enter clarify stage for current project"),
            ("kernel", "Define the kernel of your idea"),
            ("outline", "Create workstream outline"),
            ("generate workstreams", "Generate outline and element documents"),
            ("research import", "Import research findings"),
            ("synthesis", "Synthesize findings into final output"),
            ("export", "Export project to various formats"),
            ("domain settings", "Configure web domain allow/deny lists"),
        ]

    def compose(self) -> ComposeResult:
        """Compose the command palette UI."""
        yield Input(placeholder="Type a command...", id="command-input")
        options = [f"{cmd}: {desc}" for cmd, desc in self.commands]
        yield OptionList(*options, id="command-list")

    def show(self) -> None:
        """Show the command palette."""
        self.add_class("visible")
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

    def hide(self) -> None:
        """Hide the command palette."""
        self.remove_class("visible")

    def action_close(self) -> None:
        """Close the command palette."""
        self.hide()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        command = event.value.lower().strip()
        # Run the async command execution
        self.app.run_worker(self.execute_command(command))
        self.hide()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection from the list."""
        from textual import log

        # Extract command from the option text (format: "command: description")
        option_text = str(event.option.prompt)
        if ":" in option_text:
            command = option_text.split(":", 1)[0].strip().lower()
            # Run the async command execution
            self.app.run_worker(self.execute_command(command))
            self.hide()
        else:
            log.warning(
                f"Unexpected option format (expected '{self.OPTION_FORMAT}'): {option_text}"
            )

    async def execute_command(self, command: str) -> None:
        """Execute the selected command."""
        from textual import log

        log(f"Executing command: {command}")

        # Import here to avoid circular imports
        from app.llm.sessions import get_policy
        from app.tui.views.session import SessionController
        from app.tui.widgets.agent_selector import AgentSelector
        from app.tui.widgets.session_viewer import SessionViewer

        # Get the session viewer from the main screen
        viewer = self.app.query_one("#session-viewer", SessionViewer)

        # Create controller
        controller = SessionController(viewer)

        # Handle clarify command
        if command == "clarify":
            # Get stage policy for tool info
            policy = get_policy("clarify")

            # Show agent selector
            agents = controller.get_available_agents()
            selector = AgentSelector(agents, policy.allowed_tools, policy.denied_tools)
            selected_agent = await self.app.push_screen_wait(selector)

            # Run the async task using Textual's worker system
            self.app.run_worker(
                controller.start_clarify_session(agent=selected_agent), exclusive=True
            )

        # Handle kernel command
        elif command == "kernel":
            # For now, use a default project slug - in production, this would prompt for it
            project_slug = "default-project"
            initial_idea = "Build a better brainstorming app"

            # Get stage policy for tool info
            policy = get_policy("kernel")

            # Show agent selector
            agents = controller.get_available_agents()
            selector = AgentSelector(agents, policy.allowed_tools, policy.denied_tools)
            selected_agent = await self.app.push_screen_wait(selector)

            # Run the async task using Textual's worker system
            self.app.run_worker(
                controller.start_kernel_session(project_slug, initial_idea, agent=selected_agent),
                exclusive=True,
            )

        # Handle generate workstreams command
        elif command == "generate workstreams":
            # Run the async task using Textual's worker system
            self.app.run_worker(controller.generate_workstreams(), exclusive=True)

        # Handle domain settings command
        elif command == "domain settings":
            from pathlib import Path

            from app.tui.widgets.domain_editor import DomainEditor

            # Get current settings if they exist
            config_dir = Path(".") / ".claude"
            allow_domains = []
            deny_domains = []

            # Try to load existing settings
            settings_path = config_dir / "settings.json"
            if settings_path.exists():
                import json

                with open(settings_path, encoding="utf-8") as f:
                    settings = json.load(f)
                    if "permissions" in settings and "webDomains" in settings["permissions"]:
                        allow_domains = settings["permissions"]["webDomains"].get("allow", [])
                        deny_domains = settings["permissions"]["webDomains"].get("deny", [])

            # Show domain editor
            editor = DomainEditor(config_dir, allow_domains, deny_domains)
            await self.app.push_screen_wait(editor)

        # Handle research import command
        elif command == "research import":
            from pathlib import Path

            from app.tui.views.research import ResearchImportModal

            # Determine project path and workstream
            # For now, use default project - in production, this would be context-aware
            project_path = Path("projects") / "default"
            project_path.mkdir(parents=True, exist_ok=True)
            db_path = project_path / "research.db"

            # Show research import modal
            modal = ResearchImportModal(workstream="research", db_path=db_path)
            await self.app.push_screen_wait(modal)

        # Handle synthesis command
        elif command == "synthesis":
            from pathlib import Path

            from app.tui.widgets.agent_selector import AgentSelector

            # Get project slug (default for now)
            project_slug = "default-project"

            # Check if kernel exists
            kernel_path = Path("projects") / project_slug / "kernel.md"
            if not kernel_path.exists():
                viewer.write(
                    "[red]Error: Kernel not found.[/red]\n"
                    "[yellow]Please run the Kernel stage first to create the project kernel.[/yellow]\n"
                )
                return

            # Get available workstreams from elements directory
            elements_dir = Path("projects") / project_slug / "elements"
            workstreams = []

            # Check for existing element files
            if elements_dir.exists():
                for file in elements_dir.glob("*.md"):
                    workstreams.append(file.stem)

            # Also check outline for planned workstreams
            outline_path = Path("projects") / project_slug / "outline.md"
            if outline_path.exists():
                # Parse outline for workstream headers
                with open(outline_path, encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("## ") and "workstream" in line.lower():
                            # Extract workstream slug from header
                            ws_title = line[3:].strip()
                            ws_slug = ws_title.lower().replace(" ", "-").replace(":", "")
                            if ws_slug not in workstreams:
                                workstreams.append(ws_slug)

            # Default workstreams if none found
            if not workstreams:
                workstreams = ["ui-ux", "backend", "infrastructure", "research"]

            # For now, use the first workstream
            # In production, show a selector dialog
            workstream = workstreams[0] if workstreams else "main"

            # Show agent selector
            viewer.write(f"[dim]Synthesizing workstream: {workstream}[/dim]\n")

            # Get stage policy
            policy = get_policy("synthesis")

            # Show agent selector
            viewer.write("[dim]Select an agent for synthesis (or press ESC to skip):[/dim]\n")

            # Get available agents
            from app.llm.agents import load_agent_specs

            agents = load_agent_specs("app.llm.agentspecs")

            selector = AgentSelector(
                agents=agents,
                stage_allowed=policy.allowed_tools,
                stage_denied=policy.denied_tools,
            )
            selected_agent = await self.app.push_screen_wait(selector)

            # Check if critic should be run
            run_critic = True  # Default to running critic for synthesis

            # Start synthesis session
            self.app.run_worker(
                controller.start_synthesis_session(
                    project_slug, workstream, agent=selected_agent, run_critic=run_critic
                ),
                exclusive=True,
            )
