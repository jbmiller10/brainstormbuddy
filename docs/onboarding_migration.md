# OnboardingController Migration Guide

## Overview

This guide helps you migrate from the synchronous OnboardingController methods to the new async-first architecture with improved error handling, validation, and transcript management.

## What's Changed

### 1. Structured Transcript Management
- **Old**: Simple list of strings (`list[str]`)
- **New**: Structured `Transcript` class with `TranscriptEntry` objects
- **Benefits**: Better type safety, metadata support, timestamp tracking

### 2. Enhanced Error Handling
- **Old**: Generic exceptions, inconsistent error handling
- **New**: Custom exception hierarchy with specific error types
- **Benefits**: More precise error identification, better debugging

### 3. Input Validation
- **Old**: Limited or no input validation
- **New**: Comprehensive validation with length limits and content checks
- **Benefits**: Prevents invalid state, better error messages

### 4. Thread Safety Improvements
- **Old**: ThreadPoolExecutor with new event loops (problematic)
- **New**: `run_coroutine_threadsafe` for better async integration
- **Benefits**: Safer concurrent execution, fewer threading issues

### 5. Deprecation Warnings
- **Old**: No migration path indicated
- **New**: Clear deprecation warnings with guidance
- **Benefits**: Smooth transition period, clear upgrade path

## Migration Steps

### Step 1: Update Imports

```python
# Old
from app.tui.controllers.onboarding_controller import OnboardingController
from app.llm.claude_client import ClaudeClient

# New
from app.tui.controllers.onboarding_controller import OnboardingController
from app.llm.llm_service import LLMService
from app.tui.controllers.exceptions import (
    ValidationError,
    LLMGenerationError,
    KernelValidationError,
)
```

### Step 2: Update Initialization

```python
# Old
client = ClaudeClient()
controller = OnboardingController(client)

# New
llm_service = LLMService(client)
controller = OnboardingController(llm_service)
```

### Step 3: Migrate to Async Methods

#### Starting a Session

```python
# Old (no explicit session start)
controller.generate_clarify_questions(braindump)

# New
await controller.start_session(project_name)
await controller.summarize_braindump(braindump)
```

#### Generating Questions

```python
# Old
questions = controller.generate_clarify_questions(
    braindump, count=5, project_slug="my-project"
)

# New
await controller.start_session("My Project")
await controller.summarize_braindump(braindump)
questions = await controller.generate_clarifying_questions(5)
```

#### Generating Kernel

```python
# Old
kernel = controller.orchestrate_kernel_generation(
    braindump, answers_text, project_slug="my-project"
)

# New
await controller.start_session("My Project")
await controller.summarize_braindump(braindump)
questions = await controller.generate_clarifying_questions()
kernel = await controller.synthesize_kernel(answers_text)
```

### Step 4: Handle New Exceptions

```python
# Old
try:
    kernel = controller.orchestrate_kernel_generation(braindump, answers)
except ValueError as e:
    print(f"Error: {e}")

# New
try:
    kernel = await controller.synthesize_kernel(answers)
except ValidationError as e:
    print(f"Invalid input: {e}")
except LLMGenerationError as e:
    print(f"LLM error: {e}")
except KernelValidationError as e:
    print(f"Invalid kernel structure: {e}")
```

### Step 5: Use Transcript Export

```python
# New feature - export conversation for debugging
export = controller.export_transcript()
print(f"Session {export['session_id']} has {export['entry_count']} entries")

# Save to file for debugging
import json
with open(f"transcript_{export['session_id']}.json", "w") as f:
    json.dump(export, f, indent=2)
```

## Complete Migration Example

### Old Code

```python
from app.tui.controllers.onboarding_controller import OnboardingController
from app.llm.claude_client import FakeClaudeClient

def onboard_project(braindump: str, project_slug: str):
    controller = OnboardingController(FakeClaudeClient())

    # Generate questions
    questions = controller.generate_clarify_questions(
        braindump, count=5, project_slug=project_slug
    )
    print("Questions:", questions)

    # Get answers from user
    answers = get_user_answers(questions)  # Your function

    # Generate kernel
    kernel = controller.orchestrate_kernel_generation(
        braindump, answers, project_slug=project_slug
    )
    return kernel
```

### New Code

```python
import asyncio
from app.tui.controllers.onboarding_controller import OnboardingController
from app.llm.llm_service import LLMService
from app.llm.claude_client import FakeClaudeClient
from app.tui.controllers.exceptions import ValidationError, LLMGenerationError

async def onboard_project(project_name: str, braindump: str):
    # Initialize with LLMService
    llm_service = LLMService(FakeClaudeClient())
    controller = OnboardingController(llm_service)

    try:
        # Start session
        await controller.start_session(project_name)

        # Summarize braindump
        summary = await controller.summarize_braindump(braindump)
        print("Summary:", summary)

        # Option to refine summary
        if needs_refinement(summary):  # Your function
            feedback = get_user_feedback()  # Your function
            summary = await controller.refine_summary(feedback)
            print("Refined summary:", summary)

        # Generate questions
        questions = await controller.generate_clarifying_questions(5)
        print("Questions:", questions)

        # Get answers from user
        answers = get_user_answers(questions)  # Your function

        # Generate kernel
        kernel = await controller.synthesize_kernel(answers)

        # Export transcript for debugging
        export = controller.export_transcript()
        save_transcript(export)  # Your function

        return kernel

    except ValidationError as e:
        print(f"Invalid input: {e}")
        raise
    except LLMGenerationError as e:
        print(f"LLM generation failed: {e}")
        raise

# Run the async function
kernel = asyncio.run(onboard_project("My Project", "My idea..."))
```

## Backward Compatibility

The old synchronous methods are still available but deprecated:

- `generate_clarify_questions()` → Use `generate_clarifying_questions()`
- `orchestrate_kernel_generation()` → Use `synthesize_kernel()`

These will show deprecation warnings:
```
DeprecationWarning: generate_clarify_questions is deprecated, use generate_clarifying_questions
```

## New Features

### 1. Session Management
```python
# Clear and start fresh
controller.clear_transcript()
await controller.start_session("New Project")
```

### 2. Transcript Export
```python
# Export for debugging/logging
export = controller.export_transcript()
```

### 3. Input Validation
```python
# Automatic validation with clear error messages
try:
    await controller.summarize_braindump("")  # Empty
except ValidationError as e:
    print(e)  # "Braindump cannot be empty"
```

### 4. Better Error Feedback
```python
# Fallback questions now indicate errors
questions = controller.generate_clarify_questions("test")
# If error: ["1. [Error: Using fallback] What specific problem..."]
```

## Testing

### Old Test Pattern

```python
def test_kernel_generation():
    controller = OnboardingController()
    kernel = controller.orchestrate_kernel_generation(
        "braindump", "answers"
    )
    assert "# Kernel" in kernel
```

### New Test Pattern

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_kernel_generation():
    mock_llm = AsyncMock(spec=LLMService)
    mock_llm.generate_response.return_value = "# Kernel..."

    controller = OnboardingController(mock_llm)
    await controller.start_session("Test")
    await controller.summarize_braindump("braindump")
    kernel = await controller.synthesize_kernel("answers")

    assert "# Kernel" in kernel
```

## Performance Considerations

1. **Async Methods**: More efficient for I/O-bound operations (LLM calls)
2. **Thread Safety**: Better handling of concurrent requests
3. **Validation**: Prevents unnecessary LLM calls for invalid input
4. **Logging**: Better observability without performance impact

## Troubleshooting

### Common Issues

1. **"No event loop" error**
   - Solution: Use `asyncio.run()` or ensure you're in an async context

2. **Deprecation warnings**
   - Solution: Migrate to async methods as shown above

3. **Validation errors**
   - Solution: Check input lengths and content before calling methods

4. **Thread safety issues**
   - Solution: Use async methods instead of sync wrappers for concurrent code

## Support

For issues or questions about migration:
1. Check the test files for usage examples
2. Review the docstrings in the updated controller
3. File an issue with the migration tag
