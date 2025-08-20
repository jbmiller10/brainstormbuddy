"""Onboarding controller for orchestrating new user flow."""

import re

from app.core.interfaces import OnboardingControllerProtocol
from app.llm.claude_client import ClaudeClient, FakeClaudeClient, MessageDone, TextDelta
from app.llm.sessions import get_policy


class OnboardingController(OnboardingControllerProtocol):
    """Controller for onboarding orchestration logic."""

    def __init__(self, client: ClaudeClient | None = None) -> None:
        """
        Initialize onboarding controller.

        Args:
            client: Claude client for LLM operations (defaults to FakeClaudeClient)
        """
        self.client = client or FakeClaudeClient()

    def generate_clarify_questions(self, braindump: str, *, count: int = 5) -> list[str]:
        """
        Generate exactly `count` clarifying questions (default 5).

        Args:
            braindump: Initial user braindump text
            count: Number of questions to generate (default 5)

        Returns:
            List of exactly `count` clarifying questions
        """
        # Get clarify stage policy
        policy = get_policy("clarify")

        # Read system prompt
        with open(policy.system_prompt_path, encoding="utf-8") as f:
            system_prompt = f.read()

        # Adjust prompt to request specific number of questions
        if count != 5:
            system_prompt = system_prompt.replace("3-7", str(count))
            system_prompt = system_prompt.replace("(3-7 total)", f"({count} total)")

        # Collect response from LLM
        full_response = ""
        try:
            # Use async generator in sync context via run_until_complete
            import asyncio

            async def _stream() -> None:
                nonlocal full_response
                async for event in self.client.stream(
                    prompt=braindump,
                    system_prompt=system_prompt,
                    allowed_tools=policy.allowed_tools,
                    denied_tools=policy.denied_tools,
                    permission_mode=policy.permission_mode,
                ):
                    if isinstance(event, TextDelta):
                        full_response += event.text
                    elif isinstance(event, MessageDone):
                        break

            # Run the async function
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _stream())
                    future.result()
            else:
                # If no loop is running, use asyncio.run
                asyncio.run(_stream())

        except Exception:
            # Fallback to default questions if LLM fails
            return [
                f"{i + 1}. What specific problem are you trying to solve?" for i in range(count)
            ]

        # Parse numbered questions from response
        questions = self._extract_numbered_questions(full_response, count)

        # Ensure we have exactly `count` questions
        if len(questions) < count:
            # Pad with generic questions
            for i in range(len(questions), count):
                questions.append(f"{i + 1}. Could you provide more details about this aspect?")
        elif len(questions) > count:
            # Trim to requested count
            questions = questions[:count]

        return questions

    def orchestrate_kernel_generation(self, braindump: str, answers_text: str) -> str:
        """
        Generate kernel.md content from braindump and a single consolidated answer string.

        Args:
            braindump: Initial user braindump text
            answers_text: Consolidated answers to clarifying questions

        Returns:
            Complete kernel.md markdown content

        Raises:
            ValueError: If kernel structure is invalid after retries
        """
        # Get kernel stage policy
        policy = get_policy("kernel")

        # Read system prompt
        with open(policy.system_prompt_path, encoding="utf-8") as f:
            system_prompt = f.read()

        # Combine braindump and answers into prompt
        combined_prompt = f"""Initial idea:
{braindump}

Clarified details:
{answers_text}

Please create a kernel document that captures the essence of this concept."""

        # Try up to 3 times (initial + 2 retries)
        for attempt in range(3):
            full_response = ""
            try:
                # Use async generator in sync context
                import asyncio

                async def _stream(prompt_text: str = combined_prompt) -> None:
                    nonlocal full_response
                    async for event in self.client.stream(
                        prompt=prompt_text,
                        system_prompt=system_prompt,
                        allowed_tools=policy.allowed_tools,
                        denied_tools=policy.denied_tools,
                        permission_mode=policy.permission_mode,
                    ):
                        if isinstance(event, TextDelta):
                            full_response += event.text
                        elif isinstance(event, MessageDone):
                            break

                # Run the async function
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, create a task
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _stream())
                        future.result()
                else:
                    # If no loop is running, use asyncio.run
                    asyncio.run(_stream())

            except Exception as e:
                if attempt == 2:
                    raise ValueError(f"Failed to generate kernel after 3 attempts: {e}") from e
                continue

            # Strip any code fences if present
            full_response = self._strip_code_fences(full_response)

            # Validate structure
            if self.validate_kernel_structure(full_response):
                return full_response

            # If invalid, adjust prompt for retry
            combined_prompt = f"""{combined_prompt}

IMPORTANT: The kernel must include exactly these 5 sections in order:
1. Core Concept
2. Key Questions
3. Success Criteria
4. Constraints
5. Primary Value Proposition

Start with "# Kernel" and use ## for section headers."""

        # If we get here, all attempts failed
        raise ValueError("Failed to generate valid kernel structure after 3 attempts")

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
        Extract numbered questions from LLM response.

        Args:
            text: Full LLM response text
            count: Expected number of questions

        Returns:
            List of question strings (without numbers)
        """
        questions: list[str] = []

        # Look for numbered patterns like "1. " or "1) "
        pattern = r"^\s*\d+[\.\)]\s+(.+)$"

        for line in text.split("\n"):
            match = re.match(pattern, line)
            if match:
                question = match.group(1).strip()
                # Remove trailing question mark if present and re-add for consistency
                if question.endswith("?"):
                    question = question[:-1]
                questions.append(f"{len(questions) + 1}. {question}?")

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
