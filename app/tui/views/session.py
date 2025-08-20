"""Session controller for managing brainstorming sessions and Claude interactions."""

from pathlib import Path

from app.files.diff import apply_patch, compute_patch, generate_diff_preview
from app.files.markdown import extract_section_paragraph
from app.files.workstream import create_workstream_batch
from app.llm.agents import AgentSpec, load_agent_specs
from app.llm.claude_client import (
    ClaudeClient,
    Event,
    FakeClaudeClient,
    MessageDone,
    TextDelta,
)
from app.llm.sessions import get_policy, merge_agent_policy
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
        # Cache loaded agent specs
        self._agent_specs: list[AgentSpec] | None = None
        self.selected_agent: AgentSpec | None = None

    def get_available_agents(self) -> list[AgentSpec]:
        """
        Get available agent specifications.

        Returns:
            List of loaded agent specs
        """
        if self._agent_specs is None:
            self._agent_specs = load_agent_specs("app.llm.agentspecs")
        return self._agent_specs

    async def start_clarify_session(
        self, initial_prompt: str = "I want to build a better app", agent: AgentSpec | None = None
    ) -> None:
        """
        Start a clarify stage session.

        Args:
            initial_prompt: The user's initial brainstorming idea
            agent: Optional agent specification to use
        """
        self.current_stage = "clarify"
        self.selected_agent = agent

        # Get clarify policy and merge with agent if provided
        policy = get_policy("clarify")
        if agent:
            policy = merge_agent_policy(policy, agent)

        # Read system prompt
        system_prompt_content = ""
        if policy.system_prompt_path.exists():
            system_prompt_content = policy.system_prompt_path.read_text()

        # Clear viewer and show starting message
        self.viewer.clear()
        self.viewer.write("[bold cyan]Starting Clarify Session[/bold cyan]\n")
        if agent:
            self.viewer.write(f"[dim]Using agent: {agent.name}[/dim]\n")
        self.viewer.write(
            f"[dim]Allowed tools: {', '.join(policy.allowed_tools) if policy.allowed_tools else 'None'}[/dim]\n"
        )
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
        self,
        project_slug: str,
        initial_idea: str = "Build a better app",
        agent: AgentSpec | None = None,
    ) -> None:
        """
        Start a kernel stage session.

        Args:
            project_slug: The project identifier/slug
            initial_idea: The user's refined brainstorming idea
            agent: Optional agent specification to use
        """
        self.current_stage = "kernel"
        self.project_slug = project_slug
        self.pending_kernel_content = ""
        self.selected_agent = agent

        # Get kernel policy and merge with agent if provided
        policy = get_policy("kernel")
        if agent:
            policy = merge_agent_policy(policy, agent)

        # Read system prompt
        system_prompt_content = ""
        if policy.system_prompt_path.exists():
            system_prompt_content = policy.system_prompt_path.read_text()

        # Clear viewer and show starting message
        self.viewer.clear()
        self.viewer.write("[bold cyan]Starting Kernel Session[/bold cyan]\n")
        self.viewer.write(f"[dim]Project: {project_slug}[/dim]\n")
        if agent:
            self.viewer.write(f"[dim]Using agent: {agent.name}[/dim]\n")
        self.viewer.write(
            f"[dim]Allowed tools: {', '.join(policy.allowed_tools) if policy.allowed_tools else 'None'}[/dim]\n"
        )
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

    async def generate_workstreams(self, project_slug: str = "default-project") -> None:
        """
        Generate workstream documents (outline and elements) for a project.

        Args:
            project_slug: The project identifier/slug
        """
        self.project_slug = project_slug

        # Clear viewer and show starting message
        self.viewer.clear()
        self.viewer.write("[bold cyan]Generating Workstream Documents[/bold cyan]\n")
        self.viewer.write(f"[dim]Project: {project_slug}[/dim]\n\n")

        try:
            # Get project path
            project_path = Path("projects") / project_slug

            # Check if kernel exists and read it for summary
            kernel_summary = None
            kernel_path = project_path / "kernel.md"
            if kernel_path.exists():
                kernel_content = kernel_path.read_text()
                # Use robust extraction utility to get the Core Concept paragraph
                kernel_summary = extract_section_paragraph(kernel_content, "## Core Concept")

            # Create batch with all workstream documents
            self.viewer.write("[dim]Creating batch with outline and element documents...[/dim]\n")
            batch = create_workstream_batch(
                project_path, project_slug, kernel_summary=kernel_summary
            )

            if not batch:
                self.viewer.write(
                    "[yellow]No changes needed - all files are up to date.[/yellow]\n"
                )
                return

            # Generate and show preview
            self.viewer.write("\n[bold]Preview of changes:[/bold]\n")
            preview = batch.generate_preview(context_lines=2)

            # Limit preview display for readability
            preview_lines = preview.split("\n")
            if len(preview_lines) > 50:
                # Show first 40 lines and summary
                self.viewer.write("\n".join(preview_lines[:40]))
                self.viewer.write(f"\n[dim]... ({len(preview_lines) - 40} more lines) ...[/dim]\n")
            else:
                self.viewer.write(preview)

            self.viewer.write(f"\n[dim]Total files to create/update: {len(batch)}[/dim]\n")

            # Get the app instance through the viewer
            app = self.viewer.app

            # Create a simple approval modal (reuse KernelApprovalModal for now)
            # In production, we'd create a dedicated WorkstreamApprovalModal
            modal = KernelApprovalModal(preview, project_slug)
            approved = await app.push_screen_wait(modal)

            if approved:
                # Apply all changes atomically
                self.viewer.write("\n[dim]Applying changes atomically...[/dim]\n")
                patches = batch.apply()

                self.viewer.write(
                    f"\n[green]✓ Successfully created/updated {len(patches)} files:[/green]\n"
                )
                for change in batch.changes:
                    status = "created" if change.is_new_file else "updated"
                    self.viewer.write(
                        f"  • {change.path.relative_to(Path('projects'))} ({status})\n"
                    )
            else:
                self.viewer.write("\n[yellow]Changes rejected. No files were modified.[/yellow]\n")

        except Exception as e:
            self.viewer.write(f"\n[red]Error generating workstreams: {e}[/red]\n")
            self.viewer.write("[yellow]No files were modified.[/yellow]\n")

    async def start_synthesis_session(
        self,
        project_slug: str,
        workstream: str,
        agent: AgentSpec | None = None,
        run_critic: bool = False,
    ) -> None:
        """
        Start a synthesis stage session.

        Args:
            project_slug: The project identifier/slug
            workstream: The workstream to synthesize
            agent: Optional agent specification to use
            run_critic: Whether to run critic review
        """
        from app.synthesis import SynthesisController
        from app.synthesis.logger import SynthesisLogger

        self.current_stage = "synthesis"
        self.project_slug = project_slug
        self.selected_agent = agent

        # Get synthesis policy and merge with agent if provided
        policy = get_policy("synthesis")
        if agent:
            policy = merge_agent_policy(policy, agent)

        # Clear viewer and show starting message
        self.viewer.clear()
        self.viewer.write("[bold cyan]Starting Synthesis Session[/bold cyan]\n")
        self.viewer.write(f"[dim]Project: {project_slug}[/dim]\n")
        self.viewer.write(f"[dim]Workstream: {workstream}[/dim]\n")
        if agent:
            self.viewer.write(f"[dim]Using agent: {agent.name}[/dim]\n")
        self.viewer.write(
            f"[dim]Allowed tools: {', '.join(policy.allowed_tools) if policy.allowed_tools else 'None'}[/dim]\n"
        )
        self.viewer.write("[dim]Synthesizing requirements...[/dim]\n\n")

        # Create synthesis controller and logger
        logger = SynthesisLogger()
        controller = SynthesisController(project_slug, self.client, logger)

        try:
            # Run synthesis
            result = await controller.synthesize_workstream(
                workstream=workstream,
                run_critic=run_critic,
                auto_fix=False,  # Let user decide on auto-fix
            )

            # Display validation results
            if result.validation_errors:
                self.viewer.write("\n[yellow]⚠ Validation issues found:[/yellow]\n")
                for error in result.validation_errors:
                    if error.line_number:
                        self.viewer.write(f"  Line {error.line_number}: {error.message}\n")
                    else:
                        self.viewer.write(f"  {error.section}: {error.message}\n")

            # Display critic results if run
            if result.critic_issues:
                self.viewer.write("\n[bold]Critic Review:[/bold]\n")

                # Group by severity
                critical = [i for i in result.critic_issues if i.severity == "Critical"]
                warnings = [i for i in result.critic_issues if i.severity == "Warning"]
                suggestions = [i for i in result.critic_issues if i.severity == "Suggestion"]

                if critical:
                    self.viewer.write("[red]Critical Issues:[/red]\n")
                    for issue in critical:
                        self.viewer.write(f"  • {issue.section}: {issue.message}\n")
                        if issue.action:
                            self.viewer.write(f"    → {issue.action}\n")

                if warnings:
                    self.viewer.write("[yellow]Warnings:[/yellow]\n")
                    for issue in warnings:
                        self.viewer.write(f"  • {issue.section}: {issue.message}\n")
                        if issue.action:
                            self.viewer.write(f"    → {issue.action}\n")

                if suggestions:
                    self.viewer.write("[dim]Suggestions:[/dim]\n")
                    for issue in suggestions[:3]:  # Show only first 3 suggestions
                        self.viewer.write(f"  • {issue.section}: {issue.message}\n")
                    if len(suggestions) > 3:
                        self.viewer.write(
                            f"  [dim](and {len(suggestions) - 3} more suggestions)[/dim]\n"
                        )

            # Show diff preview
            self.viewer.write("\n[bold]Preview of changes:[/bold]\n")
            preview_lines = result.diff_preview.split("\n")
            if len(preview_lines) > 40:
                self.viewer.write("\n".join(preview_lines[:35]))
                self.viewer.write(f"\n[dim]... ({len(preview_lines) - 35} more lines) ...[/dim]\n")
            else:
                self.viewer.write(result.diff_preview)

            # Get approval
            app = self.viewer.app
            modal = KernelApprovalModal(result.diff_preview, project_slug)
            approved = await app.push_screen_wait(modal)

            if approved:
                # Apply synthesis
                await controller.apply_synthesis(result)
                self.viewer.write(
                    f"\n[green]✓ Successfully synthesized {workstream} to elements/{workstream}.md[/green]\n"
                )

                # Log decision
                await logger.log_decision(
                    stage="synthesis",
                    decision="applied_as_is"
                    if not result.validation_errors
                    else "applied_with_fixes",
                    details={
                        "workstream": workstream,
                        "validation_errors": len(result.validation_errors),
                    },
                )
            else:
                self.viewer.write(
                    "\n[yellow]Synthesis rejected. No files were modified.[/yellow]\n"
                )
                await logger.log_decision(
                    stage="synthesis",
                    decision="canceled",
                    details={"workstream": workstream},
                )

            # Show log location
            self.viewer.write(f"\n[dim]Log saved to: {logger.get_log_path()}[/dim]\n")

        except FileNotFoundError as e:
            self.viewer.write(f"\n[red]Error: {e}[/red]\n")
            self.viewer.write("[yellow]Please run the Kernel stage first.[/yellow]\n")
        except Exception as e:
            self.viewer.write(f"\n[red]Error during synthesis: {e}[/red]\n")
