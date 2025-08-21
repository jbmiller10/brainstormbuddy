"""New project wizard for guided project creation."""

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

    DEFAULT_CSS = """
    NewProjectWizard {
        align: center middle;
    }

    NewProjectWizard .container {
        width: 90%;
        height: 90%;
        max-width: 120;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }

    NewProjectWizard .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    NewProjectWizard .step-indicator {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    NewProjectWizard .content-area {
        height: 1fr;
        margin-bottom: 2;
        padding: 1;
    }

    NewProjectWizard .instructions {
        margin-bottom: 1;
        color: $text;
    }

    NewProjectWizard .questions-container {
        padding: 1;
        border: solid $primary;
        background: $panel;
    }

    NewProjectWizard .question-item {
        margin-bottom: 1;
        padding: 0 1;
    }

    NewProjectWizard Input {
        width: 100%;
        margin-bottom: 1;
    }

    NewProjectWizard TextArea {
        width: 100%;
        height: 100%;
    }

    NewProjectWizard .button-container {
        height: 3;
        align: center middle;
    }

    NewProjectWizard Button {
        width: 16;
        margin: 0 1;
    }

    NewProjectWizard .next-button {
        background: $success;
    }

    NewProjectWizard .back-button {
        background: $warning;
    }

    NewProjectWizard .cancel-button {
        background: $error;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
        Binding("ctrl+n", "next_step", "Next", show=False),
        Binding("ctrl+b", "prev_step", "Back", show=False),
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
        """Focus the project name input."""
        try:
            input_widget = self.query_one("#project-name-input", Input)
            input_widget.focus()
        except Exception:
            pass

    def focus_textarea(self) -> None:
        """Focus the active textarea."""
        try:
            if self.current_step == WizardStep.BRAINDUMP:
                textarea = self.query_one("#braindump-textarea", TextArea)
            elif self.current_step == WizardStep.ANSWERS:
                textarea = self.query_one("#answers-textarea", TextArea)
            else:
                return
            textarea.focus()
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "next-button":
            await self.action_next_step()
        elif event.button.id == "back-button":
            self.action_prev_step()
        elif event.button.id == "cancel-button":
            self.action_cancel()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "project-name-input":
            self.project_name = event.value

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

            self.project_slug = ensure_unique_slug(slugify(self.project_name))
            self.current_step = WizardStep.BRAINDUMP

        elif self.current_step == WizardStep.BRAINDUMP:
            # Validate braindump
            if not self.braindump.strip():
                self.notify("Please describe your idea", severity="error")
                return

            # Generate clarifying questions
            self.notify("Generating clarifying questions...")
            try:
                self.clarify_questions = self.controller.generate_clarify_questions(
                    self.braindump, count=5
                )
            except Exception as e:
                self.notify(f"Failed to generate questions: {e}", severity="error")
                return

            self.current_step = WizardStep.CLARIFY_QUESTIONS

        elif self.current_step == WizardStep.CLARIFY_QUESTIONS:
            self.current_step = WizardStep.ANSWERS

        elif self.current_step == WizardStep.ANSWERS:
            # Validate answers
            if not self.answers.strip():
                self.notify("Please answer the questions", severity="error")
                return

            # Generate kernel proposal
            self.notify("Generating project kernel...")
            try:
                self.kernel_content = self.controller.orchestrate_kernel_generation(
                    self.braindump, self.answers
                )
            except Exception as e:
                self.notify(f"Failed to generate kernel: {e}", severity="error")
                return

            self.current_step = WizardStep.KERNEL_PROPOSAL

        elif self.current_step == WizardStep.KERNEL_PROPOSAL:
            # Show kernel approval modal
            modal = KernelApprovalModal(self.kernel_content, self.project_slug, mode="proposal")
            approved = await self.app.push_screen_wait(modal)

            if approved:
                await self.create_project()
            else:
                self.notify("Project creation cancelled", severity="warning")

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
        self.dismiss(False)

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
