"""New project wizard for guided project creation."""

import re
from datetime import datetime
from enum import Enum

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static, TextArea

from app.core.state import get_app_state
from app.files.atomic import atomic_write_text
from app.files.project_meta import ProjectMeta
from app.files.scaffold import scaffold_project
from app.files.slug import ensure_unique_slug, slugify
from app.tui.controllers.onboarding_controller import OnboardingController
from app.tui.styles import get_common_css
from app.tui.widgets.kernel_approval import KernelApprovalModal


class WizardStep(Enum):
    """Wizard step enumeration."""

    PROJECT_NAME = 1
    BRAINDUMP = 2
    CLARIFY_QUESTIONS = 3
    ANSWERS = 4
    KERNEL_PROPOSAL = 5
    COMPLETE = 6


class NewProjectWizard(Screen[bool]):
    """Multi-step wizard for creating a new project."""

    # Configuration constants
    CLARIFY_QUESTIONS_COUNT = 5
    MAX_RETRY_ATTEMPTS = 2
    MIN_KERNEL_LENGTH = 100
    MAX_PROJECT_NAME_LENGTH = 100
    # Allow single character names and be more permissive with special chars
    PROJECT_NAME_PATTERN = r"^[\w][\w\s\-]*[\w]$|^[\w]$"

    # Use shared styles for consistent appearance
    DEFAULT_CSS = get_common_css("NewProjectWizard", center_align=True)

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
        Binding("ctrl+n", "next_step", "Next", show=False),
        Binding("ctrl+b", "prev_step", "Back", show=False),
        Binding("ctrl+enter", "next_step", "Next", show=False),
        Binding("tab", "focus_next", "Next Field", show=False),
        Binding("shift+tab", "focus_previous", "Previous Field", show=False),
    ]

    def __init__(self) -> None:
        """Initialize the wizard."""
        super().__init__()
        self.current_step = WizardStep.PROJECT_NAME
        self.controller = OnboardingController()

        # Wizard state
        self.project_name: str = ""
        self.project_slug: str = ""
        self.braindump: str = ""
        self.clarify_questions: list[str] = []
        self.answers: str = ""
        self.kernel_content: str = ""
        self._partial_project_created: bool = False

    def compose(self) -> ComposeResult:
        """Compose the wizard UI."""
        yield Header()
        with Container(classes="container"):
            yield Label("Create New Project", classes="title")
            yield Label("", id="step-indicator", classes="step-indicator")

            with VerticalScroll(classes="content-area", id="content-area"):
                # Content will be dynamically updated based on step
                pass

            with Horizontal(classes="button-container"):
                yield Button(
                    "Back",
                    variant="warning",
                    classes="back-button",
                    id="back-button",
                    disabled=True,
                )
                yield Button(
                    "Next",
                    variant="success",
                    classes="next-button",
                    id="next-button",
                )
                yield Button(
                    "Cancel",
                    variant="error",
                    classes="cancel-button",
                    id="cancel-button",
                )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the first step when mounted."""
        self.update_step_content()

    async def on_unmount(self) -> None:
        """Clean up resources when unmounting."""
        # If project was partially created but wizard was cancelled, clean up
        if self._partial_project_created and self.project_slug:
            try:
                import shutil
                from pathlib import Path

                project_path = Path("projects") / self.project_slug
                if project_path.exists() and not (project_path / "kernel.md").exists():
                    # Only remove if kernel.md doesn't exist (incomplete project)
                    shutil.rmtree(project_path)
                    self.log.debug(f"Cleaned up incomplete project: {self.project_slug}")
            except Exception as e:
                self.log.warning(f"Failed to clean up incomplete project: {e}")

    def update_step_content(self) -> None:
        """Update the content area based on current step."""
        content_area = self.query_one("#content-area", VerticalScroll)
        content_area.remove_children()

        # Update step indicator
        step_indicator = self.query_one("#step-indicator", Label)
        step_indicator.update(f"Step {self.current_step.value} of 5")

        # Update button states
        back_button = self.query_one("#back-button", Button)
        next_button = self.query_one("#next-button", Button)
        back_button.disabled = self.current_step == WizardStep.PROJECT_NAME

        if self.current_step == WizardStep.PROJECT_NAME:
            self.render_project_name_step(content_area)
        elif self.current_step == WizardStep.BRAINDUMP:
            self.render_braindump_step(content_area)
        elif self.current_step == WizardStep.CLARIFY_QUESTIONS:
            self.render_questions_step(content_area)
        elif self.current_step == WizardStep.ANSWERS:
            self.render_answers_step(content_area)
        elif self.current_step == WizardStep.KERNEL_PROPOSAL:
            self.render_kernel_step(content_area)
            next_button.label = "Accept"
            next_button.variant = "success"

    def render_project_name_step(self, container: VerticalScroll) -> None:
        """Render the project name input step."""
        container.mount(
            Label("Enter a name for your project:", classes="instructions"),
            Input(
                placeholder="My Awesome Project", value=self.project_name, id="project-name-input"
            ),
            Label("[dim]This will be used to create a unique project identifier[/dim]"),
        )
        # Focus the input
        self.call_after_refresh(self.focus_input)

    def render_braindump_step(self, container: VerticalScroll) -> None:
        """Render the braindump textarea step."""
        container.mount(
            Label("Describe your idea in detail:", classes="instructions"),
            Label("[dim]Don't worry about structure - just get your thoughts out![/dim]"),
            TextArea(
                self.braindump,
                id="braindump-textarea",
                tab_behavior="indent",
            ),
        )
        # Focus the textarea
        self.call_after_refresh(self.focus_textarea)

    def render_questions_step(self, container: VerticalScroll) -> None:
        """Render the clarifying questions display."""
        container.mount(
            Label("Please review these clarifying questions:", classes="instructions"),
            Label("[dim]You'll answer them all together in the next step[/dim]"),
        )

        with container:
            questions_container = Container(classes="questions-container")
            for question in self.clarify_questions:
                questions_container.mount(
                    Static(f"[bold]{question}[/bold]", classes="question-item")
                )
            container.mount(questions_container)

    def render_answers_step(self, container: VerticalScroll) -> None:
        """Render the answers input step."""
        container.mount(
            Label("Answer the clarifying questions:", classes="instructions"),
            Label("[dim]Provide a consolidated response addressing all questions[/dim]"),
            TextArea(
                self.answers,
                id="answers-textarea",
                tab_behavior="indent",
            ),
        )
        # Focus the textarea
        self.call_after_refresh(self.focus_textarea)

    def render_kernel_step(self, container: VerticalScroll) -> None:
        """Render the kernel proposal review."""
        container.mount(
            Label("Review your project kernel:", classes="instructions"),
            Label("[dim]This captures the essence of your project[/dim]"),
            Static(self.kernel_content, markup=False),
        )

    def focus_input(self) -> None:
        """Focus the project name input with error logging."""
        try:
            input_widget = self.query_one("#project-name-input", Input)
            input_widget.focus()
        except Exception as e:
            self.log.debug(f"Failed to focus input: {e}")

    def focus_textarea(self) -> None:
        """Focus the active textarea with error logging."""
        try:
            if self.current_step == WizardStep.BRAINDUMP:
                textarea = self.query_one("#braindump-textarea", TextArea)
            elif self.current_step == WizardStep.ANSWERS:
                textarea = self.query_one("#answers-textarea", TextArea)
            else:
                return
            textarea.focus()
        except Exception as e:
            self.log.debug(f"Failed to focus textarea: {e}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "next-button":
            await self.action_next_step()
        elif event.button.id == "back-button":
            self.action_prev_step()
        elif event.button.id == "cancel-button":
            self.action_cancel()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes with improved validation."""
        if event.input.id == "project-name-input":
            self.project_name = event.value
            # Validate input in real-time with improved regex
            value = event.value.strip()
            if value:
                if len(value) > self.MAX_PROJECT_NAME_LENGTH:
                    self.notify(
                        f"Project name too long (max {self.MAX_PROJECT_NAME_LENGTH} characters)",
                        severity="warning",
                    )
                elif not re.match(self.PROJECT_NAME_PATTERN, value):
                    self.notify(
                        "Project name must start and end with letters/numbers/underscore",
                        severity="warning",
                    )

    async def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle textarea changes."""
        if event.text_area.id == "braindump-textarea":
            self.braindump = event.text_area.text
        elif event.text_area.id == "answers-textarea":
            self.answers = event.text_area.text

    async def action_next_step(self) -> None:
        """Move to the next wizard step."""
        if self.current_step == WizardStep.PROJECT_NAME:
            # Validate and generate slug
            if not self.project_name.strip():
                self.notify("Please enter a project name", severity="error")
                return

            # Additional validation for filesystem safety with improved regex
            name = self.project_name.strip()
            if len(name) > self.MAX_PROJECT_NAME_LENGTH:
                self.notify(
                    f"Project name too long (max {self.MAX_PROJECT_NAME_LENGTH} characters)",
                    severity="error",
                )
                return
            if not re.match(self.PROJECT_NAME_PATTERN, name):
                self.notify(
                    "Project name must start and end with letters/numbers/underscore",
                    severity="error",
                )
                return

            # Generate unique slug with error handling
            try:
                self.project_slug = ensure_unique_slug(slugify(self.project_name))
            except TimeoutError:
                self.notify("Project creation is locked, please try again", severity="error")
                return
            except Exception as e:
                self.notify(f"Error creating project identifier: {str(e)[:50]}", severity="error")
                return
            self.current_step = WizardStep.BRAINDUMP

        elif self.current_step == WizardStep.BRAINDUMP:
            # Validate braindump
            if not self.braindump.strip():
                self.notify("Please describe your idea", severity="error")
                return

            # Generate clarifying questions with retry
            self.notify("Generating clarifying questions...")
            questions_generated = False
            for attempt in range(self.MAX_RETRY_ATTEMPTS):
                try:
                    self.clarify_questions = self.controller.generate_clarify_questions(
                        self.braindump, count=self.CLARIFY_QUESTIONS_COUNT
                    )
                    questions_generated = True
                    break
                except TimeoutError:
                    if attempt == 0:
                        self.notify("Request timed out, retrying...", severity="warning")
                        continue
                    self.notify(
                        "Using contextual questions based on your braindump",
                        severity="information",
                    )
                    # Generate dynamic fallback questions based on braindump content
                    self.clarify_questions = self._generate_fallback_questions()
                    questions_generated = True
                    break
                except Exception as e:
                    self.notify(f"Failed to generate questions: {e}", severity="error")
                    return

            if not questions_generated:
                return

            self.current_step = WizardStep.CLARIFY_QUESTIONS

        elif self.current_step == WizardStep.CLARIFY_QUESTIONS:
            self.current_step = WizardStep.ANSWERS

        elif self.current_step == WizardStep.ANSWERS:
            # Validate answers
            if not self.answers.strip():
                self.notify("Please answer the questions", severity="error")
                return

            # Generate kernel proposal with retry
            self.notify("Generating project kernel...")
            kernel_generated = False
            for attempt in range(self.MAX_RETRY_ATTEMPTS):
                try:
                    self.kernel_content = self.controller.orchestrate_kernel_generation(
                        self.braindump, self.answers
                    )
                    kernel_generated = True
                    break
                except TimeoutError:
                    if attempt == 0:
                        self.notify("Request timed out, retrying...", severity="warning")
                        continue
                    self.notify(
                        "Creating kernel from your inputs",
                        severity="information",
                    )
                    # Fallback to dynamic template
                    self.kernel_content = self._generate_kernel_template()
                    kernel_generated = True
                    break
                except Exception as e:
                    if attempt == 0:
                        self.notify(f"Generation failed, retrying: {e}", severity="warning")
                        continue
                    self.notify(f"Failed to generate kernel: {e}", severity="error")
                    return

            if not kernel_generated:
                return

            # Validate kernel content length
            if len(self.kernel_content.strip()) < self.MIN_KERNEL_LENGTH:
                self.notify(
                    f"Kernel content too short (minimum {self.MIN_KERNEL_LENGTH} characters). Regenerating...",
                    severity="warning",
                )
                self.kernel_content = self._generate_kernel_template()

            self.current_step = WizardStep.KERNEL_PROPOSAL

        elif self.current_step == WizardStep.KERNEL_PROPOSAL:
            # Show kernel approval modal with error handling
            try:
                modal = KernelApprovalModal(self.kernel_content, self.project_slug, mode="proposal")
                approved = await self.app.push_screen_wait(modal)

                if approved is True:
                    await self.create_project()
                elif approved is False:
                    self.notify("Project creation cancelled", severity="warning")
                else:  # None or unexpected value (e.g., modal dismissed with ESC)
                    self.notify("Action cancelled", severity="information")
                    return
            except Exception as e:
                self.notify(f"Error showing approval dialog: {e}", severity="error")
                return

        self.update_step_content()

    def action_prev_step(self) -> None:
        """Move to the previous wizard step."""
        if self.current_step == WizardStep.BRAINDUMP:
            self.current_step = WizardStep.PROJECT_NAME
        elif self.current_step == WizardStep.CLARIFY_QUESTIONS:
            self.current_step = WizardStep.BRAINDUMP
        elif self.current_step == WizardStep.ANSWERS:
            self.current_step = WizardStep.CLARIFY_QUESTIONS
        elif self.current_step == WizardStep.KERNEL_PROPOSAL:
            self.current_step = WizardStep.ANSWERS

        self.update_step_content()

    def action_cancel(self) -> None:
        """Cancel the wizard."""
        # Confirm cancellation if there's data
        if self.project_name or self.braindump:
            # Mark that we're cancelling to trigger cleanup
            self._partial_project_created = False
        self.dismiss(False)

    def action_focus_next(self) -> None:
        """Focus the next input field."""
        import contextlib

        with contextlib.suppress(Exception):
            self.screen.focus_next()

    def action_focus_previous(self) -> None:
        """Focus the previous input field."""
        import contextlib

        with contextlib.suppress(Exception):
            self.screen.focus_previous()

    async def create_project(self) -> None:
        """Create the project with all the gathered information."""
        try:
            # Create project structure
            project_path = scaffold_project(self.project_slug)

            # Write the kernel content
            kernel_path = project_path / "kernel.md"

            # Add frontmatter to kernel
            frontmatter = f"""---
title: Kernel
project: {self.project_slug}
created: {datetime.now().isoformat()}
stage: kernel
---

"""
            full_kernel = frontmatter + self.kernel_content
            atomic_write_text(kernel_path, full_kernel)

            # Update project metadata
            project_data = ProjectMeta.read_project_yaml(self.project_slug)
            if project_data:
                project_data["title"] = self.project_name
                project_data["description"] = (
                    self.braindump[:200] + "..." if len(self.braindump) > 200 else self.braindump
                )
                project_data["stage"] = "kernel"
                ProjectMeta.write_project_yaml(self.project_slug, project_data)

            # Set as active project
            app_state = get_app_state()
            app_state.set_active_project(self.project_slug, reason="wizard-accept")

            self.notify(
                f"Project '{self.project_name}' created successfully!", severity="information"
            )

            # Switch to main screen
            from app.tui.views.main_screen import MainScreen

            self.app.switch_screen(MainScreen())

        except Exception as e:
            self.notify(f"Failed to create project: {e}", severity="error")

    def _generate_kernel_template(self) -> str:
        """Generate a dynamic kernel template based on user inputs."""
        # Extract first sentence as core concept
        first_sentence = (
            self.braindump.split(".")[0] if "." in self.braindump else self.braindump[:200]
        )

        # Extract key points from answers
        answer_lines = self.answers.split("\n")
        key_points = [line.strip() for line in answer_lines[:3] if line.strip()]

        return f"""# Kernel

## Core Concept
{first_sentence.strip()}.

{self.braindump[:500] if len(self.braindump) > len(first_sentence) else ""}

## Key Questions
Based on your clarifications:
{chr(10).join("- " + point for point in key_points) if key_points else self.answers[:500]}

## Success Criteria
- Complete implementation of described functionality
- User satisfaction with the solution
- Meeting identified requirements

## Constraints
- Available resources and timeline
- Technical requirements as specified
- Scope as defined in the braindump

## Primary Value Proposition
{first_sentence.strip()} - delivering value through effective implementation.
"""

    def _generate_fallback_questions(self) -> list[str]:
        """Generate contextual fallback questions based on braindump."""
        # Analyze braindump for keywords to create more relevant questions
        braindump_lower = self.braindump.lower()
        questions = []

        # Always start with problem definition
        questions.append("1. What specific problem does this solve?")

        # Check for user/audience mentions
        if any(word in braindump_lower for word in ["user", "customer", "people", "team"]):
            questions.append("2. Who are the primary users and what are their needs?")
        else:
            questions.append("2. Who will benefit from this project?")

        # Check for technical terms
        if any(
            word in braindump_lower for word in ["api", "database", "system", "app", "software"]
        ):
            questions.append("3. What are the technical requirements and integrations?")
        else:
            questions.append("3. What are the key features or capabilities?")

        # Check for time-related words
        if any(word in braindump_lower for word in ["deadline", "timeline", "when", "date"]):
            questions.append("4. What is the specific timeline and key milestones?")
        else:
            questions.append("4. What is your expected timeline?")

        # Always end with success metrics
        questions.append("5. How will you measure success?")

        return questions[: self.CLARIFY_QUESTIONS_COUNT]
