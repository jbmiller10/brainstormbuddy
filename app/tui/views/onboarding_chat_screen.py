"""Conversational onboarding chat screen for new project creation."""

import asyncio
import logging
import re
from datetime import datetime
from enum import Enum, auto

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog

from app.core.config import load_settings
from app.core.state import get_app_state
from app.files.atomic import atomic_write_text
from app.files.project_meta import ProjectMeta
from app.files.scaffold import scaffold_project
from app.files.slug import ensure_unique_slug, slugify
from app.llm.claude_client import FakeClaudeClient
from app.llm.llm_service import LLMService
from app.tui.controllers.onboarding_controller import OnboardingController
from app.tui.utils.text import truncate_description
from app.tui.widgets.kernel_approval import KernelApprovalModal

logger = logging.getLogger(__name__)


class OnboardingState(Enum):
    """Conversation state tracking for onboarding flow.

    Note: QUESTIONS state handles both displaying questions and receiving answers.
    There is no separate ANSWERS state - answers are processed within QUESTIONS
    before transitioning to KERNEL_REVIEW.
    """

    WELCOME = auto()
    PROJECT_NAME = auto()  # User provides project name
    BRAINDUMP = auto()  # User provides initial idea description
    SUMMARY_REVIEW = auto()  # Review and refine summary
    QUESTIONS = auto()  # Display questions AND receive answers
    KERNEL_REVIEW = auto()  # Review generated kernel
    COMPLETE = auto()  # Project creation complete


class OnboardingChatScreen(Screen[bool]):
    """Chat-based onboarding screen for conversational project creation."""

    DEFAULT_CSS = """
    OnboardingChatScreen {
        layout: vertical;
    }

    .onboarding-chat-container {
        height: 1fr;
        padding: 1;
    }

    .onboarding-chat-history {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    .onboarding-input-container {
        height: 3;
        padding: 0 1;
    }

    .onboarding-loading {
        color: $text-muted;
        font-style: italic;
    }

    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
    ]

    def __init__(self) -> None:
        """Initialize the onboarding chat screen."""
        super().__init__()

        # Load configuration
        self.settings = load_settings()

        # Initialize LLM service with configurable client
        # Note: Real ClaudeClient implementation pending
        if self.settings.use_fake_llm_client:
            client = FakeClaudeClient()
        else:
            # TODO: Implement and use real ClaudeClient when available
            client = FakeClaudeClient()
            logger.warning("Real ClaudeClient not yet implemented, using FakeClaudeClient")

        llm_service = LLMService(client=client)
        self.controller = OnboardingController(llm_service=llm_service)

        # State management with race condition prevention
        self.state = OnboardingState.WELCOME
        self._creation_lock = asyncio.Lock()
        self._processing_message_shown = False

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
        with Container(classes="onboarding-chat-container"), Vertical():
            yield RichLog(
                id="chat-history",
                classes="onboarding-chat-history",
                wrap=True,
                highlight=True,
                markup=True,
            )
            with Container(classes="onboarding-input-container"):
                yield Input(
                    placeholder="Type your message and press Enter...",
                    id="chat-input",
                    classes="onboarding-chat-input",
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
        input_widget: Input = self.query_one("#chat-input", Input)
        input_widget.focus()

    def add_ai_message(self, message: str) -> None:
        """
        Add an AI message to the chat history.

        Args:
            message: The message content to display
        """
        chat_history: RichLog = self.query_one("#chat-history", RichLog)
        chat_history.write(f"[bold cyan]🤖 Assistant:[/bold cyan] {message}")
        chat_history.write("")  # Add spacing

    def add_user_message(self, message: str) -> None:
        """
        Add a user message to the chat history.

        Args:
            message: The message content to display
        """
        chat_history: RichLog = self.query_one("#chat-history", RichLog)
        chat_history.write(f"[bold green]👤 You:[/bold green] {message}")
        chat_history.write("")  # Add spacing

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user message submission."""
        message = event.value.strip()
        if not message:
            return

        # Clear and disable the input during processing
        event.input.value = ""
        event.input.disabled = True

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
        # Show loading indicator only once
        if not self._processing_message_shown:
            self.app.call_from_thread(self.add_ai_message, "[dim italic]Processing...[/dim italic]")
            self._processing_message_shown = True

        try:
            logger.debug(f"Processing message in state {self.state.name}: {message[:50]}...")

            if self.state == OnboardingState.WELCOME:
                # Clear the processing message if shown
                if self._processing_message_shown:
                    self._clear_last_ai_message()
                    self._processing_message_shown = False

                # Validate project name length
                if len(message) < self.settings.min_project_name_length:
                    self.app.call_from_thread(
                        self.add_ai_message,
                        f"Please provide a project name with at least {self.settings.min_project_name_length} characters.",
                    )
                    return

                if len(message) > self.settings.max_project_name_length:
                    self.app.call_from_thread(
                        self.add_ai_message,
                        f"Project name is too long. Please keep it under {self.settings.max_project_name_length} characters.",
                    )
                    return

                # Validate project name characters
                if not re.match(r"^[\w\s\-]+$", message):
                    self.app.call_from_thread(
                        self.add_ai_message,
                        "Project names can only contain letters, numbers, spaces, hyphens, and underscores.",
                    )
                    return

                # User is providing project name
                self.project_name = message
                self.project_slug = ensure_unique_slug(slugify(message))
                logger.info(f"Creating project: {self.project_name} (slug: {self.project_slug})")

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
                # Clear the processing message if shown
                if self._processing_message_shown:
                    self._clear_last_ai_message()
                    self._processing_message_shown = False

                # Validate braindump with helpful character count
                current_length = len(message.strip())
                if current_length < self.settings.min_braindump_length:
                    self.app.call_from_thread(
                        self.add_ai_message,
                        f"Please provide more detail about your idea. "
                        f"Current: {current_length} characters, minimum: {self.settings.min_braindump_length} characters.",
                    )
                    return

                if len(message) > self.settings.max_braindump_length:
                    self.app.call_from_thread(
                        self.add_ai_message,
                        f"Your description is too long ({len(message)} characters). "
                        f"Please keep it under {self.settings.max_braindump_length} characters.",
                    )
                    return

                # User provided braindump
                self.braindump = message
                logger.debug(f"Received braindump of {len(message)} characters")

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
                # Clear the processing message if shown
                if self._processing_message_shown:
                    self._clear_last_ai_message()
                    self._processing_message_shown = False

                # Check if user approves or wants to refine
                if message.lower() in ["yes", "y", "correct", "good", "perfect"]:
                    # Move directly to questions state
                    self.app.call_from_thread(
                        self.add_ai_message,
                        "Excellent! Let me ask you a few clarifying questions to better understand your project...",
                    )

                    # Generate questions
                    self.questions = await self.controller.generate_clarifying_questions(
                        count=self.settings.onboarding_questions_count
                    )

                    # Display questions and set state
                    questions_text = "\n".join(self.questions)
                    self.state = OnboardingState.QUESTIONS
                    logger.debug(
                        f"Transitioned to QUESTIONS state with {len(self.questions)} questions"
                    )
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
                # Clear the processing message if shown
                if self._processing_message_shown:
                    self._clear_last_ai_message()
                    self._processing_message_shown = False

                # User provided answers (no separate ANSWERS state needed)
                self.answers = message

                # Generate kernel
                self.app.call_from_thread(
                    self.add_ai_message,
                    "Thank you for those answers! Now I'll create a project kernel that captures "
                    "the essence of your idea...",
                )

                self.kernel_content = await self.controller.synthesize_kernel(self.answers)

                # Show kernel for review using modal
                self.state = OnboardingState.KERNEL_REVIEW
                self.app.call_from_thread(
                    self.add_ai_message,
                    "Here's your project kernel. I'll show you a review modal where you can:"
                    "\n• Accept the kernel and create the project"
                    "\n• Clarify something to refine the kernel"
                    "\n• Start over from the beginning",
                )

                # Show the kernel approval modal
                self.app.call_from_thread(self.show_kernel_approval_modal)

            elif self.state == OnboardingState.KERNEL_REVIEW:
                # Clear the processing message if shown
                if self._processing_message_shown:
                    self._clear_last_ai_message()
                    self._processing_message_shown = False

                # In KERNEL_REVIEW state, user can provide clarification feedback
                # Store the feedback and regenerate the kernel
                self.app.call_from_thread(
                    self.add_ai_message, "Let me refine the kernel based on your feedback..."
                )

                # Add feedback to transcript and regenerate
                self.controller.transcript.add_user(f"Kernel feedback: {message}")
                self.kernel_content = await self.controller.synthesize_kernel(self.answers)

                self.app.call_from_thread(
                    self.add_ai_message,
                    "I've refined the kernel based on your feedback. Let me show you the updated version.",
                )

                # Show the modal again with the refined kernel
                self.app.call_from_thread(self.show_kernel_approval_modal)

        except Exception as e:
            # Clear processing indicator if it was shown
            if self._processing_message_shown:
                self._clear_last_ai_message()
                self._processing_message_shown = False

            # Handle errors gracefully
            logger.error(f"Error processing message in state {self.state.name}: {e}", exc_info=True)
            self.app.call_from_thread(
                self.add_ai_message,
                f"I encountered an error: {str(e)}. Please try again or press ESC to cancel.",
            )
        finally:
            # Always reset processing flag and re-enable input
            self._processing_message_shown = False
            self.app.call_from_thread(self._enable_input)

    async def create_project(self) -> None:
        """Create the project with all gathered information."""
        # Use lock to prevent race conditions
        async with self._creation_lock:
            try:
                # Prevent multiple calls during transition
                if self.state == OnboardingState.COMPLETE:
                    logger.warning("Project creation already in progress, skipping duplicate call")
                    return

                self.state = OnboardingState.COMPLETE
                logger.info(f"Creating project: {self.project_slug}")

                # Create project structure
                project_path = scaffold_project(self.project_slug)

                # Verify scaffold succeeded
                if not project_path.exists():
                    raise RuntimeError(f"Failed to create project directory: {project_path}")

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
                try:
                    project_data = ProjectMeta.read_project_yaml(self.project_slug)
                    if project_data:
                        project_data["title"] = self.project_name
                        project_data["description"] = truncate_description(self.braindump)
                        project_data["stage"] = "kernel"
                        ProjectMeta.write_project_yaml(self.project_slug, project_data)
                    else:
                        logger.warning(
                            f"Could not read project.yaml for {self.project_slug}, creating minimal metadata"
                        )
                        # Create minimal metadata if read failed
                        project_data = {
                            "title": self.project_name,
                            "description": truncate_description(self.braindump),
                            "stage": "kernel",
                        }
                        ProjectMeta.write_project_yaml(self.project_slug, project_data)
                except Exception as e:
                    logger.error(f"Failed to update project metadata: {e}", exc_info=True)
                    # Continue - project is still created even if metadata update fails

                # Set as active project
                app_state = get_app_state()
                app_state.set_active_project(self.project_slug, reason="wizard-accept")

                self.app.call_from_thread(
                    self.add_ai_message,
                    f"🎉 Project '{self.project_name}' created successfully! "
                    "Switching to the main screen...",
                )

                logger.info(f"Successfully created project {self.project_slug}")

                # Switch to main screen directly from the worker thread
                from app.tui.views.main_screen import MainScreen

                self.app.call_from_thread(self.app.switch_screen, MainScreen())

            except Exception as e:
                logger.error(f"Failed to create project {self.project_slug}: {e}", exc_info=True)
                self.state = OnboardingState.KERNEL_REVIEW  # Reset state so user can try again
                self.app.call_from_thread(
                    self.add_ai_message, f"Failed to create project: {str(e)}"
                )

    def action_cancel(self) -> None:
        """Cancel the onboarding process."""
        self.dismiss(False)

    def _clear_last_ai_message(self) -> None:
        """Clear the processing indicator message.

        Note: RichLog doesn't support removing messages, so we overwrite
        the processing message with actual content immediately.
        This is called right before adding the real response.
        """
        # This is a no-op now since we immediately overwrite with real content
        pass

    def _enable_input(self) -> None:
        """Re-enable the chat input after processing."""
        input_widget: Input = self.query_one("#chat-input", Input)
        input_widget.disabled = False
        input_widget.focus()

    @work
    async def show_kernel_approval_modal(self) -> None:
        """Show the kernel approval modal and handle the user's decision."""
        try:
            modal = KernelApprovalModal(self.kernel_content, self.project_slug, mode="proposal")
            decision = await self.app.push_screen_wait(modal)

            if decision == "accept":
                # Create the project
                logger.info("User accepted kernel, creating project")
                await self.create_project()

            elif decision == "restart":
                # Reset everything
                logger.info("User requested restart of onboarding process")
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
                # Re-enable input for new conversation
                self.app.call_from_thread(self._enable_input)

            else:  # "clarify"
                # User wants to provide feedback
                logger.info("User wants to clarify kernel")
                self.app.call_from_thread(
                    self.add_ai_message,
                    "Please tell me what you'd like to clarify or change about the kernel:",
                )
                # Re-enable input for feedback
                self.app.call_from_thread(self._enable_input)

        except Exception as e:
            logger.error(f"Error showing kernel approval modal: {e}", exc_info=True)
            self.app.call_from_thread(
                self.add_ai_message,
                f"I encountered an error showing the approval dialog: {str(e)}. "
                "Please provide feedback to refine the kernel or type 'restart' to begin again.",
            )
            # Re-enable input on error
            self.app.call_from_thread(self._enable_input)
