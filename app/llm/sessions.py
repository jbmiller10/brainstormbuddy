"""Session policy registry for stage-gated tool permissions and prompts."""

from dataclasses import dataclass
from pathlib import Path

from app.core.config import load_settings
from app.llm.agents import AgentSpec


@dataclass(frozen=True)
class SessionPolicy:
    """Configuration for a brainstorming session stage."""

    stage: str
    system_prompt_path: Path
    allowed_tools: list[str]
    denied_tools: list[str]
    write_roots: list[str]
    permission_mode: str
    web_tools_allowed: list[str]


def get_policy(stage: str) -> SessionPolicy:
    """
    Get the policy configuration for a given stage.

    Args:
        stage: One of 'clarify', 'kernel', 'outline', 'research', 'synthesis'

    Returns:
        SessionPolicy with appropriate configuration

    Raises:
        ValueError: If stage is not recognized
    """
    settings = load_settings()
    base_prompt_path = Path(__file__).resolve().parent / "prompts"

    policies = {
        "clarify": SessionPolicy(
            stage="clarify",
            system_prompt_path=base_prompt_path / "clarify.md",
            allowed_tools=["Read"],
            denied_tools=["Write", "Edit", "Bash", "WebSearch", "WebFetch"],
            write_roots=[],
            permission_mode="readonly",
            web_tools_allowed=[],
        ),
        "kernel": SessionPolicy(
            stage="kernel",
            system_prompt_path=base_prompt_path / "kernel.md",
            allowed_tools=["Read", "Write", "Edit"],
            denied_tools=["Bash", "WebSearch", "WebFetch"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=[],
        ),
        "outline": SessionPolicy(
            stage="outline",
            system_prompt_path=base_prompt_path / "outline.md",
            allowed_tools=["Read", "Write", "Edit"],
            denied_tools=["Bash", "WebSearch", "WebFetch"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=[],
        ),
        "research": SessionPolicy(
            stage="research",
            system_prompt_path=base_prompt_path / "research.md",
            allowed_tools=(
                ["Read", "Write", "Edit", "WebSearch", "WebFetch"]
                if settings.enable_web_tools
                else ["Read", "Write", "Edit"]
            ),
            denied_tools=["Bash"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=(["WebSearch", "WebFetch"] if settings.enable_web_tools else []),
        ),
        "synthesis": SessionPolicy(
            stage="synthesis",
            system_prompt_path=base_prompt_path / "synthesis.md",
            allowed_tools=["Read", "Write", "Edit"],
            denied_tools=["Bash", "WebSearch", "WebFetch"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=[],
        ),
    }

    if stage not in policies:
        raise ValueError(f"Unknown stage: {stage}. Valid stages are: {', '.join(policies.keys())}")

    return policies[stage]


def merge_agent_policy(stage_policy: SessionPolicy, agent_spec: AgentSpec | None) -> SessionPolicy:
    """
    Merge agent tools with stage policy, respecting denies.

    The merge logic:
    1. Start with stage's allowed tools
    2. If agent provided, intersect with agent's requested tools
    3. Remove any tools that are in stage's denied_tools
    4. Global denies always win

    Args:
        stage_policy: The base stage policy
        agent_spec: Optional agent specification with tool requests

    Returns:
        New SessionPolicy with merged tool permissions
    """
    # Start with stage's allowed tools
    allowed = set(stage_policy.allowed_tools)

    # If agent provided, intersect with agent's requested tools
    if agent_spec and agent_spec.tools:
        agent_tools = set(agent_spec.tools)
        allowed = allowed.intersection(agent_tools)

    # Remove any denied tools (denies always win)
    denied = set(stage_policy.denied_tools)
    final_allowed = allowed - denied

    # Convert back to sorted list for consistency
    final_allowed_list = sorted(final_allowed)

    # Create new policy with merged tools
    return SessionPolicy(
        stage=stage_policy.stage,
        system_prompt_path=stage_policy.system_prompt_path,
        allowed_tools=final_allowed_list,
        denied_tools=stage_policy.denied_tools,
        write_roots=stage_policy.write_roots,
        permission_mode=stage_policy.permission_mode,
        web_tools_allowed=[
            tool for tool in stage_policy.web_tools_allowed if tool in final_allowed_list
        ],
    )
