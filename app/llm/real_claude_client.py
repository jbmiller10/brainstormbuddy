"""Real Claude client implementation using claude-code-sdk."""

from collections.abc import AsyncGenerator
from typing import Any

from app.llm.claude_client import (
    ClaudeClient,
    Event,
    MessageDone,
    TextDelta,
)

try:
    from claude_code_sdk import AssistantMessage, ClaudeCodeOptions, TextBlock, query

    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False

    # Define dummy classes for type hints when SDK not available
    class AssistantMessage:  # type: ignore
        content: list[Any] = []

    class TextBlock:  # type: ignore
        text: str = ""

    class ClaudeCodeOptions:  # type: ignore
        pass

    async def query(*args: Any, **kwargs: Any) -> AsyncGenerator[Any, None]:  # noqa: ARG001
        yield  # pragma: no cover


class RealClaudeClient(ClaudeClient):
    """Real Claude client implementation using claude-code-sdk."""

    def __init__(self) -> None:
        """Initialize the real Claude client."""
        if not CLAUDE_SDK_AVAILABLE:
            raise ImportError(
                "claude-code-sdk is not installed. Please install it with: pip install claude-code-sdk"
            )

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
        Stream events from Claude API using claude-code-sdk.

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
        # Configure options for Claude Code SDK
        options = ClaudeCodeOptions(
            system_prompt=system_prompt,
            allowed_tools=allowed_tools or [],
            denied_tools=denied_tools or [],
            permission_mode=permission_mode,
            cwd=cwd,
            max_turns=1,  # Single turn for our use case
        )

        try:
            # Stream messages from Claude
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    # Process assistant message content
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            # Yield text in chunks for streaming effect
                            text = block.text
                            # Split into lines for more natural streaming
                            lines = text.split("\n")
                            for i, line in enumerate(lines):
                                if i > 0:
                                    yield TextDelta("\n")
                                if line:
                                    yield TextDelta(line)
                        # Handle other block types if needed (ToolUse, etc.)
                        # For now, we're focusing on text generation

            # Signal completion
            yield MessageDone()

        except Exception as e:
            # Log error and fall back gracefully
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error streaming from Claude SDK: {e}")
            # Yield an error message to the user
            yield TextDelta(f"Error communicating with Claude: {str(e)}")
            yield MessageDone()


def is_claude_sdk_available() -> bool:
    """Check if the Claude SDK is available."""
    return CLAUDE_SDK_AVAILABLE
