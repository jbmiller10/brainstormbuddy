"""Onboarding controller for orchestrating new user flow."""

import asyncio
import concurrent.futures
import contextlib
import re

from app.core.interfaces import OnboardingControllerProtocol
from app.llm.llm_service import LLMService
from app.tui.controllers.onboarding_logger import OnboardingLogger


class OnboardingController(OnboardingControllerProtocol):
    """Controller for onboarding orchestration logic."""

    # Configuration constants
    MAX_KERNEL_ATTEMPTS = 3
    DEFAULT_QUESTION_COUNT = 5

    def __init__(self, llm_service: LLMService) -> None:
        """
        Initialize onboarding controller.

        Args:
            llm_service: LLM service for AI interactions
        """
        self.llm_service = llm_service
        self.transcript: list[str] = []
        self.logger = OnboardingLogger()

    async def start_session(self, project_name: str) -> None:
        """
        Initialize a new onboarding session.

        Args:
            project_name: Name of the project being created

        Raises:
            ValueError: If project name is empty or only whitespace
        """
        if not project_name or not project_name.strip():
            raise ValueError("Project name cannot be empty")

        self.transcript.clear()
        welcome_message = f"Starting new project: {project_name}"
        self.transcript.append(f"System: {welcome_message}")

    async def summarize_braindump(self, braindump: str) -> str:
        """
        Generate initial summary from user's braindump.

        Args:
            braindump: User's initial braindump text

        Returns:
            2-3 sentence summary of the braindump
        """
        self.transcript.append(f"User Braindump: {braindump}")

        summary = await self.llm_service.generate_response(
            transcript=self.transcript, system_prompt_name="summarize"
        )

        self.transcript.append(f"Assistant Summary: {summary}")
        return summary

    async def refine_summary(self, feedback: str) -> str:
        """
        Refine summary based on user feedback.

        Args:
            feedback: User's feedback on the initial summary

        Returns:
            Refined summary incorporating user feedback
        """
        self.transcript.append(f"User Feedback: {feedback}")

        refined_summary = await self.llm_service.generate_response(
            transcript=self.transcript, system_prompt_name="refine_summary"
        )

        self.transcript.append(f"Assistant Refined Summary: {refined_summary}")
        return refined_summary

    async def generate_clarifying_questions(self, count: int = 5) -> list[str]:
        """
        Generate clarifying questions based on conversation so far.

        Args:
            count: Number of questions to generate (default 5)

        Returns:
            List of numbered clarifying questions
        """
        # Generate questions using the clarify prompt
        response = await self.llm_service.generate_response(
            transcript=self.transcript, system_prompt_name="clarify"
        )

        # Parse numbered questions from response
        questions = self._extract_numbered_questions(response, count)

        # Ensure we have exactly `count` questions
        if len(questions) < count:
            # Pad with generic questions, preserving original numbering
            for i in range(len(questions), count):
                questions.append(f"{i + 1}. Could you provide more details about this aspect?")
        elif len(questions) > count:
            # Trim to requested count
            questions = questions[:count]

        # Add questions to transcript
        self.transcript.append(f"Assistant Questions: {', '.join(questions)}")

        return questions

    async def synthesize_kernel(self, answers: str) -> str:
        """
        Generate kernel from complete conversation transcript.

        Args:
            answers: User's answers to clarifying questions

        Returns:
            Complete kernel.md markdown content

        Raises:
            ValueError: If kernel structure is invalid after retries
        """
        self.transcript.append(f"User Answers: {answers}")

        # Try up to MAX_KERNEL_ATTEMPTS times
        for attempt in range(self.MAX_KERNEL_ATTEMPTS):
            try:
                kernel_content = await self.llm_service.generate_response(
                    transcript=self.transcript, system_prompt_name="kernel_from_transcript"
                )

                # Strip any code fences if present
                kernel_content = self._strip_code_fences(kernel_content)

                # Validate structure
                if self.validate_kernel_structure(kernel_content):
                    return kernel_content

                # If invalid, add feedback to transcript for retry
                if attempt < self.MAX_KERNEL_ATTEMPTS - 1:
                    self.transcript.append(
                        "System: Previous kernel was invalid. Please ensure the kernel includes "
                        "exactly these 5 sections in order: Core Concept, Key Questions, "
                        "Success Criteria, Constraints, Primary Value Proposition."
                    )
            except Exception as e:
                if attempt == self.MAX_KERNEL_ATTEMPTS - 1:
                    raise ValueError(
                        f"Failed to generate kernel after {self.MAX_KERNEL_ATTEMPTS} attempts: {e}"
                    ) from e
                # Add error feedback for retry
                self.transcript.append(f"System: Generation failed: {e}. Retrying...")

        # If we get here, all attempts failed
        raise ValueError(
            f"Failed to generate valid kernel structure after {self.MAX_KERNEL_ATTEMPTS} attempts"
        )

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
        """
        # Add braindump to transcript if not already there
        if not any("Braindump" in entry for entry in self.transcript):
            self.transcript.append(f"User Braindump: {braindump}")

        # Run async method synchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new event loop in a thread
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.generate_clarifying_questions(count))
                    questions = future.result()
            else:
                # If no loop is running, use asyncio.run
                questions = asyncio.run(self.generate_clarifying_questions(count))
        except Exception as e:
            # Fallback to default questions if async fails
            print(f"LLM request failed ({type(e).__name__}): {e}")
            questions = [
                f"{i + 1}. What specific problem are you trying to solve?" for i in range(count)
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
        """
        # Ensure braindump is in transcript
        if not any("Braindump" in entry for entry in self.transcript):
            self.transcript.append(f"User Braindump: {braindump}")

        # Run async method synchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new event loop in a thread
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.synthesize_kernel(answers_text))
                    kernel_content = future.result()
            else:
                # If no loop is running, use asyncio.run
                kernel_content = asyncio.run(self.synthesize_kernel(answers_text))

            # Log successful generation (fire-and-forget, non-blocking)
            if project_slug:
                with contextlib.suppress(Exception):
                    self.logger.log_kernel_generated(project_slug, kernel_content)

            return kernel_content
        except Exception as e:
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
            return False

        # Check the first 5 sections match exactly
        for i, required in enumerate(required_sections):
            if i >= len(found_sections):
                return False
            if found_sections[i] != required:
                return False

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

        return text.strip()
