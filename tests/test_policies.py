"""Unit tests for session policy registry."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.llm.sessions import SessionPolicy, get_policy


def test_get_policy_clarify() -> None:
    """Test clarify stage policy configuration."""
    policy = get_policy("clarify")

    assert policy.stage == "clarify"
    assert policy.system_prompt_path == Path("app/llm/prompts/clarify.md")
    assert policy.allowed_tools == ["Read"]
    assert set(policy.denied_tools) == {"Write", "Edit", "Bash", "WebSearch", "WebFetch"}
    assert policy.write_roots == []
    assert policy.permission_mode == "readonly"
    assert policy.web_allow == []


def test_get_policy_kernel() -> None:
    """Test kernel stage policy configuration."""
    policy = get_policy("kernel")

    assert policy.stage == "kernel"
    assert policy.system_prompt_path == Path("app/llm/prompts/kernel.md")
    assert set(policy.allowed_tools) == {"Read", "Write", "Edit"}
    assert set(policy.denied_tools) == {"Bash", "WebSearch", "WebFetch"}
    assert policy.write_roots == ["projects/**"]
    assert policy.permission_mode == "restricted"
    assert policy.web_allow == []


def test_get_policy_outline() -> None:
    """Test outline stage policy configuration."""
    policy = get_policy("outline")

    assert policy.stage == "outline"
    assert policy.system_prompt_path == Path("app/llm/prompts/outline.md")
    assert set(policy.allowed_tools) == {"Read", "Write", "Edit"}
    assert set(policy.denied_tools) == {"Bash", "WebSearch", "WebFetch"}
    assert policy.write_roots == ["projects/**"]
    assert policy.permission_mode == "restricted"
    assert policy.web_allow == []


def test_get_policy_research_with_web_disabled() -> None:
    """Test research stage policy with web tools disabled."""
    with patch("app.llm.sessions.load_settings") as mock_settings:
        mock_settings.return_value.enable_web_tools = False
        policy = get_policy("research")

    assert policy.stage == "research"
    assert policy.system_prompt_path == Path("app/llm/prompts/research.md")
    assert set(policy.allowed_tools) == {"Read", "Write", "Edit"}
    assert "Bash" in policy.denied_tools
    assert policy.write_roots == ["projects/**"]
    assert policy.permission_mode == "restricted"
    assert policy.web_allow == []


def test_get_policy_research_with_web_enabled() -> None:
    """Test research stage policy with web tools enabled."""
    with patch("app.llm.sessions.load_settings") as mock_settings:
        mock_settings.return_value.enable_web_tools = True
        policy = get_policy("research")

    assert policy.stage == "research"
    assert policy.system_prompt_path == Path("app/llm/prompts/research.md")
    assert set(policy.allowed_tools) == {"Read", "Write", "Edit", "WebSearch", "WebFetch"}
    assert "Bash" in policy.denied_tools
    assert policy.write_roots == ["projects/**"]
    assert policy.permission_mode == "restricted"
    assert set(policy.web_allow) == {"WebSearch", "WebFetch"}


def test_get_policy_synthesis() -> None:
    """Test synthesis stage policy configuration."""
    policy = get_policy("synthesis")

    assert policy.stage == "synthesis"
    assert policy.system_prompt_path == Path("app/llm/prompts/synthesis.md")
    assert set(policy.allowed_tools) == {"Read", "Write", "Edit"}
    assert set(policy.denied_tools) == {"Bash", "WebSearch", "WebFetch"}
    assert policy.write_roots == ["projects/**"]
    assert policy.permission_mode == "restricted"
    assert policy.web_allow == []


def test_get_policy_invalid_stage() -> None:
    """Test that invalid stage raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        get_policy("invalid_stage")

    assert "Unknown stage: invalid_stage" in str(exc_info.value)
    assert "Valid stages are:" in str(exc_info.value)


def test_session_policy_is_frozen() -> None:
    """Test that SessionPolicy is immutable."""
    policy = SessionPolicy(
        stage="test",
        system_prompt_path=Path("test.md"),
        allowed_tools=[],
        denied_tools=[],
        write_roots=[],
        permission_mode="test",
        web_allow=[],
    )

    with pytest.raises(AttributeError):
        policy.stage = "modified"  # type: ignore


def test_policies_have_correct_prompt_paths() -> None:
    """Test that all policies have correctly formed prompt paths."""
    stages = ["clarify", "kernel", "outline", "research", "synthesis"]

    for stage in stages:
        policy = get_policy(stage)
        assert policy.system_prompt_path.suffix == ".md"
        assert "app/llm/prompts" in str(policy.system_prompt_path)
        # Note: synthesis and research stages use prompts that don't exist yet
        # but the paths should still be correctly formed
