"""Session controller for managing brainstorming sessions and Claude interactions."""

from pathlib import Path

from app.files.diff import apply_patch, compute_patch, generate_diff_preview
from app.llm.claude_client import ClaudeClient, Event, FakeClaudeClient, MessageDone, TextDelta
from app.llm.sessions import get_policy
from app.tui.widgets.kernel_approval import KernelApprovalModal
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
        self.pending_kernel_content: str | None = None
        self.project_slug: str | None = None

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

    async def start_kernel_session(
        self, project_slug: str, initial_idea: str = "Build a better app"
    ) -> None:
        """
        Start a kernel stage session.

        Args:
            project_slug: The project identifier/slug
            initial_idea: The user's refined brainstorming idea
        """
        self.current_stage = "kernel"
        self.project_slug = project_slug
        self.pending_kernel_content = ""

        # Get kernel policy
        policy = get_policy("kernel")

        # Read system prompt
        system_prompt_content = ""
        if policy.system_prompt_path.exists():
            system_prompt_content = policy.system_prompt_path.read_text()

        # Clear viewer and show starting message
        self.viewer.clear()
        self.viewer.write("[bold cyan]Starting Kernel Session[/bold cyan]\n")
        self.viewer.write(f"[dim]Project: {project_slug}[/dim]\n")
        self.viewer.write("[dim]Generating kernel document...[/dim]\n\n")

        # Stream events from client
        try:
            async for event in self.client.stream(
                prompt=initial_idea,
                system_prompt=system_prompt_content,
                allowed_tools=policy.allowed_tools,
                denied_tools=policy.denied_tools,
                permission_mode=policy.permission_mode,
            ):
                await self._handle_kernel_event(event)
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

    async def _handle_kernel_event(self, event: Event) -> None:
        """
        Handle a stream event from the Claude client during kernel stage.

        Args:
            event: The event to handle
        """
        if isinstance(event, TextDelta):
            # Accumulate text for the kernel content
            if self.pending_kernel_content is not None:
                self.pending_kernel_content += event.text
            # Display text chunks as they arrive
            self.viewer.write(event.text, scroll_end=True)
        elif isinstance(event, MessageDone):
            # Session complete - show diff preview
            self.viewer.write("\n[dim]Kernel generation complete.[/dim]\n")
            await self._show_kernel_diff_preview()

    async def _show_kernel_diff_preview(self) -> None:
        """Show a diff preview and prompt for approval."""
        if not self.project_slug or not self.pending_kernel_content:
            self.viewer.write("[red]Error: No kernel content to preview[/red]\n")
            return

        # Construct kernel file path
        kernel_path = Path("projects") / self.project_slug / "kernel.md"

        # Read existing content if file exists
        old_content = ""
        if kernel_path.exists():
            old_content = kernel_path.read_text()

        # Generate diff preview
        diff_preview = generate_diff_preview(
            old_content,
            self.pending_kernel_content,
            context_lines=3,
            from_label=f"projects/{self.project_slug}/kernel.md (current)",
            to_label=f"projects/{self.project_slug}/kernel.md (proposed)",
        )

        # Get the app instance through the viewer
        app = self.viewer.app

        # Show modal and wait for response
        modal = KernelApprovalModal(diff_preview, self.project_slug)
        approved = await app.push_screen_wait(modal)

        if approved:
            self.approve_kernel_changes()
        else:
            self.reject_kernel_changes()

    def approve_kernel_changes(self) -> bool:
        """
        Apply the pending kernel changes atomically.

        Returns:
            True if changes were applied successfully, False otherwise
        """
        if not self.project_slug or not self.pending_kernel_content:
            self.viewer.write("[red]Error: No pending changes to apply[/red]\n")
            return False

        try:
            # Construct kernel file path
            kernel_path = Path("projects") / self.project_slug / "kernel.md"

            # Ensure parent directory exists
            kernel_path.parent.mkdir(parents=True, exist_ok=True)

            # Read existing content if file exists
            old_content = ""
            if kernel_path.exists():
                old_content = kernel_path.read_text()

            # Compute and apply patch
            patch = compute_patch(old_content, self.pending_kernel_content)
            apply_patch(kernel_path, patch)

            self.viewer.write(
                f"\n[green]✓ Kernel successfully written to projects/{self.project_slug}/kernel.md[/green]\n"
            )

            # Clear pending content
            self.pending_kernel_content = None
            return True

        except Exception as e:
            self.viewer.write(
                f"\n[red]Error applying changes: {e}[/red]\n"
                "[yellow]Original file remains unchanged.[/yellow]\n"
            )
            return False

    def reject_kernel_changes(self) -> None:
        """Reject the pending kernel changes."""
        self.viewer.write("\n[yellow]Changes rejected. Kernel file remains unchanged.[/yellow]\n")
        self.pending_kernel_content = None
