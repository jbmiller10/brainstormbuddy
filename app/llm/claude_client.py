"""Claude client interface with streaming support and fake implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass


@dataclass(frozen=True)
class TextDelta:
    """Represents a text chunk in the stream."""

    text: str


@dataclass(frozen=True)
class ToolUseStart:
    """Indicates the start of tool usage."""

    tool_name: str
    tool_id: str


@dataclass(frozen=True)
class ToolUseEnd:
    """Indicates the end of tool usage."""

    tool_id: str
    result: str | None = None


@dataclass(frozen=True)
class MessageDone:
    """Indicates the message stream is complete."""

    pass


Event = TextDelta | ToolUseStart | ToolUseEnd | MessageDone


class ClaudeClient(ABC):
    """Abstract interface for Claude API clients."""

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        allowed_tools: list[str] | None = None,
        denied_tools: list[str] | None = None,
        permission_mode: str = "standard",
        cwd: str | None = None,
    ) -> AsyncGenerator[Event, None]:
        """
        Stream events from Claude API.

        Args:
            prompt: User prompt to send to Claude
            system_prompt: Optional system prompt to set context
            allowed_tools: List of allowed tool names
            denied_tools: List of denied tool names
            permission_mode: Permission mode for tool usage
            cwd: Current working directory for tool execution

        Yields:
            Event objects representing stream chunks
        """
        raise NotImplementedError
        yield  # pragma: no cover


class FakeClaudeClient(ClaudeClient):
    """Fake implementation for testing with deterministic output."""

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        allowed_tools: list[str] | None = None,
        denied_tools: list[str] | None = None,
        permission_mode: str = "standard",
        cwd: str | None = None,
    ) -> AsyncGenerator[Event, None]:
        """Yield a deterministic sequence of events for testing."""
        # Parameters are intentionally unused in fake implementation
        _ = (allowed_tools, denied_tools, permission_mode, cwd)

        # Check if this is a clarify stage request
        if system_prompt and "clarify stage" in system_prompt.lower():
            # Generate clarify questions based on the prompt
            yield TextDelta(f"I see you want to explore: {prompt[:100]}\n\n")
            yield TextDelta(
                "Let me ask some clarifying questions to help sharpen your thinking:\n\n"
            )

            questions = [
                "1. What specific problem are you trying to solve, and who will benefit most from the solution?",
                "2. What constraints (time, budget, technical, regulatory) must you work within?",
                "3. How would you measure success for this initiative after 3 months?",
                "4. What existing solutions have you considered, and why aren't they sufficient?",
                "5. What's the minimum viable version that would still deliver value?",
            ]

            for question in questions:
                yield TextDelta(f"{question}\n\n")

            yield MessageDone()
        else:
            # Default test output
            yield TextDelta("First chunk of text")
            yield TextDelta("Second chunk of text")
            yield MessageDone()
