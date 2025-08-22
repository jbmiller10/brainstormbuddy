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

        # Check if this is a refine summary request (must check before general summarize)
        if system_prompt and "refining a project summary" in system_prompt.lower():
            # Generate a refined summary incorporating feedback
            yield TextDelta(
                "Based on your feedback, here's a refined understanding: You're building an intelligent "
                "brainstorming assistant that leverages AI to help users develop ideas systematically. "
                "The system will guide users through structured thinking processes while remaining flexible "
                "enough to adapt to different creative workflows."
            )
            yield MessageDone()

        # Check if this is an initial summarization request
        elif system_prompt and "initial onboarding phase" in system_prompt.lower():
            # Extract key info from the braindump
            idea_snippet = prompt[:200].strip()
            if "braindump:" in idea_snippet.lower():
                idea_snippet = idea_snippet.split(":", 1)[1].strip()

            # Generate a meaningful summary
            if "claude code" in idea_snippet.lower() or "agentic" in idea_snippet.lower():
                summary = (
                    "You want to build an AI-powered brainstorming application that provides intelligent assistance "
                    "similar to Claude Code, helping users develop and refine their ideas through guided conversation. "
                    "The goal is to create an agentic system that can understand context and provide meaningful support "
                    "throughout the creative process."
                )
            else:
                # Generic but contextual summary
                summary = (
                    f"You're envisioning {idea_snippet[:100]}. "
                    "This would involve creating a systematic approach to capture, refine, and develop ideas. "
                    "The focus is on building something that provides real value through intelligent assistance."
                )

            yield TextDelta(summary)
            yield MessageDone()

        # Check if this is a kernel generation request
        elif system_prompt and ("kernel" in system_prompt.lower() or "# Kernel" in system_prompt):
            # Generate a kernel document based on the prompt
            # Extract a meaningful snippet from the prompt for the core concept
            prompt_snippet = prompt[:100].lower().strip(".")
            if "skip" in prompt_snippet or "test" in prompt_snippet or len(prompt_snippet) < 20:
                # Use a generic but valid kernel for testing
                prompt_snippet = "create a solution that addresses user needs"

            kernel_content = f"""# Kernel

## Core Concept
The essential idea is to {prompt_snippet}. This represents a focused approach to solving a specific problem through systematic exploration and implementation.

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
        elif system_prompt and "clarify" in system_prompt.lower():
            # Generate clarify questions based on the prompt
            questions = [
                "1. What specific problem are you trying to solve, and who will benefit most from the solution?",
                "2. What constraints (time, budget, technical, regulatory) must you work within?",
                "3. How would you measure success for this initiative after 3 months?",
                "4. What existing solutions have you considered, and why aren't they sufficient?",
                "5. What's the minimum viable version that would still deliver value?",
            ]

            for question in questions:
                yield TextDelta(f"{question}\n")

            yield TextDelta("\nPlease provide your answers in a single response.")
            yield MessageDone()

        else:
            # Default test output for unrecognized prompts
            yield TextDelta("First chunk of text")
            yield TextDelta("Second chunk of text")
            yield MessageDone()
