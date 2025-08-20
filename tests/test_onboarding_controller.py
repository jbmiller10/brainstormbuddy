"""Tests for onboarding controller."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.llm.claude_client import Event, MessageDone, TextDelta
from app.tui.controllers.onboarding_controller import OnboardingController


@pytest.mark.asyncio
async def test_generate_clarify_questions_returns_five() -> None:
    """Test that generate_clarify_questions returns exactly 5 questions."""
    controller = OnboardingController()

    questions = controller.generate_clarify_questions("I want to build a todo app")

    assert len(questions) == 5
    # Check all are numbered questions
    for i, q in enumerate(questions, 1):
        assert q.startswith(f"{i}. ")
        assert q.endswith("?")


@pytest.mark.asyncio
async def test_generate_clarify_questions_custom_count() -> None:
    """Test that generate_clarify_questions respects custom count parameter."""
    controller = OnboardingController()

    questions = controller.generate_clarify_questions("I want to build an app", count=3)

    assert len(questions) == 3
    # Check all are numbered questions
    for i, q in enumerate(questions, 1):
        assert q.startswith(f"{i}. ")


@pytest.mark.asyncio
async def test_validate_kernel_structure_valid() -> None:
    """Test kernel validation accepts valid structure."""
    controller = OnboardingController()

    valid_kernel = """# Kernel

## Core Concept
This is the core concept.

## Key Questions
1. Question one?
2. Question two?

## Success Criteria
- Criteria one
- Criteria two

## Constraints
Some constraints here.

## Primary Value Proposition
The main value proposition."""

    assert controller.validate_kernel_structure(valid_kernel) is True


@pytest.mark.asyncio
async def test_validate_kernel_structure_missing_section() -> None:
    """Test kernel validation rejects structure with missing section."""
    controller = OnboardingController()

    # Missing Constraints section
    invalid_kernel = """# Kernel

## Core Concept
This is the core concept.

## Key Questions
1. Question one?

## Success Criteria
- Criteria one

## Primary Value Proposition
The main value proposition."""

    assert controller.validate_kernel_structure(invalid_kernel) is False


@pytest.mark.asyncio
async def test_validate_kernel_structure_wrong_order() -> None:
    """Test kernel validation rejects structure with wrong section order."""
    controller = OnboardingController()

    # Constraints and Success Criteria swapped
    invalid_kernel = """# Kernel

## Core Concept
This is the core concept.

## Key Questions
1. Question one?

## Constraints
Some constraints.

## Success Criteria
- Criteria one

## Primary Value Proposition
The main value proposition."""

    assert controller.validate_kernel_structure(invalid_kernel) is False


@pytest.mark.asyncio
async def test_validate_kernel_structure_no_header() -> None:
    """Test kernel validation rejects structure without # Kernel header."""
    controller = OnboardingController()

    invalid_kernel = """## Core Concept
This is the core concept.

## Key Questions
1. Question one?

## Success Criteria
- Criteria one

## Constraints
Some constraints.

## Primary Value Proposition
The main value proposition."""

    assert controller.validate_kernel_structure(invalid_kernel) is False


@pytest.mark.asyncio
async def test_orchestrate_kernel_generation_success() -> None:
    """Test successful kernel generation."""
    controller = OnboardingController()

    kernel = controller.orchestrate_kernel_generation(
        braindump="I want to build a todo app", answers_text="It should be simple and user-friendly"
    )

    # Should return valid kernel structure
    assert controller.validate_kernel_structure(kernel)
    assert "# Kernel" in kernel
    assert "## Core Concept" in kernel


@pytest.mark.asyncio
async def test_orchestrate_kernel_generation_retry_on_invalid() -> None:
    """Test that kernel generation retries on invalid structure."""

    # Create a mock client that returns invalid then valid kernel
    mock_client = MagicMock()
    call_count = 0

    async def mock_stream(*_args: Any, **_kwargs: Any) -> AsyncGenerator[Event, None]:
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # First call: return invalid structure (missing section)
            yield TextDelta("# Kernel\n\n")
            yield TextDelta("## Core Concept\nSome concept\n\n")
            yield TextDelta("## Key Questions\n1. Question?\n\n")
            # Missing Success Criteria, Constraints, Primary Value Proposition
            yield MessageDone()
        else:
            # Second call: return valid structure
            yield TextDelta("# Kernel\n\n")
            yield TextDelta("## Core Concept\nSome concept\n\n")
            yield TextDelta("## Key Questions\n1. Question?\n\n")
            yield TextDelta("## Success Criteria\n- Criteria\n\n")
            yield TextDelta("## Constraints\nConstraints\n\n")
            yield TextDelta("## Primary Value Proposition\nValue prop\n")
            yield MessageDone()

    mock_client.stream = mock_stream
    controller = OnboardingController(client=mock_client)

    kernel = controller.orchestrate_kernel_generation(
        braindump="Test idea", answers_text="Test answers"
    )

    # Should succeed after retry
    assert controller.validate_kernel_structure(kernel)
    assert call_count == 2  # Should have been called twice


@pytest.mark.asyncio
async def test_strip_code_fences() -> None:
    """Test that code fences are properly stripped."""
    controller = OnboardingController()

    # Test with fences
    fenced = """```markdown
# Kernel

## Core Concept
Content here
```"""

    result = controller._strip_code_fences(fenced)
    assert not result.startswith("```")
    assert not result.endswith("```")
    assert result.startswith("# Kernel")

    # Test without fences
    unfenced = """# Kernel

## Core Concept
Content here"""

    result = controller._strip_code_fences(unfenced)
    assert result == unfenced.strip()


@pytest.mark.asyncio
async def test_extract_numbered_questions() -> None:
    """Test extraction of numbered questions from text."""
    controller = OnboardingController()

    text = """I see you want to explore this idea.

Let me ask some questions:

1. What is the main goal?
2. Who is the target audience?
3. What are the constraints?

These will help clarify your thinking."""

    questions = controller._extract_numbered_questions(text, 3)

    assert len(questions) == 3
    assert questions[0] == "1. What is the main goal?"
    assert questions[1] == "2. Who is the target audience?"
    assert questions[2] == "3. What are the constraints?"

    # Test with different numbering style
    text2 = """Questions:
1) First question?
2) Second question?"""

    questions2 = controller._extract_numbered_questions(text2, 2)
    assert len(questions2) == 2
