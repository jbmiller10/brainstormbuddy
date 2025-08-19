"""Claude client interface with streaming support and fake implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
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
    def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        allowed_tools: list[str] | None = None,
        denied_tools: list[str] | None = None,
        permission_mode: str = "standard",
        cwd: str | None = None,
    ) -> AsyncIterator[Event]:
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
        ...


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
    ) -> AsyncIterator[Event]:
        """Yield a deterministic sequence of events for testing."""
        # Parameters are intentionally unused in fake implementation
        _ = (prompt, system_prompt, allowed_tools, denied_tools, permission_mode, cwd)
        yield TextDelta("First chunk of text")
        yield TextDelta("Second chunk of text")
        yield MessageDone()
