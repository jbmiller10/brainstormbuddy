"""Tests for policy merge functionality."""

from pathlib import Path

import pytest

from app.llm.agents import AgentSpec
from app.llm.sessions import SessionPolicy, get_policy, merge_agent_policy


@pytest.fixture
def base_policy() -> SessionPolicy:
    """Create a base policy for testing."""
    return SessionPolicy(
        stage="test",
        system_prompt_path=Path("/tmp/test.md"),
        allowed_tools=["Read", "Write", "Edit"],
        denied_tools=["Bash", "WebSearch"],
        write_roots=["projects/**"],
        permission_mode="restricted",
        web_tools_allowed=["WebFetch"],
    )


@pytest.fixture
def agent_with_tools() -> AgentSpec:
    """Create an agent spec with tools."""
    return AgentSpec(
        name="test-agent",
        description="A test agent",
        tools=["Read", "Edit", "WebFetch", "Bash"],
        prompt="Test prompt",
    )


@pytest.fixture
def agent_without_tools() -> AgentSpec:
    """Create an agent spec without tools."""
    return AgentSpec(
        name="empty-agent",
        description="An agent with no tools",
        tools=[],
        prompt="Test prompt",
    )


def test_merge_with_no_agent(base_policy: SessionPolicy) -> None:
    """Test merging with no agent (None) returns base policy tools."""
    result = merge_agent_policy(base_policy, None)

    assert result.stage == base_policy.stage
    assert result.system_prompt_path == base_policy.system_prompt_path
    assert set(result.allowed_tools) == {"Read", "Write", "Edit"}
    assert result.denied_tools == base_policy.denied_tools
    assert result.write_roots == base_policy.write_roots
    assert result.permission_mode == base_policy.permission_mode


def test_merge_with_empty_agent_tools(
    base_policy: SessionPolicy, agent_without_tools: AgentSpec
) -> None:
    """Test merging with agent that has empty tools list."""
    result = merge_agent_policy(base_policy, agent_without_tools)

    # Empty agent tools means no tools allowed (intersection is empty)
    assert result.allowed_tools == []
    assert result.denied_tools == base_policy.denied_tools
    assert result.web_tools_allowed == []


def test_merge_with_full_overlap(base_policy: SessionPolicy) -> None:
    """Test merging when agent tools fully overlap with stage allowed."""
    agent = AgentSpec(
        name="overlap-agent",
        description="Agent with overlapping tools",
        tools=["Read", "Edit"],  # Subset of base allowed
        prompt="Test",
    )

    result = merge_agent_policy(base_policy, agent)

    # Should get intersection: Read, Edit
    assert set(result.allowed_tools) == {"Read", "Edit"}
    assert result.web_tools_allowed == []  # WebFetch not in agent tools


def test_merge_with_partial_overlap(
    base_policy: SessionPolicy, agent_with_tools: AgentSpec
) -> None:
    """Test merging when agent tools partially overlap with stage allowed."""
    # Agent has: Read, Edit, WebFetch, Bash
    # Stage allows: Read, Write, Edit
    # Stage denies: Bash, WebSearch

    result = merge_agent_policy(base_policy, agent_with_tools)

    # Intersection: Read, Edit (Write not in agent, WebFetch/Bash not in stage allowed)
    # After removing denied: still Read, Edit (Bash was never in intersection)
    assert set(result.allowed_tools) == {"Read", "Edit"}
    assert result.web_tools_allowed == []


def test_denied_tools_always_win() -> None:
    """Test that denied tools are always removed even if in intersection."""
    # Create policy where a tool is both allowed and denied (edge case)
    policy = SessionPolicy(
        stage="test",
        system_prompt_path=Path("/tmp/test.md"),
        allowed_tools=["Read", "Write", "Bash"],  # Bash is allowed
        denied_tools=["Bash"],  # But also denied
        write_roots=[],
        permission_mode="restricted",
        web_tools_allowed=[],
    )

    agent = AgentSpec(
        name="bash-agent",
        description="Agent wanting Bash",
        tools=["Read", "Bash"],
        prompt="Test",
    )

    result = merge_agent_policy(policy, agent)

    # Bash should be removed due to deny list
    assert "Bash" not in result.allowed_tools
    assert set(result.allowed_tools) == {"Read"}


def test_web_tools_filtered_correctly() -> None:
    """Test that web_tools_allowed is filtered based on final allowed tools."""
    # Modify base policy to have WebFetch in allowed
    policy = SessionPolicy(
        stage="test",
        system_prompt_path=Path("/tmp/test.md"),
        allowed_tools=["Read", "WebFetch", "WebSearch"],
        denied_tools=[],
        write_roots=[],
        permission_mode="restricted",
        web_tools_allowed=["WebFetch", "WebSearch"],
    )

    agent = AgentSpec(
        name="web-agent",
        description="Agent with limited web",
        tools=["Read", "WebFetch"],  # Only wants WebFetch, not WebSearch
        prompt="Test",
    )

    result = merge_agent_policy(policy, agent)

    # Only WebFetch should remain in web_tools_allowed
    assert set(result.allowed_tools) == {"Read", "WebFetch"}
    assert result.web_tools_allowed == ["WebFetch"]  # WebSearch filtered out


def test_merge_preserves_other_policy_fields(
    base_policy: SessionPolicy, agent_with_tools: AgentSpec
) -> None:
    """Test that merge preserves non-tool fields from base policy."""
    result = merge_agent_policy(base_policy, agent_with_tools)

    assert result.stage == base_policy.stage
    assert result.system_prompt_path == base_policy.system_prompt_path
    assert result.write_roots == base_policy.write_roots
    assert result.permission_mode == base_policy.permission_mode
    assert result.denied_tools == base_policy.denied_tools


def test_tools_are_sorted_consistently(base_policy: SessionPolicy) -> None:
    """Test that allowed tools are sorted for consistent output."""
    agent = AgentSpec(
        name="unsorted-agent",
        description="Agent with unsorted tools",
        tools=["Edit", "Write", "Read"],  # Deliberately unsorted
        prompt="Test",
    )

    result = merge_agent_policy(base_policy, agent)

    # Should be sorted alphabetically
    assert result.allowed_tools == ["Edit", "Read", "Write"]


def test_real_stage_policies_with_agents() -> None:
    """Test merging with actual stage policies from the system."""
    # Test with clarify stage (read-only)
    clarify_policy = get_policy("clarify")
    researcher = AgentSpec(
        name="researcher",
        description="Research agent",
        tools=["Read", "Write", "WebSearch", "WebFetch"],
        prompt="Research",
    )

    result = merge_agent_policy(clarify_policy, researcher)

    # Clarify only allows Read, so intersection is just Read
    # Clarify denies Write, WebSearch, WebFetch
    assert result.allowed_tools == ["Read"]
    assert result.web_tools_allowed == []

    # Test with research stage (allows web when enabled)
    research_policy = get_policy("research")
    critic = AgentSpec(
        name="critic",
        description="Critic agent",
        tools=["Read"],  # Read-only agent
        prompt="Critique",
    )

    result = merge_agent_policy(research_policy, critic)

    # Critic only wants Read, so that's all it gets
    assert result.allowed_tools == ["Read"]
    assert result.web_tools_allowed == []


def test_edge_case_agent_requests_only_denied_tools() -> None:
    """Test when agent only requests tools that are denied."""
    policy = SessionPolicy(
        stage="test",
        system_prompt_path=Path("/tmp/test.md"),
        allowed_tools=["Read", "Write", "Bash"],
        denied_tools=["Bash"],
        write_roots=[],
        permission_mode="restricted",
        web_tools_allowed=[],
    )

    agent = AgentSpec(
        name="denied-only",
        description="Agent requesting only denied tools",
        tools=["Bash"],
        prompt="Test",
    )

    result = merge_agent_policy(policy, agent)

    # No tools should be allowed
    assert result.allowed_tools == []
    assert result.web_tools_allowed == []
