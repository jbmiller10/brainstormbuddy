"""Session controller for managing brainstorming sessions and Claude interactions."""

from app.llm.claude_client import ClaudeClient, Event, FakeClaudeClient, MessageDone, TextDelta
from app.llm.sessions import get_policy
from app.tui.widgets.session_viewer import SessionViewer


class SessionController:
    """Controller for managing brainstorming sessions."""

    def __init__(self, session_viewer: SessionViewer) -> None:
        """
        Initialize the session controller.

        Args:
            session_viewer: The widget to display session output
        """
        self.viewer = session_viewer
        self.client: ClaudeClient = FakeClaudeClient()
        self.current_stage: str | None = None

    async def start_clarify_session(
        self, initial_prompt: str = "I want to build a better app"
    ) -> None:
        """
        Start a clarify stage session.

        Args:
            initial_prompt: The user's initial brainstorming idea
        """
        self.current_stage = "clarify"

        # Get clarify policy
        policy = get_policy("clarify")

        # Read system prompt
        system_prompt_content = ""
        if policy.system_prompt_path.exists():
            system_prompt_content = policy.system_prompt_path.read_text()

        # Clear viewer and show starting message
        self.viewer.clear()
        self.viewer.write("[bold cyan]Starting Clarify Session[/bold cyan]\n")
        self.viewer.write("[dim]Generating clarifying questions...[/dim]\n\n")

        # Stream events from client
        try:
            async for event in self.client.stream(
                prompt=initial_prompt,
                system_prompt=system_prompt_content,
                allowed_tools=policy.allowed_tools,
                denied_tools=policy.denied_tools,
                permission_mode=policy.permission_mode,
            ):
                await self._handle_event(event)
        except Exception as e:
            self.viewer.write(f"\n[red]Error during session: {e}[/red]")

    async def _handle_event(self, event: Event) -> None:
        """
        Handle a stream event from the Claude client.

        Args:
            event: The event to handle
        """
        if isinstance(event, TextDelta):
            # Display text chunks as they arrive
            self.viewer.write(event.text, scroll_end=True)
        elif isinstance(event, MessageDone):
            # Session complete
            self.viewer.write(
                "\n[dim]Session complete. Consider these questions as you refine your idea.[/dim]"
            )
