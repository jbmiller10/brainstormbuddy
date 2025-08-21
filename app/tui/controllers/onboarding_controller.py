"""Onboarding controller for orchestrating new user flow."""

import asyncio
import contextlib
import logging
import re
import uuid
import warnings
from asyncio import run_coroutine_threadsafe
from datetime import datetime
from typing import Any

from app.core.interfaces import OnboardingControllerProtocol
from app.llm.llm_service import LLMService
from app.tui.controllers.exceptions import (
    KernelValidationError,
    LLMGenerationError,
    ValidationError,
)
from app.tui.controllers.onboarding_logger import OnboardingLogger
from app.tui.controllers.transcript import Transcript

logger = logging.getLogger(__name__)


class OnboardingController(OnboardingControllerProtocol):
    """Controller for onboarding orchestration logic.

    This controller manages the conversational flow for project onboarding,
    maintaining a structured transcript of the conversation and orchestrating
    interactions with the LLM service.

    Thread Safety:
        The async methods are thread-safe when called from the same event loop.
        The sync wrapper methods handle event loop management but are not
        thread-safe when called concurrently from multiple threads.
    """

    # Configuration constants
    MAX_KERNEL_ATTEMPTS = 3
    DEFAULT_QUESTION_COUNT = 5
    MAX_BRAINDUMP_LENGTH = 10000
    MAX_ANSWERS_LENGTH = 5000
    MAX_FEEDBACK_LENGTH = 2000
    MIN_QUESTION_COUNT = 1
    MAX_QUESTION_COUNT = 10

    def __init__(self, llm_service: LLMService) -> None:
        """
        Initialize onboarding controller.

        Args:
            llm_service: LLM service for AI interactions
        """
        self.llm_service = llm_service
        self.transcript = Transcript()
        self.logger = OnboardingLogger()
        self.session_id = str(uuid.uuid4())
        logger.info(f"OnboardingController initialized with session {self.session_id}")

    async def start_session(self, project_name: str) -> None:
        """
        Initialize a new onboarding session.

        Args:
            project_name: Name of the project being created

        Raises:
            ValidationError: If project name is empty or only whitespace

        Example:
            >>> controller = OnboardingController(llm_service)
            >>> await controller.start_session("My Awesome Project")
        """
        if not project_name or not project_name.strip():
            logger.error(f"Invalid project name provided: '{project_name}'")
            raise ValidationError("Project name cannot be empty")

        logger.info(f"Starting new session for project: {project_name}")
        self.transcript.clear()
        self.session_id = str(uuid.uuid4())

        welcome_message = f"Starting new project: {project_name}"
        self.transcript.add_system(
            welcome_message,
            metadata={"project_name": project_name, "session_id": self.session_id},
        )
        logger.debug(f"Session {self.session_id} initialized with project '{project_name}'")

    async def summarize_braindump(self, braindump: str) -> str:
        """
        Generate initial summary from user's braindump.

        Args:
            braindump: User's initial braindump text

        Returns:
            2-3 sentence summary of the braindump

        Raises:
            ValidationError: If braindump is empty or exceeds max length
            LLMGenerationError: If LLM fails to generate summary

        Example:
            >>> summary = await controller.summarize_braindump(
            ...     "I want to build a task management app..."
            ... )
        """
        # Validate input
        if not braindump or not braindump.strip():
            logger.error("Empty braindump provided")
            raise ValidationError("Braindump cannot be empty")

        if len(braindump) > self.MAX_BRAINDUMP_LENGTH:
            logger.error(
                f"Braindump exceeds max length: {len(braindump)} > {self.MAX_BRAINDUMP_LENGTH}"
            )
            raise ValidationError(
                f"Braindump exceeds maximum length of {self.MAX_BRAINDUMP_LENGTH} characters"
            )

        logger.debug(f"Summarizing braindump of {len(braindump)} characters")
        self.transcript.add_user(f"Braindump: {braindump}")

        try:
            summary = await self.llm_service.generate_response(
                transcript=self.transcript.to_string_list(),
                system_prompt_name="summarize",
            )
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            raise LLMGenerationError(f"Failed to generate summary: {e}") from e

        self.transcript.add_assistant(f"Summary: {summary}")
        logger.info("Successfully generated braindump summary")
        return summary

    async def refine_summary(self, feedback: str) -> str:
        """
        Refine summary based on user feedback.

        Args:
            feedback: User's feedback on the initial summary

        Returns:
            Refined summary incorporating user feedback

        Raises:
            ValidationError: If feedback is empty or exceeds max length
            LLMGenerationError: If LLM fails to generate refined summary

        Example:
            >>> refined = await controller.refine_summary(
            ...     "Actually, the focus should be more on collaboration"
            ... )
        """
        # Validate input
        if not feedback or not feedback.strip():
            logger.error("Empty feedback provided")
            raise ValidationError("Feedback cannot be empty")

        if len(feedback) > self.MAX_FEEDBACK_LENGTH:
            logger.error(
                f"Feedback exceeds max length: {len(feedback)} > {self.MAX_FEEDBACK_LENGTH}"
            )
            raise ValidationError(
                f"Feedback exceeds maximum length of {self.MAX_FEEDBACK_LENGTH} characters"
            )

        logger.debug(f"Refining summary based on {len(feedback)} characters of feedback")
        self.transcript.add_user(f"Feedback: {feedback}")

        try:
            refined_summary = await self.llm_service.generate_response(
                transcript=self.transcript.to_string_list(),
                system_prompt_name="refine_summary",
            )
        except Exception as e:
            logger.error(f"Failed to refine summary: {e}")
            raise LLMGenerationError(f"Failed to refine summary: {e}") from e

        self.transcript.add_assistant(f"Refined Summary: {refined_summary}")
        logger.info("Successfully refined summary based on feedback")
        return refined_summary

    async def generate_clarifying_questions(self, count: int = 5) -> list[str]:
        """
        Generate clarifying questions based on conversation so far.

        Args:
            count: Number of questions to generate (default 5)

        Returns:
            List of numbered clarifying questions

        Raises:
            ValidationError: If count is outside valid range
            LLMGenerationError: If LLM fails to generate questions

        Example:
            >>> questions = await controller.generate_clarifying_questions(5)
            >>> for q in questions:
            ...     print(q)
        """
        # Validate count
        if not self.MIN_QUESTION_COUNT <= count <= self.MAX_QUESTION_COUNT:
            logger.error(f"Invalid question count: {count}")
            raise ValidationError(
                f"Question count must be between {self.MIN_QUESTION_COUNT} and {self.MAX_QUESTION_COUNT}"
            )

        logger.debug(f"Generating {count} clarifying questions")

        try:
            response = await self.llm_service.generate_response(
                transcript=self.transcript.to_string_list(),
                system_prompt_name="clarify",
            )
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            raise LLMGenerationError(f"Failed to generate questions: {e}") from e

        # Parse numbered questions from response
        questions = self._extract_numbered_questions(response, count)

        # Ensure we have exactly `count` questions
        if len(questions) < count:
            logger.warning(f"Generated only {len(questions)} questions, padding to {count}")
            for i in range(len(questions), count):
                questions.append(f"{i + 1}. Could you provide more details about this aspect?")
        elif len(questions) > count:
            logger.debug(f"Generated {len(questions)} questions, trimming to {count}")
            questions = questions[:count]

        # Add questions to transcript
        self.transcript.add_assistant(f"Questions: {', '.join(questions)}")
        logger.info(f"Successfully generated {len(questions)} clarifying questions")
        return questions

    async def synthesize_kernel(self, answers: str) -> str:
        """
        Generate kernel from complete conversation transcript.

        Args:
            answers: User's answers to clarifying questions

        Returns:
            Complete kernel.md markdown content

        Raises:
            ValidationError: If answers are empty or exceed max length
            KernelValidationError: If kernel structure is invalid after retries
            LLMGenerationError: If LLM fails to generate kernel

        Example:
            >>> kernel = await controller.synthesize_kernel(
            ...     "1. The main goal is... 2. The target users are..."
            ... )
        """
        # Validate input
        if not answers or not answers.strip():
            logger.error("Empty answers provided")
            raise ValidationError("Answers cannot be empty")

        if len(answers) > self.MAX_ANSWERS_LENGTH:
            logger.error(f"Answers exceed max length: {len(answers)} > {self.MAX_ANSWERS_LENGTH}")
            raise ValidationError(
                f"Answers exceed maximum length of {self.MAX_ANSWERS_LENGTH} characters"
            )

        logger.debug(f"Synthesizing kernel from {len(answers)} characters of answers")
        self.transcript.add_user(f"Answers: {answers}")

        # Try up to MAX_KERNEL_ATTEMPTS times
        for attempt in range(self.MAX_KERNEL_ATTEMPTS):
            try:
                logger.debug(f"Kernel generation attempt {attempt + 1}/{self.MAX_KERNEL_ATTEMPTS}")

                kernel_content = await self.llm_service.generate_response(
                    transcript=self.transcript.to_string_list(),
                    system_prompt_name="kernel_from_transcript",
                )

                # Strip any code fences if present
                kernel_content = self._strip_code_fences(kernel_content)

                # Validate structure
                if self.validate_kernel_structure(kernel_content):
                    logger.info("Successfully generated valid kernel")
                    return kernel_content

                # If invalid, add feedback to transcript for retry
                if attempt < self.MAX_KERNEL_ATTEMPTS - 1:
                    logger.warning(
                        f"Kernel validation failed on attempt {attempt + 1}, retrying..."
                    )
                    self.transcript.add_system(
                        "Previous kernel was invalid. Please ensure the kernel includes "
                        "exactly these 5 sections in order: Core Concept, Key Questions, "
                        "Success Criteria, Constraints, Primary Value Proposition."
                    )
            except Exception as e:
                logger.error(f"Kernel generation attempt {attempt + 1} failed: {e}")
                if attempt == self.MAX_KERNEL_ATTEMPTS - 1:
                    raise LLMGenerationError(
                        f"Failed to generate kernel after {self.MAX_KERNEL_ATTEMPTS} attempts: {e}"
                    ) from e
                # Add error feedback for retry
                self.transcript.add_system(f"Generation failed: {e}. Retrying...")

        # If we get here, all attempts failed
        logger.error(f"Failed to generate valid kernel after {self.MAX_KERNEL_ATTEMPTS} attempts")
        raise KernelValidationError(
            f"Failed to generate valid kernel structure after {self.MAX_KERNEL_ATTEMPTS} attempts"
        )

    def export_transcript(self) -> dict[str, Any]:
        """
        Export conversation transcript for debugging/logging.

        Returns:
            Dictionary containing transcript entries and metadata

        Example:
            >>> export = controller.export_transcript()
            >>> print(f"Session {export['session_id']} has {export['entry_count']} entries")
        """
        return {
            "entries": self.transcript.to_dict(),
            "entry_count": len(self.transcript),
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
        }

    def clear_transcript(self) -> None:
        """
        Clear the transcript and reset session.

        This is useful for starting fresh without creating a new controller instance.
        """
        logger.info(f"Clearing transcript for session {self.session_id}")
        self.transcript.clear()
        self.session_id = str(uuid.uuid4())
        logger.debug(f"New session ID: {self.session_id}")

    def generate_clarify_questions(
        self, braindump: str, *, count: int = 5, project_slug: str = ""
    ) -> list[str]:
        """
        Generate exactly `count` clarifying questions (default 5).

        This is a synchronous wrapper for backward compatibility.
        New code should use generate_clarifying_questions() instead.

        Note: This method is not thread-safe when called from
        multiple threads due to event loop management.

        Args:
            braindump: Initial user braindump text
            count: Number of questions to generate (default 5)
            project_slug: Project slug for logging context

        Returns:
            List of exactly `count` clarifying questions

        Deprecated:
            Use generate_clarifying_questions() for new code.
        """
        warnings.warn(
            "generate_clarify_questions is deprecated, use generate_clarifying_questions",
            DeprecationWarning,
            stacklevel=2,
        )

        # Add braindump to transcript if not already there
        if not any(entry.content.startswith("Braindump:") for entry in self.transcript):
            self.transcript.add_user(f"Braindump: {braindump}")

        # Run async method synchronously with improved thread safety
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop exists, create one
                logger.debug("No event loop found, using asyncio.run")
                questions = asyncio.run(self.generate_clarifying_questions(count))
            else:
                if loop.is_running():
                    # Running in async context - use run_coroutine_threadsafe
                    logger.debug("Running in async context, using run_coroutine_threadsafe")
                    future = run_coroutine_threadsafe(
                        self.generate_clarifying_questions(count), loop
                    )
                    questions = future.result(timeout=30)
                else:
                    # Loop exists but not running
                    logger.debug("Event loop exists but not running, using asyncio.run")
                    questions = asyncio.run(self.generate_clarifying_questions(count))
        except Exception as e:
            # Provide better error feedback
            logger.error(f"LLM request failed ({type(e).__name__}): {e}")
            questions = [
                f"{i + 1}. [Error: Using fallback] What specific problem are you trying to solve?"
                for i in range(count)
            ]

        # Log the event (fire-and-forget, non-blocking)
        if project_slug:
            with contextlib.suppress(Exception):
                self.logger.log_clarify_questions_shown(project_slug, questions, braindump)

        return questions

    def orchestrate_kernel_generation(
        self, braindump: str, answers_text: str, *, project_slug: str = ""
    ) -> str:
        """
        Generate kernel.md content from braindump and a single consolidated answer string.

        This is a synchronous wrapper for backward compatibility.
        New code should use synthesize_kernel() instead.

        Args:
            braindump: Initial user braindump text
            answers_text: Consolidated answers to clarifying questions
            project_slug: Project slug for logging context

        Returns:
            Complete kernel.md markdown content

        Raises:
            ValueError: If kernel structure is invalid after retries

        Deprecated:
            Use synthesize_kernel() for new code.
        """
        warnings.warn(
            "orchestrate_kernel_generation is deprecated, use synthesize_kernel",
            DeprecationWarning,
            stacklevel=2,
        )

        # Ensure braindump is in transcript
        if not any(entry.content.startswith("Braindump:") for entry in self.transcript):
            self.transcript.add_user(f"Braindump: {braindump}")

        # Run async method synchronously with improved thread safety
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop exists, create one
                logger.debug("No event loop found, using asyncio.run")
                kernel_content = asyncio.run(self.synthesize_kernel(answers_text))
            else:
                if loop.is_running():
                    # Running in async context - use run_coroutine_threadsafe
                    logger.debug("Running in async context, using run_coroutine_threadsafe")
                    future = run_coroutine_threadsafe(self.synthesize_kernel(answers_text), loop)
                    kernel_content = future.result(timeout=60)
                else:
                    # Loop exists but not running
                    logger.debug("Event loop exists but not running, using asyncio.run")
                    kernel_content = asyncio.run(self.synthesize_kernel(answers_text))

            # Log successful generation (fire-and-forget, non-blocking)
            if project_slug:
                with contextlib.suppress(Exception):
                    self.logger.log_kernel_generated(project_slug, kernel_content)

            return kernel_content
        except Exception as e:
            logger.error(f"Failed to generate kernel: {e}")
            raise ValueError(f"Failed to generate kernel: {e}") from e

    def validate_kernel_structure(self, kernel_content: str) -> bool:
        """
        Validate that kernel has all required sections in correct order.

        Args:
            kernel_content: Kernel markdown content to validate

        Returns:
            True if structure is valid, False otherwise
        """
        # Check it starts with # Kernel
        if not kernel_content.strip().startswith("# Kernel"):
            logger.debug("Kernel validation failed: missing '# Kernel' header")
            return False

        # Required sections in order
        required_sections = [
            "## Core Concept",
            "## Key Questions",
            "## Success Criteria",
            "## Constraints",
            "## Primary Value Proposition",
        ]

        # Find all section headers
        lines = kernel_content.strip().split("\n")
        found_sections = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("##"):
                # Normalize whitespace
                section = " ".join(stripped.split())
                found_sections.append(section)

        # Check all required sections are present in order
        if len(found_sections) < len(required_sections):
            logger.debug(
                f"Kernel validation failed: found {len(found_sections)} sections, "
                f"expected {len(required_sections)}"
            )
            return False

        # Check the first 5 sections match exactly
        for i, required in enumerate(required_sections):
            if i >= len(found_sections):
                logger.debug(f"Kernel validation failed: missing section {required}")
                return False
            if found_sections[i] != required:
                logger.debug(
                    f"Kernel validation failed: section {i} is '{found_sections[i]}', "
                    f"expected '{required}'"
                )
                return False

        logger.debug("Kernel validation passed")
        return True

    def _extract_numbered_questions(self, text: str, count: int) -> list[str]:
        """
        Extract numbered questions from LLM response, preserving original numbering.

        Args:
            text: Full LLM response text
            count: Expected number of questions

        Returns:
            List of question strings with original numbering preserved
        """
        questions: list[str] = []

        # Look for numbered patterns like "1. " or "1) " and capture the number
        pattern = r"^\s*(\d+)[\.\)]\s+(.+)$"

        for line in text.split("\n"):
            match = re.match(pattern, line)
            if match:
                original_number = match.group(1)
                question = match.group(2).strip()
                # Remove trailing question mark if present and re-add for consistency
                if question.endswith("?"):
                    question = question[:-1]
                # Preserve original numbering
                questions.append(f"{original_number}. {question}?")

                if len(questions) >= count:
                    break

        logger.debug(f"Extracted {len(questions)} questions from LLM response")
        return questions

    def _strip_code_fences(self, text: str) -> str:
        """
        Remove code fences from text if present.

        Args:
            text: Text that might contain code fences

        Returns:
            Text with code fences removed
        """
        # Remove markdown code fences
        if text.strip().startswith("```"):
            lines = text.strip().split("\n")
            # Find start and end of fence
            if lines[0].startswith("```"):
                lines = lines[1:]  # Remove first fence line
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]  # Remove last fence line
            text = "\n".join(lines)
            logger.debug("Stripped code fences from text")

        return text.strip()
