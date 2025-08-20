"""Controller for synthesis stage operations."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.files.atomic import atomic_write_text
from app.files.diff import generate_diff_preview
from app.files.validate_element import (
    ValidationError,
    auto_fix_element_structure,
    validate_element_structure,
)
from app.llm.agents import AgentSpec, load_agent_specs
from app.llm.claude_client import ClaudeClient, FakeClaudeClient, MessageDone, TextDelta
from app.llm.sessions import get_policy, merge_agent_policy
from app.research.db import ResearchDB
from app.synthesis.logger import SynthesisLogger

# Constants for synthesis operations
EVIDENCE_TRUNCATION_LENGTH = 200
DEFAULT_MIN_CONFIDENCE = 0.5
DEFAULT_MAX_FINDINGS = 200


@dataclass
class SynthesisConfig:
    """Configuration for synthesis operations."""

    min_confidence: float = DEFAULT_MIN_CONFIDENCE
    max_findings: int = DEFAULT_MAX_FINDINGS
    evidence_truncation_length: int = EVIDENCE_TRUNCATION_LENGTH
    enable_critic: bool = False
    enable_auto_fix: bool = False
    enable_progress_tracking: bool = True


@dataclass
class CriticIssue:
    """Represents an issue found by the critic."""

    severity: str  # Critical|Warning|Suggestion
    section: str
    message: str
    action: str


@dataclass
class SynthesisProgress:
    """Progress information for synthesis operations."""

    step: str  # Current step name
    progress: int  # Progress percentage (0-100)
    message: str  # Descriptive message
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SynthesisResult:
    """Result of synthesis operation."""

    workstream: str
    proposal: str
    validation_errors: list[ValidationError]
    critic_issues: list[CriticIssue] | None
    diff_preview: str
    applied: bool = False


class SynthesisController:
    """Manages synthesis operations for workstreams."""

    def __init__(
        self,
        project_slug: str,
        client: ClaudeClient | None = None,
        logger: SynthesisLogger | None = None,
        config: SynthesisConfig | None = None,
    ) -> None:
        """
        Initialize synthesis controller.

        Args:
            project_slug: Project identifier
            client: Claude client for LLM operations
            logger: Logger for tracking operations
            config: Synthesis configuration settings
        """
        self.project_slug = project_slug
        self.project_path = Path("projects") / project_slug
        self.client = client or FakeClaudeClient()
        self.logger = logger or SynthesisLogger()
        self.config = config or SynthesisConfig()
        self._agent_specs: list[AgentSpec] | None = None

    def get_agent_specs(self) -> list[AgentSpec]:
        """Load and cache agent specifications."""
        if self._agent_specs is None:
            self._agent_specs = load_agent_specs("app.llm.agentspecs")
        return self._agent_specs

    async def load_kernel(self) -> str:
        """
        Load kernel content from project.

        Returns:
            Kernel markdown content

        Raises:
            FileNotFoundError: If kernel.md doesn't exist
        """
        kernel_path = self.project_path / "kernel.md"
        if not kernel_path.exists():
            raise FileNotFoundError(f"Kernel not found at {kernel_path}; run Kernel stage first")

        with open(kernel_path, encoding="utf-8") as f:
            return f.read()

    async def load_findings(
        self,
        workstream: str,
        min_confidence: float | None = None,
        max_items: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Load research findings from database.

        Args:
            workstream: Workstream slug to filter by
            min_confidence: Minimum confidence threshold (uses config default if not specified)
            max_items: Maximum number of findings to return (uses config default if not specified)

        Returns:
            List of finding dictionaries sorted by confidence
        """
        # Use config defaults if not specified
        min_confidence = (
            min_confidence if min_confidence is not None else self.config.min_confidence
        )
        max_items = max_items if max_items is not None else self.config.max_findings

        db_path = self.project_path / "research" / "findings.db"
        if not db_path.exists():
            return []

        async with ResearchDB(db_path) as db:
            findings = await db.list_findings(
                workstream=workstream, min_confidence=min_confidence, limit=max_items
            )

        # Sort by confidence descending, take top items
        findings.sort(key=lambda f: f.get("confidence", 0), reverse=True)
        return findings[:max_items]

    def format_findings_for_prompt(self, findings: list[dict[str, Any]]) -> str:
        """
        Format findings for inclusion in architect prompt.

        Args:
            findings: List of finding dictionaries

        Returns:
            Formatted findings text
        """
        if not findings:
            return "No findings available for this workstream."

        lines = []
        for i, finding in enumerate(findings, 1):
            claim = finding.get("claim", "")
            evidence = finding.get("evidence", "")
            url = finding.get("url", "")
            confidence = finding.get("confidence", 0)
            tags = finding.get("tags", [])

            # Truncate evidence if too long
            truncate_len = self.config.evidence_truncation_length
            if len(evidence) > truncate_len:
                evidence = evidence[: truncate_len - 3] + "..."

            lines.append(f"- Finding {i}:")
            lines.append(f"  Claim: {claim}")
            lines.append(f"  Evidence: {evidence}")
            if url:
                lines.append(f"  Source: {url}")
            lines.append(f"  Confidence: {confidence:.2f}")
            if tags:
                lines.append(f"  Tags: {', '.join(tags)}")

        return "\n".join(lines)

    async def run_architect(
        self,
        kernel: str,
        findings: list[dict[str, Any]],
        workstream: str,
        workstream_title: str,
    ) -> str:
        """
        Run architect subagent to generate requirements.

        Args:
            kernel: Kernel content
            findings: Research findings
            workstream: Workstream slug
            workstream_title: Human-friendly workstream title

        Returns:
            Generated element markdown content
        """
        # Get architect agent spec
        agent_specs = self.get_agent_specs()
        architect_spec = next((a for a in agent_specs if a.name == "architect"), None)

        if not architect_spec:
            raise ValueError("Architect agent specification not found")

        # Get synthesis policy and merge with agent
        policy = get_policy("synthesis")
        policy = merge_agent_policy(policy, architect_spec)

        # Read synthesis prompt template to ensure it exists
        prompt_path = Path(__file__).resolve().parent.parent / "llm" / "prompts" / "synthesis.md"
        with open(prompt_path, encoding="utf-8") as f:
            _ = f.read()  # Read to validate file exists

        # Format the prompt with actual data
        findings_text = self.format_findings_for_prompt(findings)
        user_prompt = f"""Please generate a requirements document for the workstream: {workstream}

Context provided:
- Kernel document with core concepts
- {len(findings)} research findings filtered for this workstream
- Workstream title: {workstream_title}

<KERNEL>
{kernel}
</KERNEL>

<FINDINGS limit="{len(findings)}" min_confidence="0.5">
{findings_text}
</FINDINGS>

<WORKSTREAM>{workstream} - {workstream_title}</WORKSTREAM>

Generate the requirements document following the exact structure specified."""

        # Stream from architect
        result_chunks: list[str] = []
        async for event in self.client.stream(
            prompt=user_prompt,
            system_prompt=architect_spec.prompt,
            allowed_tools=policy.allowed_tools,
            denied_tools=policy.denied_tools,
            permission_mode=policy.permission_mode,
        ):
            if isinstance(event, TextDelta):
                result_chunks.append(event.text)
            elif isinstance(event, MessageDone):
                break

        return "".join(result_chunks)

    async def run_critic(
        self, kernel: str, findings: list[dict[str, Any]], proposal: str
    ) -> list[CriticIssue]:
        """
        Run critic subagent to review proposal.

        Args:
            kernel: Kernel content
            findings: Research findings used
            proposal: Architect's proposal

        Returns:
            List of critic issues
        """
        # Get critic agent spec
        agent_specs = self.get_agent_specs()
        critic_spec = next((a for a in agent_specs if a.name == "critic"), None)

        if not critic_spec:
            raise ValueError("Critic agent specification not found")

        # Get synthesis policy and merge with agent
        policy = get_policy("synthesis")
        policy = merge_agent_policy(policy, critic_spec)

        # Format critic prompt
        findings_text = self.format_findings_for_prompt(findings)
        user_prompt = f"""Review this workstream requirements document for logical gaps, missing acceptance criteria, ambiguous requirements, and ungrounded claims.

<KERNEL>
{kernel}
</KERNEL>

<FINDINGS>
{findings_text}
</FINDINGS>

<PROPOSAL>
{proposal}
</PROPOSAL>

Return your critique as a list with these fields for each issue:
- severity: Critical|Warning|Suggestion
- section: Which section the issue is in
- message: Short description of the issue
- action: Recommended fix

Format as JSON array."""

        # Stream from critic
        result_chunks: list[str] = []
        async for event in self.client.stream(
            prompt=user_prompt,
            system_prompt=critic_spec.prompt,
            allowed_tools=policy.allowed_tools,
            denied_tools=policy.denied_tools,
            permission_mode=policy.permission_mode,
        ):
            if isinstance(event, TextDelta):
                result_chunks.append(event.text)
            elif isinstance(event, MessageDone):
                break

        # Parse critic response
        response = "".join(result_chunks)
        issues: list[CriticIssue] = []

        try:
            # Try to parse as JSON
            issues_data = json.loads(response)
            if isinstance(issues_data, list):
                for item in issues_data:
                    if isinstance(item, dict):
                        issues.append(
                            CriticIssue(
                                severity=item.get("severity", "Suggestion"),
                                section=item.get("section", "Unknown"),
                                message=item.get("message", ""),
                                action=item.get("action", ""),
                            )
                        )
        except json.JSONDecodeError:
            # Fallback to text parsing if not valid JSON
            # Look for patterns like "severity: Critical"
            current_issue: dict[str, str] = {}
            for line in response.split("\n"):
                line = line.strip()
                if line.startswith("- severity:"):
                    if current_issue:
                        issues.append(
                            CriticIssue(
                                severity=current_issue.get("severity", "Suggestion"),
                                section=current_issue.get("section", "Unknown"),
                                message=current_issue.get("message", ""),
                                action=current_issue.get("action", ""),
                            )
                        )
                    current_issue = {"severity": line.replace("- severity:", "").strip()}
                elif line.startswith("- section:") or line.startswith("section:"):
                    current_issue["section"] = (
                        line.replace("- section:", "").replace("section:", "").strip()
                    )
                elif line.startswith("- message:") or line.startswith("message:"):
                    current_issue["message"] = (
                        line.replace("- message:", "").replace("message:", "").strip()
                    )
                elif line.startswith("- action:") or line.startswith("action:"):
                    current_issue["action"] = (
                        line.replace("- action:", "").replace("action:", "").strip()
                    )

            # Add last issue if any
            if current_issue:
                issues.append(
                    CriticIssue(
                        severity=current_issue.get("severity", "Suggestion"),
                        section=current_issue.get("section", "Unknown"),
                        message=current_issue.get("message", ""),
                        action=current_issue.get("action", ""),
                    )
                )

        return issues

    async def synthesize_workstream(
        self,
        workstream: str,
        workstream_title: str = "",
        run_critic: bool = False,
        auto_fix: bool = False,
        min_confidence: float = 0.5,
        max_findings: int = 200,
        progress_callback: Callable[[SynthesisProgress], None] | None = None,
    ) -> SynthesisResult:
        """
        Run full synthesis for a workstream.

        Args:
            workstream: Workstream slug
            workstream_title: Human-friendly title
            run_critic: Whether to run critic review
            auto_fix: Whether to apply auto-fixes
            min_confidence: Minimum confidence for findings
            max_findings: Maximum number of findings
            progress_callback: Optional callback for progress updates

        Returns:
            SynthesisResult with proposal and validation
        """

        def report_progress(step: str, progress: int, message: str, **details: Any) -> None:
            """Report progress if callback is configured."""
            if progress_callback and self.config.enable_progress_tracking:
                progress_callback(
                    SynthesisProgress(
                        step=step, progress=progress, message=message, details=details
                    )
                )

        # Log start
        await self.logger.log_event(
            stage="synthesis",
            event="start",
            data={"workstream": workstream, "project": self.project_slug},
        )
        report_progress("start", 0, f"Starting synthesis for {workstream}")

        # Load kernel
        report_progress("kernel", 10, "Loading project kernel...")
        kernel = await self.load_kernel()
        report_progress("kernel", 20, "Kernel loaded successfully")

        # Load findings
        report_progress("findings", 25, f"Loading research findings for {workstream}...")
        findings = await self.load_findings(workstream, min_confidence, max_findings)

        # Log findings loaded
        await self.logger.log_event(
            stage="synthesis",
            event="findings_loaded",
            data={"workstream": workstream, "findings_count": len(findings)},
        )
        report_progress(
            "findings", 35, f"Loaded {len(findings)} findings", findings_count=len(findings)
        )

        # Run architect
        if not workstream_title:
            workstream_title = workstream.replace("-", " ").title()

        report_progress("architect", 40, "Running architect agent to generate requirements...")
        proposal = await self.run_architect(kernel, findings, workstream, workstream_title)
        report_progress("architect", 60, "Requirements document generated")

        # Validate structure
        report_progress("validation", 65, "Validating document structure...")
        validation_errors = validate_element_structure(proposal)
        report_progress(
            "validation",
            70,
            f"Validation complete: {len(validation_errors)} issues found",
            errors_count=len(validation_errors),
        )

        # Run critic if requested
        critic_issues = None
        if run_critic:
            report_progress("critic", 75, "Running critic review...")
            await self.logger.log_event(
                stage="critic", event="start", data={"workstream": workstream}
            )
            critic_issues = await self.run_critic(kernel, findings, proposal)
            await self.logger.log_event(
                stage="critic",
                event="complete",
                data={
                    "workstream": workstream,
                    "issues_count": len(critic_issues),
                    "critical_count": sum(1 for i in critic_issues if i.severity == "Critical"),
                },
            )
            report_progress(
                "critic",
                85,
                f"Critic review complete: {len(critic_issues)} issues",
                issues_count=len(critic_issues),
            )

        # Apply auto-fixes if requested
        fixed_proposal = proposal
        if auto_fix and (
            validation_errors
            or (critic_issues and any(i.severity == "Critical" for i in critic_issues))
        ):
            report_progress("autofix", 90, "Applying automatic fixes...")
            fixed_proposal = auto_fix_element_structure(proposal, validation_errors)
            # Re-validate after fixes
            validation_errors = validate_element_structure(fixed_proposal)
            report_progress("autofix", 95, "Auto-fixes applied")

        # Generate diff preview
        element_path = self.project_path / "elements" / f"{workstream}.md"
        old_content = ""
        if element_path.exists():
            with open(element_path, encoding="utf-8") as f:
                old_content = f.read()

        diff_preview = generate_diff_preview(
            old_content,
            fixed_proposal,
            from_label=f"{element_path} (current)",
            to_label=f"{element_path} (proposed)",
        )

        # Count metrics
        ac_count = len(
            [line for line in fixed_proposal.split("\n") if line.strip().startswith("- AC-")]
        )
        req_count = len(
            [line for line in fixed_proposal.split("\n") if line.strip().startswith("- REQ-")]
        )

        # Log completion
        await self.logger.log_event(
            stage="synthesis",
            event="complete",
            data={
                "workstream": workstream,
                "findings_used": len(findings),
                "ac_count": ac_count,
                "requirements_count": req_count,
                "validation_errors": len(validation_errors),
                "critic_run": run_critic,
                "auto_fixed": auto_fix,
            },
        )

        report_progress(
            "complete",
            100,
            "Synthesis complete",
            ac_count=ac_count,
            req_count=req_count,
            validation_errors=len(validation_errors),
        )

        return SynthesisResult(
            workstream=workstream,
            proposal=fixed_proposal,
            validation_errors=validation_errors,
            critic_issues=critic_issues,
            diff_preview=diff_preview,
        )

    async def apply_synthesis(self, result: SynthesisResult) -> None:
        """
        Apply synthesis result to element file with rollback support.

        Args:
            result: Synthesis result to apply

        Raises:
            Exception: If application fails after backup
        """
        element_path = self.project_path / "elements" / f"{result.workstream}.md"
        element_path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists
        backup_content: str | None = None
        if element_path.exists():
            with open(element_path, encoding="utf-8") as f:
                backup_content = f.read()

        try:
            # Apply atomically
            atomic_write_text(element_path, result.proposal)

            # Mark as applied
            result.applied = True

            # Log application
            await self.logger.log_event(
                stage="synthesis",
                event="applied",
                data={"workstream": result.workstream, "path": str(element_path)},
            )
        except Exception as e:
            # Rollback on failure
            if backup_content is not None:
                try:
                    atomic_write_text(element_path, backup_content)
                    await self.logger.log_event(
                        stage="synthesis",
                        event="rollback",
                        data={
                            "workstream": result.workstream,
                            "reason": str(e),
                            "path": str(element_path),
                        },
                    )
                except Exception as rollback_error:
                    # Log critical failure
                    await self.logger.log_event(
                        stage="synthesis",
                        event="rollback_failed",
                        data={
                            "workstream": result.workstream,
                            "original_error": str(e),
                            "rollback_error": str(rollback_error),
                        },
                    )
                    raise
            raise
