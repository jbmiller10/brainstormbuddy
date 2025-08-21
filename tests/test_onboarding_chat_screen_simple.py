"""Simple unit tests for OnboardingChatScreen without app context."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

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


class TestOnboardingChatScreenBasics:
    """Basic tests for OnboardingChatScreen without app context."""

    def test_initialization(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test screen initializes with default values."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        assert screen.state == OnboardingState.WELCOME
        assert screen.project_name == ""
        assert screen.project_slug == ""
        assert screen.braindump == ""
        assert screen.summary == ""
        assert screen.questions == []
        assert screen.answers == ""
        assert screen.kernel_content == ""
        assert screen._processing_message_shown is False
        assert isinstance(screen._creation_lock, asyncio.Lock)

    def test_settings_loaded(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test settings are properly loaded."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        assert screen.settings == mock_settings

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

        assert hasattr(screen, "compose")
        assert callable(screen.compose)

    def test_message_methods_exist(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test message methods exist."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        assert hasattr(screen, "add_ai_message")
        assert hasattr(screen, "add_user_message")
        assert hasattr(screen, "process_message")

    def test_action_cancel_exists(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test action_cancel method exists."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        with patch.object(screen, "dismiss") as mock_dismiss:
            screen.action_cancel()
            mock_dismiss.assert_called_once_with(False)

    def test_clear_last_ai_message(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test _clear_last_ai_message is a no-op."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        # Should not raise an error
        screen._clear_last_ai_message()

    def test_enable_input_method_exists(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test _enable_input method exists."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        assert hasattr(screen, "_enable_input")
        assert callable(screen._enable_input)


class TestStateValidation:
    """Test state validation without app context."""

    def test_initial_state_is_welcome(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test initial state is WELCOME."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        assert screen.state == OnboardingState.WELCOME

    def test_all_states_defined(self) -> None:
        """Test all expected states are defined."""
        expected_states = [
            "WELCOME",
            "PROJECT_NAME",
            "BRAINDUMP",
            "SUMMARY_REVIEW",
            "QUESTIONS",
            "KERNEL_REVIEW",
            "COMPLETE",
        ]

        for state_name in expected_states:
            assert hasattr(OnboardingState, state_name)


class TestInputSubmissionHandling:
    """Test input submission without app context."""

    def test_input_submission_with_empty_value(
        self, mock_settings: Mock, mock_controller: Mock
    ) -> None:
        """Test input submission with empty value."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        with (
            patch.object(screen, "add_user_message") as mock_add_user,
            patch.object(screen, "process_message") as mock_process,
        ):
            # Create mock event with empty value
            mock_event = Mock()
            mock_event.value = "  "  # Just whitespace
            mock_event.input.value = ""
            mock_event.input.disabled = False

            screen.on_input_submitted(mock_event)

            # Should not process empty message
            mock_add_user.assert_not_called()
            mock_process.assert_not_called()

    def test_input_submission_with_valid_value(
        self, mock_settings: Mock, mock_controller: Mock
    ) -> None:
        """Test input submission with valid value."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        with (
            patch.object(screen, "add_user_message") as mock_add_user,
            patch.object(screen, "process_message") as mock_process,
        ):
            # Create mock event with valid value
            mock_event = Mock()
            mock_event.value = "Test input"
            mock_event.input.value = "Test input"
            mock_event.input.disabled = False

            screen.on_input_submitted(mock_event)

            # Should clear and disable input
            assert mock_event.input.value == ""
            assert mock_event.input.disabled is True

            # Should process the message
            mock_add_user.assert_called_once_with("Test input")
            mock_process.assert_called_once_with("Test input")


class TestClientConfiguration:
    """Test LLM client configuration."""

    def test_fake_client_when_configured(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test fake client is used when configured."""
        mock_settings.use_fake_llm_client = True

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.FakeClaudeClient") as mock_fake,
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            OnboardingChatScreen()

        mock_fake.assert_called_once()

    def test_real_client_fallback_to_fake(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test real client falls back to fake with warning."""
        mock_settings.use_fake_llm_client = False

        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.FakeClaudeClient"),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
            patch("app.tui.views.onboarding_chat_screen.logger") as mock_logger,
        ):
            OnboardingChatScreen()

        mock_logger.warning.assert_called_with(
            "Real ClaudeClient not yet implemented, using FakeClaudeClient"
        )


class TestProjectCreationLock:
    """Test project creation lock without app context."""

    @pytest.mark.asyncio
    async def test_creation_lock_exists(self, mock_settings: Mock, mock_controller: Mock) -> None:
        """Test creation lock is initialized."""
        with (
            patch("app.tui.views.onboarding_chat_screen.load_settings", return_value=mock_settings),
            patch(
                "app.tui.views.onboarding_chat_screen.OnboardingController",
                return_value=mock_controller,
            ),
            patch("app.tui.views.onboarding_chat_screen.LLMService"),
        ):
            screen = OnboardingChatScreen()

        assert hasattr(screen, "_creation_lock")
        assert isinstance(screen._creation_lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_complete_state_prevents_duplicate_creation(
        self, mock_settings: Mock, mock_controller: Mock
    ) -> None:
        """Test COMPLETE state prevents duplicate project creation."""
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

            # Mock app context
            mock_app = Mock()
            mock_app.call_from_thread = Mock(side_effect=lambda func, *args: func(*args))

            # Temporarily set app for this test
            with patch.object(type(screen), "app", property(lambda _: mock_app)):
                await screen.create_project()

        # Should remain COMPLETE and not proceed
        assert screen.state == OnboardingState.COMPLETE
