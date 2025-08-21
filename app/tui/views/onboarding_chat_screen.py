"""Conversational onboarding chat screen for new project creation."""

from datetime import datetime
from enum import Enum, auto

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog

from app.core.state import get_app_state
from app.files.atomic import atomic_write_text
from app.files.project_meta import ProjectMeta
from app.files.scaffold import scaffold_project
from app.files.slug import ensure_unique_slug, slugify
from app.llm.claude_client import FakeClaudeClient
from app.llm.llm_service import LLMService
from app.tui.controllers.onboarding_controller import OnboardingController


class OnboardingState(Enum):
    """Conversation state tracking for onboarding flow."""

    WELCOME = auto()
    PROJECT_NAME = auto()
    BRAINDUMP = auto()
    SUMMARY_REVIEW = auto()
    CLARIFYING = auto()
    QUESTIONS = auto()
    ANSWERS = auto()
    KERNEL_REVIEW = auto()
    COMPLETE = auto()


class OnboardingChatScreen(Screen[bool]):
    """Chat-based onboarding screen for conversational project creation."""

    DEFAULT_CSS = """
    OnboardingChatScreen {
        layout: vertical;
    }

    .chat-container {
        height: 1fr;
        padding: 1;
    }

    .chat-history {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    .input-container {
        height: 3;
        padding: 0 1;
    }

    .chat-input {
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
    ]

    def __init__(self) -> None:
        """Initialize the onboarding chat screen."""
        super().__init__()

        # Initialize LLM service and controller
        llm_service = LLMService(client=FakeClaudeClient())
        self.controller = OnboardingController(llm_service=llm_service)

        # State management
        self.state = OnboardingState.WELCOME

        # Project data
        self.project_name: str = ""
        self.project_slug: str = ""
        self.braindump: str = ""
        self.summary: str = ""
        self.questions: list[str] = []
        self.answers: str = ""
        self.kernel_content: str = ""

    def compose(self) -> ComposeResult:
        """Compose the chat interface UI."""
        yield Header()
        with Container(classes="chat-container"), Vertical():
            yield RichLog(
                id="chat-history",
                classes="chat-history",
                wrap=True,
                highlight=True,
                markup=True,
            )
            with Container(classes="input-container"):
                yield Input(
                    placeholder="Type your message and press Enter...",
                    id="chat-input",
                    classes="chat-input",
                )
        yield Footer()

    def on_mount(self) -> None:
        """Display welcome message when screen mounts."""
        self.add_ai_message(
            "👋 Welcome to Brainstorm Buddy! I'll help you create a new project through a "
            "conversational process. Let's start by giving your project a name. "
            "What would you like to call it?"
        )
        # Focus the input
        input_widget = self.query_one("#chat-input", Input)
        input_widget.focus()

    def add_ai_message(self, message: str) -> None:
        """
        Add an AI message to the chat history.

        Args:
            message: The message content to display
        """
        chat_history = self.query_one("#chat-history", RichLog)
        chat_history.write(f"[bold cyan]🤖 Assistant:[/bold cyan] {message}")
        chat_history.write("")  # Add spacing

    def add_user_message(self, message: str) -> None:
        """
        Add a user message to the chat history.

        Args:
            message: The message content to display
        """
        chat_history = self.query_one("#chat-history", RichLog)
        chat_history.write(f"[bold green]👤 You:[/bold green] {message}")
        chat_history.write("")  # Add spacing

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user message submission."""
        message = event.value.strip()
        if not message:
            return

        # Clear the input
        event.input.value = ""

        # Add user message to chat
        self.add_user_message(message)

        # Process the message in a worker thread
        self.process_message(message)

    @work
    async def process_message(self, message: str) -> None:
        """
        Process user message based on current conversation state.

        Args:
            message: The user's message to process
        """
        try:
            if self.state == OnboardingState.WELCOME:
                # User is providing project name
                self.project_name = message
                self.project_slug = ensure_unique_slug(slugify(message))

                # Start the session
                await self.controller.start_session(self.project_name)

                # Move to braindump state
                self.state = OnboardingState.BRAINDUMP
                self.app.call_from_thread(
                    self.add_ai_message,
                    f"Great! I've created a project called '{self.project_name}'. "
                    "Now, tell me about your idea. Don't worry about structure - "
                    "just describe what you're thinking in as much detail as you'd like.",
                )

            elif self.state == OnboardingState.BRAINDUMP:
                # User provided braindump
                self.braindump = message

                # Generate summary
                self.app.call_from_thread(
                    self.add_ai_message, "Thanks for sharing! Let me summarize what I understand..."
                )

                self.summary = await self.controller.summarize_braindump(self.braindump)

                # Show summary and ask for confirmation
                self.state = OnboardingState.SUMMARY_REVIEW
                self.app.call_from_thread(
                    self.add_ai_message,
                    f"Here's my summary of your idea:\n\n{self.summary}\n\n"
                    "Does this capture the essence of your project? "
                    "You can say 'yes' to continue or provide feedback to refine it.",
                )

            elif self.state == OnboardingState.SUMMARY_REVIEW:
                # Check if user approves or wants to refine
                if message.lower() in ["yes", "y", "correct", "good", "perfect"]:
                    # Move to questions
                    self.state = OnboardingState.CLARIFYING
                    self.app.call_from_thread(
                        self.add_ai_message,
                        "Excellent! Let me ask you a few clarifying questions to better understand your project...",
                    )

                    # Generate questions
                    self.questions = await self.controller.generate_clarifying_questions(count=5)

                    # Display questions
                    questions_text = "\n".join(self.questions)
                    self.state = OnboardingState.QUESTIONS
                    self.app.call_from_thread(
                        self.add_ai_message,
                        f"{questions_text}\n\nPlease provide your answers in a single response.",
                    )
                else:
                    # Refine summary based on feedback
                    self.app.call_from_thread(
                        self.add_ai_message, "Let me refine the summary based on your feedback..."
                    )

                    self.summary = await self.controller.refine_summary(message)

                    self.app.call_from_thread(
                        self.add_ai_message,
                        f"Here's the refined summary:\n\n{self.summary}\n\n"
                        "Does this better capture your idea? (yes/no or provide more feedback)",
                    )

            elif self.state == OnboardingState.QUESTIONS:
                # User provided answers
                self.answers = message

                # Generate kernel
                self.app.call_from_thread(
                    self.add_ai_message,
                    "Thank you for those answers! Now I'll create a project kernel that captures "
                    "the essence of your idea...",
                )

                self.kernel_content = await self.controller.synthesize_kernel(self.answers)

                # Show kernel for review
                self.state = OnboardingState.KERNEL_REVIEW
                self.app.call_from_thread(
                    self.add_ai_message,
                    f"Here's your project kernel:\n\n{self.kernel_content}\n\n"
                    "Would you like to:\n"
                    "1. Accept this kernel and create the project (type 'accept')\n"
                    "2. Clarify something (type 'clarify' and explain)\n"
                    "3. Start over (type 'restart')",
                )

            elif self.state == OnboardingState.KERNEL_REVIEW:
                # Handle kernel review decision
                decision = message.lower().strip()

                if decision == "accept" or decision == "1":
                    # Create the project
                    await self.create_project()

                elif decision == "restart" or decision == "3":
                    # Reset everything
                    self.state = OnboardingState.WELCOME
                    self.project_name = ""
                    self.project_slug = ""
                    self.braindump = ""
                    self.summary = ""
                    self.questions = []
                    self.answers = ""
                    self.kernel_content = ""
                    self.controller.clear_transcript()

                    self.app.call_from_thread(
                        self.add_ai_message,
                        "No problem! Let's start fresh. What would you like to name your project?",
                    )

                else:
                    # Treat as clarification feedback
                    self.app.call_from_thread(
                        self.add_ai_message, "Let me refine the kernel based on your feedback..."
                    )

                    # Add feedback to transcript and regenerate
                    self.controller.transcript.add_user(f"Kernel feedback: {message}")
                    self.kernel_content = await self.controller.synthesize_kernel(self.answers)

                    self.app.call_from_thread(
                        self.add_ai_message,
                        f"Here's the refined kernel:\n\n{self.kernel_content}\n\n"
                        "Would you like to accept, clarify further, or restart?",
                    )

        except Exception as e:
            # Handle errors gracefully
            self.app.call_from_thread(
                self.add_ai_message,
                f"I encountered an error: {str(e)}. Please try again or press ESC to cancel.",
            )

    async def create_project(self) -> None:
        """Create the project with all gathered information."""
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

            self.app.call_from_thread(
                self.add_ai_message,
                f"🎉 Project '{self.project_name}' created successfully! "
                "Switching to the main screen...",
            )

            # Switch to main screen after a brief pause
            self.set_timer(1.5, self.switch_to_main)

        except Exception as e:
            self.app.call_from_thread(self.add_ai_message, f"Failed to create project: {str(e)}")

    def switch_to_main(self) -> None:
        """Switch to the main screen."""
        from app.tui.views.main_screen import MainScreen

        self.app.switch_screen(MainScreen())

    def action_cancel(self) -> None:
        """Cancel the onboarding process."""
        self.dismiss(False)
