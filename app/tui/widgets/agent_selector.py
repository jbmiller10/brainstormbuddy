"""Agent selection widget for choosing Claude Code agents."""

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from app.llm.agents import AgentSpec


class AgentCard(Container):
    """Display card for a single agent."""

    def __init__(self, agent: AgentSpec, selected: bool = False) -> None:
        """
        Initialize the agent card.

        Args:
            agent: The agent specification to display
            selected: Whether this agent is currently selected
        """
        super().__init__(classes="agent-card")
        self.agent = agent
        self.selected = selected
        if selected:
            self.add_class("selected")

    def compose(self) -> ComposeResult:
        """Create the card content."""
        yield Label(f"[bold]{self.agent.name}[/bold]", classes="agent-name")
        yield Label(self.agent.description, classes="agent-description")
        if self.agent.tools:
            tools_str = ", ".join(self.agent.tools)
            yield Label(f"[dim]Tools: {tools_str}[/dim]", classes="agent-tools")
        else:
            yield Label("[dim]Tools: None[/dim]", classes="agent-tools")


class AgentSelector(ModalScreen[AgentSpec | None]):
    """Modal for selecting an agent for a session."""

    DEFAULT_CSS = """
    AgentSelector {
        align: center middle;
    }

    AgentSelector > Container {
        width: 80;
        height: auto;
        max-height: 80%;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    .modal-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .agent-list {
        height: auto;
        max-height: 20;
        margin-bottom: 1;
    }

    .agent-card {
        padding: 1;
        margin-bottom: 1;
        border: solid $primary 50%;
    }

    .agent-card.selected {
        border: solid $accent;
        background: $boost;
    }

    .agent-card:hover {
        background: $boost;
    }

    .agent-name {
        margin-bottom: 0;
    }

    .agent-description {
        margin-bottom: 0;
    }

    .agent-tools {
        margin-top: 0;
    }

    .final-tools {
        border: solid $primary 50%;
        padding: 1;
        margin-bottom: 1;
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
        agents: list[AgentSpec],
        stage_allowed: list[str],
        stage_denied: list[str],
    ) -> None:
        """
        Initialize the agent selector.

        Args:
            agents: List of available agents
            stage_allowed: Tools allowed by the current stage
            stage_denied: Tools denied by the current stage
        """
        super().__init__()
        self.agents = agents
        self.stage_allowed = stage_allowed
        self.stage_denied = stage_denied
        self.selected_agent: AgentSpec | None = None
        self.agent_cards: list[AgentCard] = []

    def compose(self) -> ComposeResult:
        """Create the selector UI."""
        with Container():
            yield Static("[bold]Select Agent (Optional)[/bold]", classes="modal-title")
            yield Static(
                "[dim]Choose an agent to assist with this session, or continue without one.[/dim]",
                classes="modal-subtitle",
            )

            # Agent list
            with VerticalScroll(classes="agent-list"):
                for agent in self.agents:
                    card = AgentCard(agent, selected=False)
                    self.agent_cards.append(card)
                    yield card

            # Final tools preview
            yield Container(
                Static("[bold]Final Tool Permissions:[/bold]"),
                Static(self._compute_final_tools_text(), id="final-tools-text"),
                classes="final-tools",
            )

            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("Select", variant="primary", id="select-button")
                yield Button("No Agent", variant="default", id="no-agent-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    def _compute_final_tools_text(self) -> str:
        """Compute the final tools text based on current selection."""
        if self.selected_agent and self.selected_agent.tools:
            # Intersection of stage allowed and agent tools
            allowed = set(self.stage_allowed).intersection(set(self.selected_agent.tools))
        else:
            # Just stage allowed
            allowed = set(self.stage_allowed)

        # Remove denied tools
        final = allowed - set(self.stage_denied)

        if final:
            return f"[green]{', '.join(sorted(final))}[/green]"
        else:
            return "[red]None (no tools available)[/red]"

    def on_click(self, event: events.Click) -> None:
        """Handle clicks on agent cards."""
        # Check if click was on an agent card
        if event.widget is None:
            return

        for card in self.agent_cards:
            if card in event.widget.ancestors_with_self:
                # Deselect all cards
                for c in self.agent_cards:
                    c.remove_class("selected")
                    c.selected = False

                # Select the clicked card
                card.add_class("selected")
                card.selected = True
                self.selected_agent = card.agent

                # Update final tools preview
                tools_text = self.query_one("#final-tools-text", Static)
                tools_text.update(self._compute_final_tools_text())
                break

    @on(Button.Pressed, "#select-button")
    def handle_select(self) -> None:
        """Handle select button - return selected agent."""
        if self.selected_agent:
            self.dismiss(self.selected_agent)
        else:
            # No agent selected, treat as "No Agent"
            self.dismiss(None)

    @on(Button.Pressed, "#no-agent-button")
    def handle_no_agent(self) -> None:
        """Handle no agent button - return None."""
        self.dismiss(None)

    @on(Button.Pressed, "#cancel-button")
    def handle_cancel(self) -> None:
        """Handle cancel button - dismiss with None (cancellation)."""
        # In this context, we'll treat cancel as "no agent" to avoid blocking
        self.dismiss(None)
