"""Unit tests for FakeClaudeClient implementation."""

import pytest

from app.llm.claude_client import (
    Event,
    FakeClaudeClient,
    MessageDone,
    TextDelta,
)


@pytest.mark.asyncio  # type: ignore[misc]
async def test_fake_client_yields_events_in_order() -> None:
    """Test that FakeClaudeClient yields events in the expected order."""
    client = FakeClaudeClient()
    events: list[Event] = []

    async for event in client.stream("test prompt"):
        events.append(event)

    assert len(events) == 3
    assert isinstance(events[0], TextDelta)
    assert events[0].text == "First chunk of text"
    assert isinstance(events[1], TextDelta)
    assert events[1].text == "Second chunk of text"
    assert isinstance(events[2], MessageDone)


@pytest.mark.asyncio  # type: ignore[misc]
async def test_fake_client_accepts_all_parameters() -> None:
    """Test that FakeClaudeClient accepts all expected parameters."""
    client = FakeClaudeClient()
    events: list[Event] = []

    async for event in client.stream(
        prompt="test prompt",
        system_prompt="system context",
        allowed_tools=["tool1", "tool2"],
        denied_tools=["tool3"],
        permission_mode="restricted",
        cwd="/test/path",
    ):
        events.append(event)

    assert len(events) == 3
    assert all(isinstance(e, TextDelta | MessageDone) for e in events)


@pytest.mark.asyncio  # type: ignore[misc]
async def test_event_types_are_frozen() -> None:
    """Test that Event dataclasses are frozen and immutable."""
    delta = TextDelta("test")
    done = MessageDone()

    with pytest.raises(AttributeError):
        delta.text = "modified"  # type: ignore

    with pytest.raises(AttributeError):
        done.extra = "field"  # type: ignore


@pytest.mark.asyncio  # type: ignore[misc]
async def test_stream_can_be_consumed_multiple_times() -> None:
    """Test that the stream method can be called multiple times."""
    client = FakeClaudeClient()

    first_run = [event async for event in client.stream("prompt1")]
    second_run = [event async for event in client.stream("prompt2")]

    assert len(first_run) == 3
    assert len(second_run) == 3
    assert first_run[0] == second_run[0]  # Same deterministic output
