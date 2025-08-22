"""Comprehensive tests for OnboardingChatScreen to improve coverage."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from textual.widgets import Input, RichLog

from app.tui.views.onboarding_chat_screen import OnboardingChatScreen, OnboardingState


@pytest.fixture
def mock_settings() -> Mock:
    """Create mock settings."""
    settings = Mock()
    settings.min_project_name_length = 3
    settings.max_project_name_length = 100
    settings.min_braindump_length = 10
    settings.max_braindump_length = 10000
    settings.onboarding_questions_count = 5
    settings.use_fake_llm_client = True
    return settings


@pytest.fixture
def mock_controller() -> Mock:
    """Create a mock OnboardingController."""
    controller = Mock()
    controller.start_session = AsyncMock()
    controller.summarize_braindump = AsyncMock(return_value="Summary of idea")
    controller.generate_clarifying_questions = AsyncMock(
        return_value=["1. Q1?", "2. Q2?", "3. Q3?", "4. Q4?", "5. Q5?"]
    )
    controller.refine_summary = AsyncMock(return_value="Refined summary")
    controller.synthesize_kernel = AsyncMock(return_value="# Kernel content")
    controller.clear_transcript = Mock()
    controller.transcript = Mock()
    controller.transcript.add_user = Mock()
    return controller


class TestUIComponents:
    """Test UI component methods."""

    def test_compose_method_exists(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test compose method exists and is callable."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        # The compose method exists and is callable
        assert hasattr(screen, "compose")
        assert callable(screen.compose)

    def test_on_mount_displays_welcome(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test on_mount displays welcome message and focuses input."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        # Mock the query_one method and input widget
        mock_input = Mock(spec=Input)

        with (
            patch.object(screen, "query_one", return_value=mock_input),
            patch.object(screen, "add_ai_message") as mock_add_ai,
        ):
            screen.on_mount()

            # Should display welcome message
            mock_add_ai.assert_called_once()
            welcome_msg = mock_add_ai.call_args[0][0]
            assert "Welcome to Brainstorm Buddy" in welcome_msg
            assert "What would you like to call it?" in welcome_msg

            # Should focus the input
            mock_input.focus.assert_called_once()

    def test_add_ai_message(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test add_ai_message writes to chat history."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        # Mock the chat history widget
        mock_chat = Mock(spec=RichLog)

        with patch.object(screen, "query_one", return_value=mock_chat):
            # Add an AI message
            test_message = "Test AI message"
            screen.add_ai_message(test_message)

            # Should write formatted message and spacing
            assert mock_chat.write.call_count == 2
            first_call = mock_chat.write.call_args_list[0][0][0]
            assert "🤖 Assistant:" in first_call
            assert test_message in first_call
            # Second call should be empty line for spacing
            assert mock_chat.write.call_args_list[1][0][0] == ""

    def test_add_user_message(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test add_user_message writes to chat history."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        # Mock the chat history widget
        mock_chat = Mock(spec=RichLog)

        with patch.object(screen, "query_one", return_value=mock_chat):
            # Add a user message
            test_message = "Test user message"
            screen.add_user_message(test_message)

            # Should write formatted message and spacing
            assert mock_chat.write.call_count == 2
            first_call = mock_chat.write.call_args_list[0][0][0]
            assert "👤 You:" in first_call
            assert test_message in first_call
            # Second call should be empty line for spacing
            assert mock_chat.write.call_args_list[1][0][0] == ""

    def test_enable_input(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test _enable_input re-enables and focuses input."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        # Mock the input widget
        mock_input = Mock(spec=Input)
        mock_input.disabled = True

        with patch.object(screen, "query_one", return_value=mock_input):
            # Enable input
            screen._enable_input()

            # Should enable and focus
            assert mock_input.disabled is False
            mock_input.focus.assert_called_once()


class TestProcessMessageWelcomeState:
    """Test process_message in WELCOME state."""

    @pytest.mark.asyncio
    async def test_project_name_too_short(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test rejection of project names that are too short."""
        mock_settings.min_project_name_length = 3

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.WELCOME

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "ab")  # type: ignore[attr-defined]  # Too short

        # Should add error message and remain in WELCOME state
        assert screen.state == OnboardingState.WELCOME
        # Check that add_ai_message was called with error
        assert any("at least 3 characters" in str(args) for func, args in call_history)

    @pytest.mark.asyncio
    async def test_project_name_too_long(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test rejection of project names that are too long."""
        mock_settings.max_project_name_length = 50

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.WELCOME

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "a" * 51)  # type: ignore[attr-defined]  # Too long

        # Should add error message and remain in WELCOME state
        assert screen.state == OnboardingState.WELCOME
        assert any("under 50 characters" in str(args) for func, args in call_history)

    @pytest.mark.asyncio
    async def test_project_name_invalid_characters(
        self, mock_settings: Mock, mock_controller: Mock
    ) -> None:
        """Test rejection of project names with invalid characters."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.WELCOME

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "test@project!")  # type: ignore[attr-defined]  # Invalid chars

        # Should add error message and remain in WELCOME state
        assert screen.state == OnboardingState.WELCOME
        assert any(
            "letters, numbers, spaces, hyphens, and underscores" in str(args)
            for func, args in call_history
        )

    @pytest.mark.asyncio
    async def test_valid_project_name(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test successful project name submission."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
            patch(
                "app.tui.views.onboarding_chat_screen.ensure_unique_slug", return_value="my-project"
            ),
            patch("app.tui.views.onboarding_chat_screen.slugify", return_value="my-project"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.WELCOME

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "My Project")  # type: ignore[attr-defined]

        # Should progress to BRAINDUMP state
        assert screen.state == OnboardingState.BRAINDUMP
        assert screen.project_name == "My Project"
        assert screen.project_slug == "my-project"
        mock_controller.start_session.assert_called_once_with("My Project")
        # Check for success message
        assert any("tell me about your idea" in str(args) for func, args in call_history)


class TestProcessMessageBraindumpState:
    """Test process_message in BRAINDUMP state."""

    @pytest.mark.asyncio
    async def test_braindump_too_short(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test rejection of braindumps that are too short."""
        mock_settings.min_braindump_length = 50

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.BRAINDUMP

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "Short idea")  # type: ignore[attr-defined]  # Too short

        # Should remain in BRAINDUMP state
        assert screen.state == OnboardingState.BRAINDUMP
        assert any("Current: 10 characters" in str(args) for func, args in call_history)
        assert any("minimum: 50 characters" in str(args) for func, args in call_history)

    @pytest.mark.asyncio
    async def test_braindump_too_long(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test rejection of braindumps that are too long."""
        mock_settings.max_braindump_length = 100

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.BRAINDUMP

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "x" * 101)  # type: ignore[attr-defined]  # Too long

        # Should remain in BRAINDUMP state
        assert screen.state == OnboardingState.BRAINDUMP
        assert any("too long (101 characters)" in str(args) for func, args in call_history)

    @pytest.mark.asyncio
    async def test_valid_braindump(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test successful braindump submission."""
        mock_settings.min_braindump_length = 10
        mock_controller.summarize_braindump = AsyncMock(
            return_value="This is a summary of the idea"
        )

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.BRAINDUMP

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            braindump = "This is my amazing idea for a project that will revolutionize everything"
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, braindump)  # type: ignore[attr-defined]

        # Should progress to SUMMARY_REVIEW state
        assert screen.state == OnboardingState.SUMMARY_REVIEW
        assert screen.braindump == braindump
        assert screen.summary == "This is a summary of the idea"
        mock_controller.summarize_braindump.assert_called_once_with(braindump)
        # Check for summary display message
        assert any("Does this capture the essence" in str(args) for func, args in call_history)


class TestProcessMessageSummaryReviewState:
    """Test process_message in SUMMARY_REVIEW state."""

    @pytest.mark.asyncio
    async def test_summary_approval(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test approving the summary."""
        mock_settings.onboarding_questions_count = 3
        mock_controller.generate_clarifying_questions = AsyncMock(
            return_value=["Q1?", "Q2?", "Q3?"]
        )

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.SUMMARY_REVIEW

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "yes")  # type: ignore[attr-defined]

        # Should progress to QUESTIONS state
        assert screen.state == OnboardingState.QUESTIONS
        assert screen.questions == ["Q1?", "Q2?", "Q3?"]
        mock_controller.generate_clarifying_questions.assert_called_once_with(count=3)
        # Check for questions display
        assert any("Q1?" in str(args) and "Q2?" in str(args) for func, args in call_history)

    @pytest.mark.asyncio
    async def test_summary_refinement(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test requesting summary refinement."""
        mock_controller.refine_summary = AsyncMock(return_value="Refined summary")

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.SUMMARY_REVIEW

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "Actually, it should focus more on X")  # type: ignore[attr-defined]

        # Should remain in SUMMARY_REVIEW state with refined summary
        assert screen.state == OnboardingState.SUMMARY_REVIEW
        assert screen.summary == "Refined summary"
        mock_controller.refine_summary.assert_called_once_with(
            "Actually, it should focus more on X"
        )
        # Check for refined summary display
        assert any("refined summary" in str(args).lower() for func, args in call_history)


class TestProcessMessageQuestionsState:
    """Test process_message in QUESTIONS state."""

    @pytest.mark.asyncio
    async def test_answers_processing(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test processing answers to questions."""
        mock_controller.synthesize_kernel = AsyncMock(
            return_value="# Project Kernel\n\nCore idea..."
        )

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.QUESTIONS
            screen.questions = ["Q1?", "Q2?", "Q3?"]

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            answers = "A1: Answer 1\nA2: Answer 2\nA3: Answer 3"
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, answers)  # type: ignore[attr-defined]

        # Should progress to KERNEL_REVIEW state
        assert screen.state == OnboardingState.KERNEL_REVIEW
        assert screen.answers == answers
        assert screen.kernel_content == "# Project Kernel\n\nCore idea..."
        mock_controller.synthesize_kernel.assert_called_once_with(answers)
        # Check for kernel modal message
        assert any("review modal" in str(args).lower() for func, args in call_history)
        assert any("accept" in str(args).lower() for func, args in call_history)


class TestProcessMessageKernelReviewState:
    """Test process_message in KERNEL_REVIEW state."""

    @pytest.mark.asyncio
    async def test_kernel_restart(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test restarting the onboarding process via modal."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.KERNEL_REVIEW
            screen.project_name = "Test Project"
            screen.project_slug = "test-project"
            screen.braindump = "Some idea"
            screen.summary = "Summary"
            screen.questions = ["Q1"]
            screen.answers = "A1"
            screen.kernel_content = "Kernel"

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )
        mock_app.push_screen_wait = AsyncMock(return_value="restart")

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the modal method directly
            await screen.show_kernel_approval_modal.__wrapped__(screen)  # type: ignore[attr-defined]

        # Should reset to WELCOME state
        assert screen.state == OnboardingState.WELCOME
        assert screen.project_name == ""
        assert screen.project_slug == ""
        assert screen.braindump == ""
        assert screen.summary == ""
        assert screen.questions == []
        assert screen.answers == ""
        assert screen.kernel_content == ""
        mock_controller.clear_transcript.assert_called_once()
        # Check for restart message
        assert any("start fresh" in str(args) for func, args in call_history)

    @pytest.mark.asyncio
    async def test_kernel_clarification(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test requesting kernel clarification."""
        mock_controller.synthesize_kernel = AsyncMock(return_value="Refined kernel content")
        mock_controller.transcript = Mock()
        mock_controller.transcript.add_user = Mock()

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.KERNEL_REVIEW
            screen.answers = "Previous answers"
            # Set the flag indicating we're expecting clarification
            screen._awaiting_clarification = True

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "Please add more detail about X")  # type: ignore[attr-defined]

        # Should remain in KERNEL_REVIEW with refined kernel
        assert screen.state == OnboardingState.KERNEL_REVIEW
        assert screen.kernel_content == "Refined kernel content"
        # Flag should be reset after processing clarification
        assert screen._awaiting_clarification is False
        mock_controller.transcript.add_user.assert_called_once_with(
            "Kernel feedback: Please add more detail about X"
        )
        mock_controller.synthesize_kernel.assert_called_once_with("Previous answers")
        # Check for refined kernel display
        assert any("refined" in str(args).lower() for func, args in call_history)

    @pytest.mark.asyncio
    async def test_kernel_unexpected_input(
        self, mock_settings: Mock, mock_controller: Mock
    ) -> None:
        """Test handling unexpected input in KERNEL_REVIEW when not awaiting clarification."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.KERNEL_REVIEW
            screen.kernel_content = "Test kernel"
            screen.project_slug = "test-project"
            # NOT setting _awaiting_clarification flag

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "Random text")  # type: ignore[attr-defined]

        # Should remain in KERNEL_REVIEW
        assert screen.state == OnboardingState.KERNEL_REVIEW
        # Should not have processed as clarification
        assert screen.kernel_content == "Test kernel"
        # Should prompt to use modal
        assert any("use the review modal" in str(args).lower() for func, args in call_history)


class TestCreateProject:
    """Test project creation method."""

    @pytest.mark.asyncio
    async def test_project_creation_failure(
        self, mock_settings: Mock, mock_controller: Mock
    ) -> None:
        """Test handling of project creation failure."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.KERNEL_REVIEW
            screen.project_slug = "test-project"

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.scaffold_project",
                side_effect=Exception("Scaffold failed"),
            ),
        ):
            await screen.create_project()

        # Should reset state to KERNEL_REVIEW
        assert screen.state == OnboardingState.KERNEL_REVIEW
        # Should display error message
        assert any("Failed to create project" in str(args) for func, args in call_history)


class TestErrorHandling:
    """Test error handling in process_message."""

    @pytest.mark.asyncio
    async def test_process_message_error_handling(
        self, mock_settings: Mock, mock_controller: Mock
    ) -> None:
        """Test error handling in process_message."""
        mock_controller.summarize_braindump = AsyncMock(side_effect=Exception("LLM error"))

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.BRAINDUMP

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "This is my braindump")  # type: ignore[attr-defined]

        # Should display error and enable input
        assert any("I encountered an error: LLM error" in str(args) for func, args in call_history)
        # _enable_input should be called via call_from_thread
        assert any(func.__name__ == "_enable_input" for func, args in call_history)


class TestProjectCreationLock:
    """Test project creation lock and duplicate prevention."""

    @pytest.mark.asyncio
    async def test_duplicate_creation_prevention(
        self, mock_settings: Mock, mock_controller: Mock
    ) -> None:
        """Test that COMPLETE state prevents duplicate project creation."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.COMPLETE
            screen.project_slug = "test-project"

        # Mock app context
        mock_app = Mock()
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: func(*args) if callable(func) else None
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch("app.tui.views.onboarding_chat_screen.scaffold_project") as mock_scaffold,
            patch("app.tui.views.onboarding_chat_screen.logger") as mock_logger,
        ):
            await screen.create_project()

        # Should log warning and return early
        mock_logger.warning.assert_called_with(
            "Project creation already in progress, skipping duplicate call"
        )
        # Should not call scaffold_project
        mock_scaffold.assert_not_called()


class TestProcessingMessageFlag:
    """Test processing message flag handling."""

    @pytest.mark.asyncio
    async def test_processing_message_shown_once(
        self, mock_settings: Mock, mock_controller: Mock
    ) -> None:
        """Test that processing message is only shown once."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
            patch(
                "app.tui.views.onboarding_chat_screen.ensure_unique_slug",
                return_value="test-project",
            ),
            patch("app.tui.views.onboarding_chat_screen.slugify", return_value="test-project"),
        ):
            screen = OnboardingChatScreen()
            screen.state = OnboardingState.WELCOME

        # Mock app context
        mock_app = Mock()
        call_history = []
        mock_app.call_from_thread = Mock(
            side_effect=lambda func, *args: call_history.append((func, args))
        )

        with (
            patch.object(type(screen), "app", property(lambda _: mock_app)),
            patch(
                "app.tui.views.onboarding_chat_screen.work", lambda f: f
            ),  # Bypass @work decorator
        ):
            # Initially flag should be False
            assert screen._processing_message_shown is False

            # Call the actual async method directly
            await screen.process_message.__wrapped__(screen, "Test Project")  # type: ignore[attr-defined]

            # After processing, flag should be reset to False
            assert screen._processing_message_shown is False

            # Check if processing message was shown (should be in call history if it was)
            processing_msgs = [
                args
                for func, args in call_history
                if func.__name__ == "add_ai_message" and "Processing..." in str(args)
            ]
            # Since we process quickly in tests, it might not show, but flag should be managed correctly
            assert len(processing_msgs) <= 1  # At most one processing message
