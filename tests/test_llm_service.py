"""Tests for the LLMService class."""

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from app.llm.claude_client import FakeClaudeClient, MessageDone, TextDelta
from app.llm.llm_service import LLMService


@pytest.mark.asyncio
async def test_llm_service_initialization() -> None:
    """Test that LLMService initializes correctly with a client."""
    client = FakeClaudeClient()
    service = LLMService(client)

    assert service.client is client
    assert service._prompt_cache == {}


@pytest.mark.asyncio
async def test_load_system_prompt_caches_content() -> None:
    """Test that _load_system_prompt loads and caches prompt content."""
    client = FakeClaudeClient()
    service = LLMService(client)

    prompt_content = "Test prompt content"

    with (
        patch("builtins.open", mock_open(read_data=prompt_content)),
        patch.object(Path, "exists", return_value=True),
    ):
        # First call should load from file
        result1 = await service._load_system_prompt("test_prompt")
        assert result1 == prompt_content
        assert "test_prompt" in service._prompt_cache

        # Second call should use cache
        result2 = await service._load_system_prompt("test_prompt")
        assert result2 == prompt_content


@pytest.mark.asyncio
async def test_load_system_prompt_file_not_found() -> None:
    """Test that _load_system_prompt raises FileNotFoundError for missing files."""
    client = FakeClaudeClient()
    service = LLMService(client)

    with (
        patch.object(Path, "exists", return_value=False),
        pytest.raises(FileNotFoundError, match="Prompt 'nonexistent_prompt' not found"),
    ):
        await service._load_system_prompt("nonexistent_prompt")


@pytest.mark.asyncio
async def test_generate_response_with_fake_client() -> None:
    """Test generate_response with FakeClaudeClient."""
    client = FakeClaudeClient()
    service = LLMService(client)

    transcript = ["User: Hello", "Assistant: Hi there", "User: How are you?"]

    # Mock the prompt loading (now async)
    with patch.object(service, "_load_system_prompt", AsyncMock(return_value="System prompt")):
        response = await service.generate_response(transcript, "test_prompt")

    # FakeClaudeClient returns deterministic output
    assert "First chunk of text" in response
    assert "Second chunk of text" in response


@pytest.mark.asyncio
async def test_generate_response_aggregates_text_deltas() -> None:
    """Test that generate_response correctly aggregates TextDelta events."""
    # Create a mock client with custom streaming behavior
    mock_client = MagicMock()

    async def mock_stream(*_args: Any, **_kwargs: Any) -> Any:
        """Mock stream that yields specific events."""
        yield TextDelta("Hello ")
        yield TextDelta("world")
        yield TextDelta("!")
        yield MessageDone()

    mock_client.stream = mock_stream
    service = LLMService(mock_client)

    transcript = ["Test message"]

    # Mock the prompt loading (now async)
    with patch.object(service, "_load_system_prompt", AsyncMock(return_value="System prompt")):
        response = await service.generate_response(transcript, "test_prompt")

    assert response == "Hello world!"


@pytest.mark.asyncio
async def test_generate_response_handles_message_done() -> None:
    """Test that generate_response stops on MessageDone event."""
    mock_client = MagicMock()

    async def mock_stream(*_args: Any, **_kwargs: Any) -> Any:
        """Mock stream with MessageDone before additional events."""
        yield TextDelta("First part")
        yield MessageDone()
        # This should not be included
        yield TextDelta("Should not appear")

    mock_client.stream = mock_stream
    service = LLMService(mock_client)

    transcript = ["Test"]

    with patch.object(service, "_load_system_prompt", return_value="System"):
        response = await service.generate_response(transcript, "test")

    assert response == "First part"
    assert "Should not appear" not in response


@pytest.mark.asyncio
async def test_generate_response_joins_transcript() -> None:
    """Test that generate_response correctly joins transcript messages."""
    mock_client = MagicMock()
    called_with_prompt = None

    async def mock_stream(prompt: str, **_kwargs: Any) -> Any:
        """Capture the prompt passed to stream."""
        nonlocal called_with_prompt
        called_with_prompt = prompt
        yield TextDelta("Response")
        yield MessageDone()

    mock_client.stream = mock_stream
    service = LLMService(mock_client)

    transcript = ["Line 1", "Line 2", "Line 3"]

    with patch.object(service, "_load_system_prompt", return_value="System"):
        await service.generate_response(transcript, "test")

    assert called_with_prompt == "Line 1\nLine 2\nLine 3"


@pytest.mark.asyncio
async def test_generate_response_uses_correct_system_prompt() -> None:
    """Test that generate_response passes the correct system prompt to client."""
    mock_client = MagicMock()
    called_with_system_prompt = None

    async def mock_stream(**kwargs: Any) -> Any:
        """Capture the system_prompt passed to stream."""
        nonlocal called_with_system_prompt
        called_with_system_prompt = kwargs.get("system_prompt")
        yield TextDelta("Response")
        yield MessageDone()

    mock_client.stream = mock_stream
    service = LLMService(mock_client)

    expected_prompt = "This is the system prompt"

    with patch.object(service, "_load_system_prompt", return_value=expected_prompt):
        await service.generate_response(["Message"], "test_prompt")

    assert called_with_system_prompt == expected_prompt


@pytest.mark.asyncio
async def test_new_prompts_exist_and_valid() -> None:
    """Test that the new prompt files exist and have valid content."""
    prompt_dir = Path(__file__).parent.parent / "app" / "llm" / "prompts"

    new_prompts = ["summarize.md", "refine_summary.md", "kernel_from_transcript.md"]

    for prompt_file in new_prompts:
        prompt_path = prompt_dir / prompt_file
        assert prompt_path.exists(), f"Prompt file {prompt_file} should exist"

        # Verify the file is not empty and contains expected sections
        content = prompt_path.read_text()
        assert len(content) > 0, f"Prompt file {prompt_file} should not be empty"
        assert "<instructions>" in content, f"Prompt {prompt_file} should contain instructions"
        assert "<context>" in content, f"Prompt {prompt_file} should contain context"
        assert "<format>" in content, f"Prompt {prompt_file} should contain format"


@pytest.mark.asyncio
async def test_llm_service_with_real_prompts() -> None:
    """Integration test with real prompt files."""
    client = FakeClaudeClient()
    service = LLMService(client)

    # Test that we can load each of the new prompts
    prompts_to_test = ["summarize", "refine_summary", "kernel_from_transcript"]

    for prompt_name in prompts_to_test:
        prompt_content = await service._load_system_prompt(prompt_name)
        assert prompt_content, f"Should load {prompt_name} prompt"
        assert "<instructions>" in prompt_content

        # Verify caching works
        assert prompt_name in service._prompt_cache
        cached_content = await service._load_system_prompt(prompt_name)
        assert cached_content == prompt_content


@pytest.mark.asyncio
async def test_generate_response_handles_timeout_error() -> None:
    """Test that generate_response properly handles TimeoutError."""
    mock_client = MagicMock()

    async def mock_stream(*_args: Any, **_kwargs: Any) -> Any:
        """Mock stream that raises TimeoutError."""
        raise TimeoutError("Request timed out")
        yield  # pragma: no cover

    mock_client.stream = mock_stream
    service = LLMService(mock_client)

    with (
        patch.object(service, "_load_system_prompt", return_value="System"),
        pytest.raises(TimeoutError, match="LLM request timed out"),
    ):
        await service.generate_response(["Test"], "test_prompt")


@pytest.mark.asyncio
async def test_generate_response_handles_connection_error() -> None:
    """Test that generate_response properly handles ConnectionError."""
    mock_client = MagicMock()

    async def mock_stream(*_args: Any, **_kwargs: Any) -> Any:
        """Mock stream that raises ConnectionError."""
        raise ConnectionError("Connection failed")
        yield  # pragma: no cover

    mock_client.stream = mock_stream
    service = LLMService(mock_client)

    with (
        patch.object(service, "_load_system_prompt", return_value="System"),
        pytest.raises(ConnectionError, match="Network connection failed"),
    ):
        await service.generate_response(["Test"], "test_prompt")


@pytest.mark.asyncio
async def test_generate_response_handles_os_error() -> None:
    """Test that generate_response properly handles OSError."""
    mock_client = MagicMock()

    async def mock_stream(*_args: Any, **_kwargs: Any) -> Any:
        """Mock stream that raises OSError."""
        raise OSError("Network error")
        yield  # pragma: no cover

    mock_client.stream = mock_stream
    service = LLMService(mock_client)

    with (
        patch.object(service, "_load_system_prompt", return_value="System"),
        pytest.raises(ConnectionError, match="Network connection failed"),
    ):
        await service.generate_response(["Test"], "test_prompt")


@pytest.mark.asyncio
async def test_generate_response_handles_generic_exception() -> None:
    """Test that generate_response properly handles generic exceptions."""
    mock_client = MagicMock()

    async def mock_stream(*_args: Any, **_kwargs: Any) -> Any:
        """Mock stream that raises generic exception."""
        raise ValueError("Unexpected error")
        yield  # pragma: no cover

    mock_client.stream = mock_stream
    service = LLMService(mock_client)

    with (
        patch.object(service, "_load_system_prompt", AsyncMock(return_value="System")),
        pytest.raises(RuntimeError, match="Failed to generate response for prompt 'test_prompt'"),
    ):
        await service.generate_response(["Test"], "test_prompt")


@pytest.mark.asyncio
async def test_concurrent_cache_access() -> None:
    """Test that concurrent access to prompt cache is thread-safe."""
    client = FakeClaudeClient()
    service = LLMService(client)

    prompt_content = "Test concurrent access"
    call_count = 0

    # Create a mock open that tracks call count
    def mock_open_side_effect(*args: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        return mock_open(read_data=prompt_content)(*args, **kwargs)

    with (
        patch("builtins.open", side_effect=mock_open_side_effect),
        patch.object(Path, "exists", return_value=True),
    ):
        # Launch multiple concurrent loads of the same prompt
        tasks = [service._load_system_prompt("concurrent_test") for _ in range(10)]
        results = await asyncio.gather(*tasks)

    # All should return the same content
    assert all(r == prompt_content for r in results)
    # File should only be read once due to caching
    assert call_count == 1
    # Cache should contain the prompt
    assert "concurrent_test" in service._prompt_cache


@pytest.mark.asyncio
async def test_load_system_prompt_encoding_error() -> None:
    """Test that _load_system_prompt handles encoding errors gracefully."""
    client = FakeClaudeClient()
    service = LLMService(client)

    # Create mock file with non-UTF-8 content
    def mock_open_with_encoding_error(*_args: Any, **_kwargs: Any) -> Any:
        raise UnicodeDecodeError("utf-8", b"\xff\xfe", 0, 1, "invalid start byte")

    with (
        patch("builtins.open", side_effect=mock_open_with_encoding_error),
        patch.object(Path, "exists", return_value=True),
        pytest.raises(ValueError, match="Failed to decode prompt file 'bad_encoding'"),
    ):
        await service._load_system_prompt("bad_encoding")


@pytest.mark.asyncio
async def test_generate_response_empty_response() -> None:
    """Test that generate_response handles empty responses correctly."""
    mock_client = MagicMock()

    async def mock_stream(*_args: Any, **_kwargs: Any) -> Any:
        """Mock stream that only yields MessageDone."""
        yield MessageDone()

    mock_client.stream = mock_stream
    service = LLMService(mock_client)

    with patch.object(service, "_load_system_prompt", AsyncMock(return_value="System")):
        response = await service.generate_response(["Test"], "test_prompt")

    # Should return empty string without error
    assert response == ""
