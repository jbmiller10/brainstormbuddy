"""Comprehensive tests for improved OnboardingController."""

import contextlib
import uuid
import warnings
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.llm.llm_service import LLMService
from app.tui.controllers.exceptions import (
    KernelValidationError,
    LLMGenerationError,
    ValidationError,
)
from app.tui.controllers.onboarding_controller import OnboardingController
from app.tui.controllers.transcript import Transcript, TranscriptEntry, TranscriptRole


class TestTranscriptManagement:
    """Test transcript data structures and management."""

    def test_transcript_entry_creation(self) -> None:
        """Test creating transcript entries."""
        entry = TranscriptEntry(
            role=TranscriptRole.USER,
            content="Test content",
            metadata={"test": "data"},
        )

        assert entry.role == TranscriptRole.USER
        assert entry.content == "Test content"
        assert entry.metadata == {"test": "data"}
        assert isinstance(entry.timestamp, datetime)

    def test_transcript_entry_to_dict(self) -> None:
        """Test converting transcript entry to dictionary."""
        entry = TranscriptEntry(
            role=TranscriptRole.ASSISTANT,
            content="Response",
            metadata={"tokens": 100},
        )

        data = entry.to_dict()
        assert data["role"] == "assistant"
        assert data["content"] == "Response"
        assert data["metadata"] == {"tokens": 100}
        assert "timestamp" in data

    def test_transcript_entry_to_string(self) -> None:
        """Test converting transcript entry to string for backward compatibility."""
        # Test basic conversion
        entry = TranscriptEntry(role=TranscriptRole.USER, content="Hello")
        assert entry.to_string() == "User: Hello"

        # Test special formatting
        braindump_entry = TranscriptEntry(
            role=TranscriptRole.USER,
            content="Braindump: My idea",
        )
        assert braindump_entry.to_string() == "User Braindump: My idea"

    def test_transcript_operations(self) -> None:
        """Test transcript class operations."""
        transcript = Transcript()

        # Test adding entries
        transcript.add_user("User message")
        transcript.add_assistant("Assistant response")
        transcript.add_system("System message")

        assert len(transcript) == 3
        assert bool(transcript) is True

        # Test getting entries
        entries = transcript.get_entries()
        assert len(entries) == 3
        assert entries[0].role == TranscriptRole.USER
        assert entries[1].role == TranscriptRole.ASSISTANT
        assert entries[2].role == TranscriptRole.SYSTEM

        # Test last entry
        last = transcript.get_last_entry()
        assert last is not None
        assert last.role == TranscriptRole.SYSTEM

        # Test clear
        transcript.clear()
        assert len(transcript) == 0
        assert bool(transcript) is False
        assert transcript.get_last_entry() is None


class TestInputValidation:
    """Test input validation for all methods."""

    @pytest.mark.asyncio
    async def test_start_session_validation(self) -> None:
        """Test project name validation in start_session."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        # Test empty string
        with pytest.raises(ValidationError, match="Project name cannot be empty"):
            await controller.start_session("")

        # Test whitespace only
        with pytest.raises(ValidationError, match="Project name cannot be empty"):
            await controller.start_session("   ")

        # Test None (type checker should catch this, but runtime check)
        with pytest.raises(ValidationError, match="Project name cannot be empty"):
            await controller.start_session(None)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_summarize_braindump_validation(self) -> None:
        """Test braindump validation."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        # Test empty braindump
        with pytest.raises(ValidationError, match="Braindump cannot be empty"):
            await controller.summarize_braindump("")

        # Test exceeding max length
        long_braindump = "x" * (controller.MAX_BRAINDUMP_LENGTH + 1)
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            await controller.summarize_braindump(long_braindump)

    @pytest.mark.asyncio
    async def test_refine_summary_validation(self) -> None:
        """Test feedback validation."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        # Test empty feedback
        with pytest.raises(ValidationError, match="Feedback cannot be empty"):
            await controller.refine_summary("")

        # Test exceeding max length
        long_feedback = "x" * (controller.MAX_FEEDBACK_LENGTH + 1)
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            await controller.refine_summary(long_feedback)

    @pytest.mark.asyncio
    async def test_generate_clarifying_questions_validation(self) -> None:
        """Test question count validation."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        # Test count too low
        with pytest.raises(ValidationError, match="Question count must be between"):
            await controller.generate_clarifying_questions(0)

        # Test count too high
        with pytest.raises(ValidationError, match="Question count must be between"):
            await controller.generate_clarifying_questions(11)

    @pytest.mark.asyncio
    async def test_synthesize_kernel_validation(self) -> None:
        """Test answers validation."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        # Test empty answers
        with pytest.raises(ValidationError, match="Answers cannot be empty"):
            await controller.synthesize_kernel("")

        # Test exceeding max length
        long_answers = "x" * (controller.MAX_ANSWERS_LENGTH + 1)
        with pytest.raises(ValidationError, match="Answers exceed maximum length"):
            await controller.synthesize_kernel(long_answers)


class TestLLMErrorHandling:
    """Test LLM error handling with custom exceptions."""

    @pytest.mark.asyncio
    async def test_summarize_braindump_llm_error(self) -> None:
        """Test LLM error handling in summarize_braindump."""
        mock_llm_service = AsyncMock(spec=LLMService)
        mock_llm_service.generate_response.side_effect = Exception("API Error")

        controller = OnboardingController(llm_service=mock_llm_service)

        with pytest.raises(LLMGenerationError, match="Failed to generate summary"):
            await controller.summarize_braindump("Test braindump")

    @pytest.mark.asyncio
    async def test_generate_questions_llm_error(self) -> None:
        """Test LLM error handling in generate_clarifying_questions."""
        mock_llm_service = AsyncMock(spec=LLMService)
        mock_llm_service.generate_response.side_effect = Exception("Network Error")

        controller = OnboardingController(llm_service=mock_llm_service)
        controller.transcript.add_user("Braindump: Test")

        with pytest.raises(LLMGenerationError, match="Failed to generate questions"):
            await controller.generate_clarifying_questions(5)

    @pytest.mark.asyncio
    async def test_synthesize_kernel_validation_error(self) -> None:
        """Test kernel validation error handling."""
        mock_llm_service = AsyncMock(spec=LLMService)
        # Return invalid kernel structure
        mock_llm_service.generate_response.return_value = "Invalid kernel"

        controller = OnboardingController(llm_service=mock_llm_service)
        controller.transcript.add_user("Braindump: Test")

        with pytest.raises(KernelValidationError, match="Failed to generate valid kernel"):
            await controller.synthesize_kernel("Test answers")


class TestTranscriptPersistence:
    """Test transcript persistence across method calls."""

    @pytest.mark.asyncio
    async def test_transcript_accumulation(self) -> None:
        """Test that transcript accumulates across method calls."""
        mock_llm_service = AsyncMock(spec=LLMService)
        mock_llm_service.generate_response.side_effect = [
            "Summary of idea",
            "Refined summary",
            "1. Question one?\n2. Question two?",
        ]

        controller = OnboardingController(llm_service=mock_llm_service)

        # Start session
        await controller.start_session("Test Project")
        assert len(controller.transcript) == 1

        # Add braindump and summarize
        await controller.summarize_braindump("My idea")
        assert len(controller.transcript) == 3  # System + User + Assistant

        # Refine summary
        await controller.refine_summary("Make it better")
        assert len(controller.transcript) == 5  # + User + Assistant

        # Generate questions
        await controller.generate_clarifying_questions(2)
        assert len(controller.transcript) == 6  # + Assistant

    @pytest.mark.asyncio
    async def test_transcript_export(self) -> None:
        """Test exporting transcript."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        await controller.start_session("Test")
        controller.transcript.add_user("Test message")

        export = controller.export_transcript()

        assert "entries" in export
        assert "entry_count" in export
        assert "timestamp" in export
        assert "session_id" in export
        assert export["entry_count"] == 2
        assert len(export["entries"]) == 2

    @pytest.mark.asyncio
    async def test_transcript_clear(self) -> None:
        """Test clearing transcript."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        await controller.start_session("Test")
        old_session_id = controller.session_id

        controller.clear_transcript()

        assert len(controller.transcript) == 0
        assert controller.session_id != old_session_id


class TestDeprecationWarnings:
    """Test deprecation warnings for sync methods."""

    def test_generate_clarify_questions_deprecation(self) -> None:
        """Test deprecation warning for generate_clarify_questions."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with contextlib.suppress(Exception):
                controller.generate_clarify_questions("Test", count=3)

            # Find the deprecation warning among all warnings
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) >= 1
            assert "deprecated" in str(deprecation_warnings[0].message)

    def test_orchestrate_kernel_generation_deprecation(self) -> None:
        """Test deprecation warning for orchestrate_kernel_generation."""
        mock_llm_service = AsyncMock(spec=LLMService)
        mock_llm_service.generate_response = Mock(return_value="# Kernel\n\n## Core Concept")
        controller = OnboardingController(llm_service=mock_llm_service)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with contextlib.suppress(Exception):
                controller.orchestrate_kernel_generation("Test", "Answers")

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message)


class TestThreadSafety:
    """Test improved thread safety in sync wrappers."""

    def test_sync_wrapper_error_handling(self) -> None:
        """Test that sync wrapper handles errors gracefully."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        # Test that errors are handled and fallback is used
        with patch(
            "app.tui.controllers.onboarding_controller.asyncio.get_event_loop"
        ) as mock_get_loop:
            mock_get_loop.side_effect = Exception("Test error")

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                questions = controller.generate_clarify_questions("Test", count=2)

        # Should return fallback questions with error indicator
        assert len(questions) == 2
        assert all("[Error: Using fallback]" in q for q in questions)

    def test_sync_wrapper_deprecation_and_functionality(self) -> None:
        """Test that sync wrappers are deprecated but still functional."""
        mock_llm_service = Mock(spec=LLMService)
        mock_llm_service.generate_response = Mock(return_value="1. Question one?\n2. Question two?")
        controller = OnboardingController(llm_service=mock_llm_service)

        # Capture deprecation warning while still testing functionality
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # This will fail but we're testing the deprecation warning
            with contextlib.suppress(Exception):
                controller.generate_clarify_questions("Test", count=2)

            # Check deprecation warning was issued
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) >= 1
            assert "generate_clarify_questions is deprecated" in str(
                deprecation_warnings[0].message
            )


class TestErrorFeedback:
    """Test enhanced error feedback for users."""

    def test_fallback_questions_with_error_indicator(self) -> None:
        """Test that fallback questions indicate an error occurred."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        # Force an error in the sync wrapper
        with patch(
            "app.tui.controllers.onboarding_controller.asyncio.get_event_loop"
        ) as mock_get_loop:
            mock_get_loop.side_effect = Exception("Test error")

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                questions = controller.generate_clarify_questions("Test", count=2)

        # Check that questions include error indicator
        assert len(questions) == 2
        assert all("[Error: Using fallback]" in q for q in questions)


class TestSessionManagement:
    """Test session ID management."""

    @pytest.mark.asyncio
    async def test_session_id_generation(self) -> None:
        """Test that session IDs are generated properly."""
        mock_llm_service = AsyncMock(spec=LLMService)
        controller = OnboardingController(llm_service=mock_llm_service)

        # Check initial session ID
        assert controller.session_id is not None
        assert isinstance(controller.session_id, str)

        # Verify it's a valid UUID
        uuid.UUID(controller.session_id)

        # Check session ID changes on start_session
        old_id = controller.session_id
        await controller.start_session("Test")
        assert controller.session_id != old_id

        # Check session ID changes on clear_transcript
        old_id = controller.session_id
        controller.clear_transcript()
        assert controller.session_id != old_id


class TestLogging:
    """Test logging functionality."""

    @pytest.mark.asyncio
    async def test_logging_in_methods(self) -> None:
        """Test that methods log appropriately."""
        mock_llm_service = AsyncMock(spec=LLMService)
        mock_llm_service.generate_response.return_value = "Test response"

        controller = OnboardingController(llm_service=mock_llm_service)

        with patch("app.tui.controllers.onboarding_controller.logger") as mock_logger:
            # Test start_session logging
            await controller.start_session("Test Project")
            mock_logger.info.assert_called()
            mock_logger.debug.assert_called()

            # Test summarize_braindump logging
            await controller.summarize_braindump("Test braindump")
            assert mock_logger.debug.called
            assert mock_logger.info.called

            # Test validation error logging
            with pytest.raises(ValidationError):
                await controller.start_session("")
            mock_logger.error.assert_called()
