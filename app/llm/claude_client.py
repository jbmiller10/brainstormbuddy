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

        # Check if this is a kernel stage request
        if system_prompt and "kernel stage" in system_prompt.lower():
            # Generate a kernel document based on the prompt
            kernel_content = f"""## Core Concept
The essential idea is to {prompt[:100].lower().strip('.')}. This represents a focused approach to solving a specific problem through systematic exploration and implementation.

## Key Questions
1. What are the fundamental requirements that must be satisfied for this concept to succeed?
2. How can we validate the core assumptions before committing significant resources?
3. What are the critical dependencies and how can we mitigate risks associated with them?
4. How will we measure progress and know when key milestones are achieved?

## Success Criteria
- Clear problem-solution fit demonstrated through user feedback or metrics
- Scalable architecture that can grow with demand
- Measurable improvement over existing alternatives
- Sustainable resource model for long-term viability

## Constraints
- Must work within existing technical infrastructure
- Budget and timeline considerations must be realistic
- Regulatory and compliance requirements must be met
- User experience must remain intuitive and accessible

## Primary Value Proposition
This initiative creates value by directly addressing the identified problem space with a solution that is both practical and innovative. The approach balances technical feasibility with user needs, ensuring that the outcome is not just theoretically sound but also delivers tangible benefits in real-world applications."""

            # Stream the kernel content
            for chunk in kernel_content.split("\n"):
                yield TextDelta(chunk + "\n")

            # Signal completion
            yield MessageDone()

        # Check if this is a clarify stage request
        elif system_prompt and "clarify stage" in system_prompt.lower():
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
