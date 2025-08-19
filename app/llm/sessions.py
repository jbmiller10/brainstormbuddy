"""Session policy registry for stage-gated tool permissions and prompts."""

from dataclasses import dataclass
from pathlib import Path

from app.core.config import load_settings


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
