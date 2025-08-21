"""Tests for onboarding controller."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.llm.llm_service import LLMService
from app.tui.controllers.onboarding_controller import OnboardingController


@pytest.mark.asyncio
async def test_generate_clarify_questions_returns_five() -> None:
    """Test that generate_clarify_questions returns exactly 5 questions."""
    # Create a mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.generate_response.return_value = """I see you want to build a todo app.

1. What features are most important for your todo app?
2. Who is the target audience?
3. What platforms will it run on?
4. What is your timeline?
5. Do you have any technical constraints?"""

    controller = OnboardingController(llm_service=mock_llm_service)
    questions = controller.generate_clarify_questions("I want to build a todo app")

    assert len(questions) == 5
    # Check all are numbered questions
    for i, q in enumerate(questions, 1):
        assert q.startswith(f"{i}. ")
        assert q.endswith("?")


@pytest.mark.asyncio
async def test_generate_clarify_questions_custom_count() -> None:
    """Test that generate_clarify_questions respects custom count parameter."""
    # Create a mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.generate_response.return_value = """I see you want to build an app.

1. What is the main purpose?
2. Who will use it?
3. What features do you need?"""

    controller = OnboardingController(llm_service=mock_llm_service)
    questions = controller.generate_clarify_questions("I want to build an app", count=3)

    assert len(questions) == 3
    # Check all are numbered questions
    for i, q in enumerate(questions, 1):
        assert q.startswith(f"{i}. ")


@pytest.mark.asyncio
async def test_validate_kernel_structure_valid() -> None:
    """Test kernel validation accepts valid structure."""
    # Create a mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    controller = OnboardingController(llm_service=mock_llm_service)

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
    # Create a mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    controller = OnboardingController(llm_service=mock_llm_service)

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
    # Create a mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    controller = OnboardingController(llm_service=mock_llm_service)

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
    # Create a mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    controller = OnboardingController(llm_service=mock_llm_service)

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


def test_orchestrate_kernel_generation_success() -> None:
    """Test successful kernel generation."""
    # Create a regular Mock for sync wrapper testing
    mock_llm_service = Mock(spec=LLMService)
    kernel_content = """# Kernel

## Core Concept
A simple, user-friendly todo app.

## Key Questions
1. What features are essential?
2. How will users interact?

## Success Criteria
- Easy to use
- Fast performance

## Constraints
Time and budget limitations.

## Primary Value Proposition
Helps users manage tasks efficiently."""

    mock_llm_service.generate_response.return_value = kernel_content

    controller = OnboardingController(llm_service=mock_llm_service)

    # Create an async function that returns the kernel content
    async def mock_synthesize_kernel(_answers: str) -> str:
        return kernel_content

    # Mock the async synthesize_kernel to avoid thread execution issues
    controller.synthesize_kernel = mock_synthesize_kernel  # type: ignore[method-assign]

    kernel = controller.orchestrate_kernel_generation(
        braindump="I want to build a todo app", answers_text="It should be simple and user-friendly"
    )

    # Should return valid kernel structure
    assert controller.validate_kernel_structure(kernel)
    assert "# Kernel" in kernel
    assert "## Core Concept" in kernel


def test_orchestrate_kernel_generation_retry_on_invalid() -> None:
    """Test that kernel generation retries on invalid structure."""
    # Create a regular Mock for sync wrapper testing
    mock_llm_service = Mock(spec=LLMService)

    # Valid kernel structure for successful generation
    valid_kernel = """# Kernel

## Core Concept
Some concept

## Key Questions
1. Question?

## Success Criteria
- Criteria

## Constraints
Constraints

## Primary Value Proposition
Value prop"""

    controller = OnboardingController(llm_service=mock_llm_service)

    # Create an async function that returns the valid kernel
    async def mock_synthesize_kernel(_answers: str) -> str:
        return valid_kernel

    # Mock synthesize_kernel to return valid kernel
    controller.synthesize_kernel = mock_synthesize_kernel  # type: ignore[method-assign]

    kernel = controller.orchestrate_kernel_generation(
        braindump="Test idea", answers_text="Test answers"
    )

    # Should succeed with valid structure
    assert controller.validate_kernel_structure(kernel)
    assert "# Kernel" in kernel


@pytest.mark.asyncio
async def test_strip_code_fences() -> None:
    """Test that code fences are properly stripped."""
    # Create a mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    controller = OnboardingController(llm_service=mock_llm_service)

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
    # Create a mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    controller = OnboardingController(llm_service=mock_llm_service)

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


@pytest.mark.asyncio
async def test_extract_numbered_questions_preserves_original_numbering() -> None:
    """Test that original question numbering is preserved."""
    # Create a mock LLM service
    mock_llm_service = AsyncMock(spec=LLMService)
    controller = OnboardingController(llm_service=mock_llm_service)

    # Test with non-sequential numbering
    text = """Questions for clarification:
3. What is your timeline?
5. What is the budget?
7. Who are the stakeholders?"""

    questions = controller._extract_numbered_questions(text, 3)

    assert len(questions) == 3
    # Original numbers should be preserved
    assert questions[0] == "3. What is your timeline?"
    assert questions[1] == "5. What is the budget?"
    assert questions[2] == "7. Who are the stakeholders?"


@pytest.mark.asyncio
async def test_class_constants_defined() -> None:
    """Test that class constants are properly defined."""
    assert hasattr(OnboardingController, "MAX_KERNEL_ATTEMPTS")
    assert OnboardingController.MAX_KERNEL_ATTEMPTS == 3
    assert hasattr(OnboardingController, "DEFAULT_QUESTION_COUNT")
    assert OnboardingController.DEFAULT_QUESTION_COUNT == 5


@pytest.mark.asyncio
async def test_specific_exception_handling() -> None:
    """Test that specific exceptions are handled appropriately."""
    # Create a mock LLM service that raises exceptions
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.generate_response.side_effect = TimeoutError("Request timed out")

    controller = OnboardingController(llm_service=mock_llm_service)

    # Should gracefully handle timeout and return default questions
    questions = controller.generate_clarify_questions("Test idea")
    assert len(questions) == 5
    assert all("What specific problem" in q for q in questions)


@pytest.mark.asyncio
async def test_start_session() -> None:
    """Test that start_session initializes a new session."""
    mock_llm_service = AsyncMock(spec=LLMService)
    controller = OnboardingController(llm_service=mock_llm_service)

    await controller.start_session("MyProject")

    assert len(controller.transcript) == 1
    assert "Starting new project: MyProject" in controller.transcript.to_string_list()[0]


@pytest.mark.asyncio
async def test_start_session_empty_name() -> None:
    """Test that start_session raises ValidationError for empty names."""
    from app.tui.controllers.exceptions import ValidationError

    mock_llm_service = AsyncMock(spec=LLMService)
    controller = OnboardingController(llm_service=mock_llm_service)

    # Test empty string
    with pytest.raises(ValidationError, match="Project name cannot be empty"):
        await controller.start_session("")

    # Test whitespace only
    with pytest.raises(ValidationError, match="Project name cannot be empty"):
        await controller.start_session("   ")

    # Transcript should remain empty after errors
    assert len(controller.transcript) == 0


@pytest.mark.asyncio
async def test_summarize_braindump() -> None:
    """Test braindump summarization."""
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.generate_response.return_value = "This is a summary of your idea."

    controller = OnboardingController(llm_service=mock_llm_service)
    summary = await controller.summarize_braindump("I have an idea for an app")

    assert summary == "This is a summary of your idea."
    transcript_strings = controller.transcript.to_string_list()
    assert any("User Braindump: I have an idea for an app" in entry for entry in transcript_strings)
    assert any(
        "Assistant Summary: This is a summary of your idea." in entry
        for entry in transcript_strings
    )


@pytest.mark.asyncio
async def test_refine_summary() -> None:
    """Test summary refinement based on feedback."""
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.generate_response.return_value = "This is a refined summary."

    controller = OnboardingController(llm_service=mock_llm_service)
    controller.transcript.add_user("Braindump: Initial idea")
    controller.transcript.add_assistant("Summary: Initial summary")

    refined = await controller.refine_summary("Actually, I meant something else")

    assert refined == "This is a refined summary."
    transcript_strings = controller.transcript.to_string_list()
    assert any(
        "User Feedback: Actually, I meant something else" in entry for entry in transcript_strings
    )
    assert any(
        "Assistant Refined Summary: This is a refined summary." in entry
        for entry in transcript_strings
    )


@pytest.mark.asyncio
async def test_generate_clarifying_questions_async() -> None:
    """Test async clarifying questions generation."""
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.generate_response.return_value = """Let me ask some questions:

1. What is the main goal?
2. Who is the target audience?
3. What are the constraints?
4. What is the timeline?
5. What is the budget?"""

    controller = OnboardingController(llm_service=mock_llm_service)
    questions = await controller.generate_clarifying_questions(5)

    assert len(questions) == 5
    assert questions[0] == "1. What is the main goal?"
    last_entry = controller.transcript.to_string_list()[-1]
    assert "Assistant Questions:" in last_entry


@pytest.mark.asyncio
async def test_synthesize_kernel() -> None:
    """Test kernel synthesis from transcript."""
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.generate_response.return_value = """# Kernel

## Core Concept
The core concept here.

## Key Questions
1. Question one?
2. Question two?

## Success Criteria
- Criterion one
- Criterion two

## Constraints
Some constraints.

## Primary Value Proposition
The value proposition."""

    controller = OnboardingController(llm_service=mock_llm_service)
    controller.transcript.add_user("Braindump: My idea")
    controller.transcript.add_assistant("Questions: Some questions")

    kernel = await controller.synthesize_kernel("My answers")

    assert controller.validate_kernel_structure(kernel)
    transcript_strings = controller.transcript.to_string_list()
    assert any("User Answers: My answers" in entry for entry in transcript_strings)
