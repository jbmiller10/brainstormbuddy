"""Tests for synthesis controller."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.synthesis.controller import CriticIssue, SynthesisController, SynthesisResult


class TestSynthesisController:
    """Test synthesis controller operations."""

    @pytest.mark.asyncio
    async def test_load_kernel(self) -> None:
        """Test loading kernel from project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test project structure
            project_path = Path(tmpdir) / "projects" / "test-project"
            project_path.mkdir(parents=True)
            kernel_path = project_path / "kernel.md"
            kernel_content = "# Kernel\n\n## Core Concept\nTest concept"
            kernel_path.write_text(kernel_content)

            # Create controller
            controller = SynthesisController("test-project")
            controller.project_path = project_path

            # Load kernel
            result = await controller.load_kernel()
            assert result == kernel_content

    @pytest.mark.asyncio
    async def test_load_kernel_not_found(self) -> None:
        """Test loading kernel when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "projects" / "test-project"
            project_path.mkdir(parents=True)

            controller = SynthesisController("test-project")
            controller.project_path = project_path

            with pytest.raises(FileNotFoundError) as exc_info:
                await controller.load_kernel()
            assert "Kernel not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_findings_empty_db(self) -> None:
        """Test loading findings when database doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "projects" / "test-project"
            project_path.mkdir(parents=True)

            controller = SynthesisController("test-project")
            controller.project_path = project_path

            findings = await controller.load_findings("ui-ux")
            assert findings == []

    def test_format_findings_for_prompt(self) -> None:
        """Test formatting findings for LLM prompt."""
        controller = SynthesisController("test")

        findings = [
            {
                "claim": "React is popular",
                "evidence": "Survey shows 70% adoption",
                "url": "https://example.com",
                "confidence": 0.9,
                "tags": ["frontend", "react"],
            },
            {
                "claim": "TypeScript improves code quality",
                "evidence": "Studies show 50% fewer bugs",
                "confidence": 0.8,
                "tags": ["typescript"],
            },
        ]

        result = controller.format_findings_for_prompt(findings)

        assert "Finding 1:" in result
        assert "React is popular" in result
        assert "Survey shows 70% adoption" in result
        assert "https://example.com" in result
        assert "0.90" in result
        assert "frontend, react" in result

        assert "Finding 2:" in result
        assert "TypeScript improves code quality" in result

    def test_format_findings_empty(self) -> None:
        """Test formatting empty findings list."""
        controller = SynthesisController("test")
        result = controller.format_findings_for_prompt([])
        assert "No findings available" in result

    def test_format_findings_truncates_long_evidence(self) -> None:
        """Test that long evidence is truncated."""
        controller = SynthesisController("test")

        findings = [
            {
                "claim": "Test claim",
                "evidence": "x" * 300,  # Very long evidence
                "confidence": 0.5,
            }
        ]

        result = controller.format_findings_for_prompt(findings)
        assert "..." in result
        assert len(result.split("Evidence:")[1].split("\n")[0]) < 250

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_run_architect(self) -> None:
        """Test running architect subagent."""
        controller = SynthesisController("test")

        # Mock client stream
        mock_client = AsyncMock()
        controller.client = mock_client

        # Create mock events
        from app.llm.claude_client import MessageDone, TextDelta

        async def mock_stream(*args: Any, **kwargs: Any) -> Any:  # noqa: ARG001
            yield TextDelta("## Decisions\n")
            yield TextDelta("- Use React\n")
            yield TextDelta("## Requirements\n")
            yield TextDelta("- REQ-1: Test requirement\n")
            yield MessageDone()

        mock_client.stream = mock_stream

        # Mock agent specs
        with patch.object(controller, "get_agent_specs") as mock_specs:
            from app.llm.agents import AgentSpec

            mock_specs.return_value = [
                AgentSpec(
                    name="architect",
                    description="Test architect",
                    tools=["Read", "Write"],
                    prompt="Architect prompt",
                )
            ]

            result = await controller.run_architect(
                kernel="Test kernel",
                findings=[],
                workstream="ui-ux",
                workstream_title="UI/UX",
            )

        assert "## Decisions" in result
        assert "Use React" in result
        assert "## Requirements" in result

    @pytest.mark.asyncio
    async def test_run_critic_text_response(self) -> None:
        """Test running critic with text response (fallback parsing)."""
        controller = SynthesisController("test")

        # Mock client with text response
        mock_client = AsyncMock()
        controller.client = mock_client

        from app.llm.claude_client import MessageDone, TextDelta

        async def mock_stream(*args: Any, **kwargs: Any) -> Any:  # noqa: ARG001
            yield TextDelta("- severity: Critical\n")
            yield TextDelta("- section: Requirements\n")
            yield TextDelta("- message: Missing requirement\n")
            yield TextDelta("- action: Add requirement\n")
            yield TextDelta("\n- severity: Warning\n")
            yield TextDelta("section: Decisions\n")  # Test without dash
            yield TextDelta("message: Unclear decision\n")
            yield TextDelta("action: Clarify decision\n")
            yield MessageDone()

        mock_client.stream = mock_stream

        # Mock agent specs
        with patch.object(controller, "get_agent_specs") as mock_specs:
            from app.llm.agents import AgentSpec

            mock_specs.return_value = [
                AgentSpec(
                    name="critic",
                    description="Test critic",
                    tools=["Read"],
                    prompt="Critic prompt",
                )
            ]

            issues = await controller.run_critic(
                kernel="Test kernel",
                findings=[],
                proposal="Test proposal",
            )

        assert len(issues) == 2
        assert issues[0].severity == "Critical"
        assert issues[0].section == "Requirements"
        assert issues[0].message == "Missing requirement"
        assert issues[0].action == "Add requirement"
        assert issues[1].severity == "Warning"
        assert issues[1].section == "Decisions"

    @pytest.mark.asyncio
    async def test_run_critic_invalid_json(self) -> None:
        """Test running critic with completely invalid response."""
        controller = SynthesisController("test")

        # Mock client with invalid response
        mock_client = AsyncMock()
        controller.client = mock_client

        from app.llm.claude_client import MessageDone, TextDelta

        async def mock_stream(*args: Any, **kwargs: Any) -> Any:  # noqa: ARG001
            yield TextDelta("This is not JSON or structured text")
            yield MessageDone()

        mock_client.stream = mock_stream

        # Mock agent specs
        with patch.object(controller, "get_agent_specs") as mock_specs:
            from app.llm.agents import AgentSpec

            mock_specs.return_value = [
                AgentSpec(
                    name="critic",
                    description="Test critic",
                    tools=["Read"],
                    prompt="Critic prompt",
                )
            ]

            issues = await controller.run_critic(
                kernel="Test kernel",
                findings=[],
                proposal="Test proposal",
            )

        # Should return empty list when can't parse
        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_run_critic_json_response(self) -> None:
        """Test running critic with JSON response."""
        controller = SynthesisController("test")

        # Mock client
        mock_client = AsyncMock()
        controller.client = mock_client

        from app.llm.claude_client import MessageDone, TextDelta

        async def mock_stream(*args: Any, **kwargs: Any) -> Any:  # noqa: ARG001
            yield TextDelta('[{"severity": "Critical", "section": "Requirements", ')
            yield TextDelta('"message": "Missing requirement", "action": "Add requirement"}]')
            yield MessageDone()

        mock_client.stream = mock_stream

        # Mock agent specs
        with patch.object(controller, "get_agent_specs") as mock_specs:
            from app.llm.agents import AgentSpec

            mock_specs.return_value = [
                AgentSpec(
                    name="critic",
                    description="Test critic",
                    tools=["Read"],
                    prompt="Critic prompt",
                )
            ]

            issues = await controller.run_critic(
                kernel="Test kernel",
                findings=[],
                proposal="Test proposal",
            )

        assert len(issues) == 1
        assert issues[0].severity == "Critical"
        assert issues[0].section == "Requirements"
        assert issues[0].message == "Missing requirement"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_synthesize_workstream_full_flow(self) -> None:
        """Test full synthesis flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup project
            project_path = Path(tmpdir) / "projects" / "test-project"
            project_path.mkdir(parents=True)
            kernel_path = project_path / "kernel.md"
            kernel_path.write_text("# Test Kernel\n## Core Concept\nTest")

            controller = SynthesisController("test-project")
            controller.project_path = project_path

            # Mock architect response
            mock_client = AsyncMock()
            controller.client = mock_client

            from app.llm.claude_client import MessageDone, TextDelta

            async def mock_stream(*args: Any, **kwargs: Any) -> Any:  # noqa: ARG001
                yield TextDelta("# UI/UX\n")
                yield TextDelta("## Decisions\n- Decision 1\n")
                yield TextDelta("## Requirements\n- REQ-1: Requirement\n")
                yield TextDelta("## Open Questions\n- Q1: Question\n")
                yield TextDelta("## Risks & Mitigations\n- R1: Risk → Mitigation\n")
                yield TextDelta("## Acceptance Criteria\n- AC-1: Test criteria\n")
                yield MessageDone()

            mock_client.stream = mock_stream

            # Mock agent specs
            with patch.object(controller, "get_agent_specs") as mock_specs:
                from app.llm.agents import AgentSpec

                mock_specs.return_value = [
                    AgentSpec(
                        name="architect",
                        description="Test",
                        tools=["Read"],
                        prompt="Test",
                    )
                ]

                result = await controller.synthesize_workstream(
                    workstream="ui-ux",
                    run_critic=False,
                )

            assert isinstance(result, SynthesisResult)
            assert result.workstream == "ui-ux"
            assert "## Decisions" in result.proposal
            assert len(result.validation_errors) == 0
            assert result.critic_issues is None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_apply_synthesis(self) -> None:
        """Test applying synthesis result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "projects" / "test-project"
            elements_path = project_path / "elements"
            elements_path.mkdir(parents=True)

            controller = SynthesisController("test-project")
            controller.project_path = project_path

            result = SynthesisResult(
                workstream="ui-ux",
                proposal="# UI/UX\n## Decisions\nTest content",
                validation_errors=[],
                critic_issues=None,
                diff_preview="Test diff",
            )

            await controller.apply_synthesis(result)

            # Check file was created
            element_file = elements_path / "ui-ux.md"
            assert element_file.exists()
            assert element_file.read_text() == result.proposal
            assert result.applied is True

    @pytest.mark.asyncio
    async def test_synthesize_workstream_with_auto_fix(self) -> None:
        """Test synthesis with auto-fix enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup project
            project_path = Path(tmpdir) / "projects" / "test-project"
            project_path.mkdir(parents=True)
            kernel_path = project_path / "kernel.md"
            kernel_path.write_text("# Test Kernel\n## Core Concept\nTest")

            controller = SynthesisController("test-project")
            controller.project_path = project_path

            # Mock architect response with validation issues
            mock_client = AsyncMock()
            controller.client = mock_client

            from app.llm.claude_client import MessageDone, TextDelta

            async def mock_stream(*args: Any, **kwargs: Any) -> Any:  # noqa: ARG001
                # Return content with issues that need fixing
                yield TextDelta("# UI/UX\n")
                yield TextDelta("## decisions\n")  # Wrong case
                yield TextDelta("- Decision 1\n")
                yield TextDelta("## Requirements\n")
                yield TextDelta("- REQ-1: Requirement\n")
                yield TextDelta("## Open Questions\n")
                yield TextDelta("- Q1: Question\n")
                yield TextDelta("## Risks & Mitigations\n")
                yield TextDelta("- R1: Risk → Mitigation\n")
                yield TextDelta("## acceptance criteria\n")  # Wrong case
                yield TextDelta("- Given X, When Y, Then Z\n")  # Missing AC- prefix
                yield MessageDone()

            mock_client.stream = mock_stream

            # Mock agent specs
            with patch.object(controller, "get_agent_specs") as mock_specs:
                from app.llm.agents import AgentSpec

                mock_specs.return_value = [
                    AgentSpec(
                        name="architect",
                        description="Test",
                        tools=["Read"],
                        prompt="Test",
                    )
                ]

                result = await controller.synthesize_workstream(
                    workstream="ui-ux",
                    run_critic=False,
                    auto_fix=True,  # Enable auto-fix
                )

            assert isinstance(result, SynthesisResult)
            # Auto-fix should have corrected the issues
            assert "## Decisions" in result.proposal
            assert "## Acceptance Criteria" in result.proposal
            assert "- AC-1:" in result.proposal

    @pytest.mark.asyncio
    async def test_load_findings_with_database(self) -> None:
        """Test loading findings from actual database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "projects" / "test-project"
            research_path = project_path / "research"
            research_path.mkdir(parents=True)

            # Create a test database with findings
            from app.research.db import ResearchDB

            db_path = research_path / "findings.db"
            async with ResearchDB(db_path) as db:
                await db.insert_finding(
                    url="https://example.com/1",
                    source_type="web",
                    claim="Test claim 1",
                    evidence="Evidence 1",
                    confidence=0.9,
                    workstream="ui-ux",
                    tags=["test"],
                )
                await db.insert_finding(
                    url="https://example.com/2",
                    source_type="web",
                    claim="Test claim 2",
                    evidence="Evidence 2",
                    confidence=0.4,  # Below threshold
                    workstream="ui-ux",
                    tags=["test"],
                )
                await db.insert_finding(
                    url="https://example.com/3",
                    source_type="web",
                    claim="Test claim 3",
                    evidence="Evidence 3",
                    confidence=0.7,
                    workstream="backend",  # Different workstream
                    tags=["test"],
                )

            controller = SynthesisController("test-project")
            controller.project_path = project_path

            # Load findings for ui-ux with min confidence 0.5
            findings = await controller.load_findings("ui-ux", min_confidence=0.5)

            assert len(findings) == 1
            assert findings[0]["claim"] == "Test claim 1"
            assert findings[0]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_run_architect_no_agent_spec(self) -> None:
        """Test architect when agent spec not found."""
        controller = SynthesisController("test")

        with patch.object(controller, "get_agent_specs") as mock_specs:
            mock_specs.return_value = []  # No agents

            with pytest.raises(ValueError) as exc_info:
                await controller.run_architect(
                    kernel="Test",
                    findings=[],
                    workstream="ui",
                    workstream_title="UI",
                )
            assert "Architect agent specification not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_run_critic_no_agent_spec(self) -> None:
        """Test critic when agent spec not found."""
        controller = SynthesisController("test")

        with patch.object(controller, "get_agent_specs") as mock_specs:
            mock_specs.return_value = []  # No agents

            with pytest.raises(ValueError) as exc_info:
                await controller.run_critic(
                    kernel="Test",
                    findings=[],
                    proposal="Test",
                )
            assert "Critic agent specification not found" in str(exc_info.value)


class TestCriticIssue:
    """Test CriticIssue dataclass."""

    def test_create_critic_issue(self) -> None:
        """Test creating a critic issue."""
        issue = CriticIssue(
            severity="Critical",
            section="Requirements",
            message="Missing requirement",
            action="Add requirement X",
        )

        assert issue.severity == "Critical"
        assert issue.section == "Requirements"
        assert issue.message == "Missing requirement"
        assert issue.action == "Add requirement X"
