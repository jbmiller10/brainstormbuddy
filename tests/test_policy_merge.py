"""Tests for agent policy merging with stage policies."""

from pathlib import Path

from app.llm.agents import AgentSpec
from app.llm.sessions import SessionPolicy, merge_agent_policy


def test_merge_with_empty_agent_tools() -> None:
    """Test that an agent with empty tools list results in no allowed tools."""
    stage_policy = SessionPolicy(
        stage="test",
        system_prompt_path=Path("test.md"),
        allowed_tools=["Read", "Write", "Edit"],
        denied_tools=["Bash"],
        write_roots=["projects/**"],
        permission_mode="restricted",
        web_tools_allowed=[],
    )

    agent_spec = AgentSpec(
        name="test_agent",
        description="Test agent",
        tools=[],  # Empty tools list
        prompt="Test prompt",
    )

    merged = merge_agent_policy(stage_policy, agent_spec)

    # When agent has empty tools, merged should have no allowed tools
    assert merged.allowed_tools == []
    # Other fields should remain unchanged
    assert merged.denied_tools == ["Bash"]
    assert merged.write_roots == ["projects/**"]
    assert merged.permission_mode == "restricted"


def test_merge_with_none_agent() -> None:
    """Test that merging with None agent returns stage policy unchanged."""
    stage_policy = SessionPolicy(
        stage="test",
        system_prompt_path=Path("test.md"),
        allowed_tools=["Read", "Write"],
        denied_tools=["Bash"],
        write_roots=["projects/**"],
        permission_mode="restricted",
        web_tools_allowed=[],
    )

    merged = merge_agent_policy(stage_policy, None)

    # Should return the same policy instance
    assert merged is stage_policy


def test_merge_with_agent_tools_intersection() -> None:
    """Test that agent tools are intersected with stage allowed tools."""
    stage_policy = SessionPolicy(
        stage="test",
        system_prompt_path=Path("test.md"),
        allowed_tools=["Read", "Write", "Edit"],
        denied_tools=["Bash", "WebSearch"],
        write_roots=["projects/**"],
        permission_mode="restricted",
        web_tools_allowed=[],
    )

    agent_spec = AgentSpec(
        name="test_agent",
        description="Test agent",
        tools=["Read", "Edit", "Bash"],  # Includes denied tool
        prompt="Test prompt",
    )

    merged = merge_agent_policy(stage_policy, agent_spec)

    # Should only include tools that are in both agent and stage allowed
    # Bash is excluded because it's in stage denied list
    assert set(merged.allowed_tools) == {"Read", "Edit"}
    assert merged.denied_tools == ["Bash", "WebSearch"]


def test_merge_with_disjoint_tools() -> None:
    """Test merging when agent and stage have no common allowed tools."""
    stage_policy = SessionPolicy(
        stage="test",
        system_prompt_path=Path("test.md"),
        allowed_tools=["Read", "Write"],
        denied_tools=["Bash"],
        write_roots=["projects/**"],
        permission_mode="restricted",
        web_tools_allowed=[],
    )

    agent_spec = AgentSpec(
        name="test_agent",
        description="Test agent",
        tools=["WebSearch", "WebFetch"],
        prompt="Test prompt",
    )

    merged = merge_agent_policy(stage_policy, agent_spec)

    # No intersection means no allowed tools
    assert merged.allowed_tools == []


def test_merge_preserves_other_policy_fields() -> None:
    """Test that merge preserves all non-tool fields from stage policy."""
    stage_policy = SessionPolicy(
        stage="research",
        system_prompt_path=Path("research.md"),
        allowed_tools=["Read", "Write", "Edit"],
        denied_tools=["Bash"],
        write_roots=["projects/**", "research/**"],
        permission_mode="restricted",
        web_tools_allowed=["WebSearch"],
    )

    agent_spec = AgentSpec(
        name="test_agent",
        description="Test agent",
        tools=["Read"],
        prompt="Test prompt",
    )

    merged = merge_agent_policy(stage_policy, agent_spec)

    # Check all fields except allowed_tools are preserved
    assert merged.stage == "research"
    assert merged.system_prompt_path == Path("research.md")
    assert merged.denied_tools == ["Bash"]
    assert merged.write_roots == ["projects/**", "research/**"]
    assert merged.permission_mode == "restricted"
    assert merged.web_tools_allowed == ["WebSearch"]
    # Only allowed_tools should change
    assert merged.allowed_tools == ["Read"]
