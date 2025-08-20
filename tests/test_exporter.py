"""Tests for export functionality."""

import csv
import json
from pathlib import Path

import pytest

from app.export.exporter import (
    export_bundle,
    export_requirements,
    export_research_csv,
    export_research_jsonl,
)
from app.research.db import ResearchDB


@pytest.mark.asyncio
async def test_export_requirements_kernel_only(tmp_path: Path) -> None:
    """Test export with only kernel.md present."""
    project_path = tmp_path / "project"
    project_path.mkdir()
    export_path = tmp_path / "exports"

    # Create kernel.md
    kernel_content = "## Core Concept\n\nThis is the kernel content."
    (project_path / "kernel.md").write_text(kernel_content)

    # Export requirements
    await export_requirements(project_path, export_path)

    # Verify output
    requirements_file = export_path / "requirements.md"
    assert requirements_file.exists()
    content = requirements_file.read_text()
    assert "# Kernel" in content
    assert "This is the kernel content." in content
    assert "# Outline" not in content  # No outline present


@pytest.mark.asyncio
async def test_export_requirements_kernel_and_outline(tmp_path: Path) -> None:
    """Test export with kernel and outline present."""
    project_path = tmp_path / "project"
    project_path.mkdir()
    export_path = tmp_path / "exports"

    # Create kernel.md
    kernel_content = "## Core Concept\n\nKernel content."
    (project_path / "kernel.md").write_text(kernel_content)

    # Create outline.md
    outline_content = "## Executive Summary\n\nOutline content."
    (project_path / "outline.md").write_text(outline_content)

    # Export requirements
    await export_requirements(project_path, export_path)

    # Verify output
    requirements_file = export_path / "requirements.md"
    assert requirements_file.exists()
    content = requirements_file.read_text()
    assert "# Kernel" in content
    assert "Kernel content." in content
    assert "# Outline" in content
    assert "Outline content." in content
    assert content.index("# Kernel") < content.index("# Outline")  # Order matters


@pytest.mark.asyncio
async def test_export_requirements_full_set(tmp_path: Path) -> None:
    """Test export with kernel, outline, and multiple elements."""
    project_path = tmp_path / "project"
    project_path.mkdir()
    elements_dir = project_path / "elements"
    elements_dir.mkdir()
    export_path = tmp_path / "exports"

    # Create kernel.md
    (project_path / "kernel.md").write_text("Kernel content.")

    # Create outline.md
    (project_path / "outline.md").write_text("Outline content.")

    # Create element files
    (elements_dir / "requirements.md").write_text("Requirements content.")
    (elements_dir / "design.md").write_text("Design content.")
    (elements_dir / "research.md").write_text("Research content.")

    # Export requirements
    await export_requirements(project_path, export_path)

    # Verify output
    requirements_file = export_path / "requirements.md"
    assert requirements_file.exists()
    content = requirements_file.read_text()

    # Check all sections present
    assert "# Kernel" in content
    assert "# Outline" in content
    assert "# Design" in content
    assert "# Requirements" in content
    assert "# Research" in content

    # Check order (alphabetical for elements)
    kernel_pos = content.index("# Kernel")
    outline_pos = content.index("# Outline")
    design_pos = content.index("# Design")
    requirements_pos = content.index("# Requirements")
    research_pos = content.index("# Research")

    assert kernel_pos < outline_pos < design_pos < requirements_pos < research_pos


@pytest.mark.asyncio
async def test_export_requirements_empty_project(tmp_path: Path) -> None:
    """Test export with no markdown files present."""
    project_path = tmp_path / "project"
    project_path.mkdir()
    export_path = tmp_path / "exports"

    # Export requirements (no files present)
    await export_requirements(project_path, export_path)

    # Verify output is empty
    requirements_file = export_path / "requirements.md"
    assert requirements_file.exists()
    content = requirements_file.read_text()
    assert content == ""


@pytest.mark.asyncio
async def test_export_research_jsonl(tmp_path: Path) -> None:
    """Test JSONL export of research findings."""
    db_path = tmp_path / "test.db"
    export_path = tmp_path / "exports"

    # Create and populate database
    async with ResearchDB(db_path) as db:
        await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Test claim 1",
            evidence="Test evidence 1",
            confidence=0.8,
            tags=["tag1", "tag2"],
            workstream="research",
        )
        await db.insert_finding(
            url="https://example.org",
            source_type="paper",
            claim="Test claim 2",
            evidence="Test evidence 2",
            confidence=0.9,
            tags=["tag3"],
            workstream="synthesis",
        )

    # Export to JSONL
    await export_research_jsonl(db_path, export_path)

    # Verify output
    jsonl_file = export_path / "research.jsonl"
    assert jsonl_file.exists()

    # Parse JSONL
    lines = jsonl_file.read_text().strip().split("\n")
    assert len(lines) == 2

    # Parse both findings
    findings = [json.loads(line) for line in lines]

    # Check both findings exist (order doesn't matter for this test)
    urls = [f["url"] for f in findings]
    assert "https://example.com" in urls
    assert "https://example.org" in urls

    # Find each specific finding and verify
    for finding in findings:
        if finding["url"] == "https://example.com":
            assert finding["claim"] == "Test claim 1"
            assert finding["confidence"] == 0.8
            assert finding["tags"] == ["tag1", "tag2"]
        elif finding["url"] == "https://example.org":
            assert finding["claim"] == "Test claim 2"
            assert finding["confidence"] == 0.9


@pytest.mark.asyncio
async def test_export_research_csv(tmp_path: Path) -> None:
    """Test CSV export of research findings."""
    db_path = tmp_path / "test.db"
    export_path = tmp_path / "exports"

    # Create and populate database
    async with ResearchDB(db_path) as db:
        await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Test claim",
            evidence="Test evidence",
            confidence=0.85,
            tags=["tag1", "tag2"],
            workstream="research",
        )

    # Export to CSV
    await export_research_csv(db_path, export_path)

    # Verify output
    csv_file = export_path / "research.csv"
    assert csv_file.exists()

    # Parse CSV
    content = csv_file.read_text()
    lines = content.strip().split("\n")

    # Check headers
    assert lines[0].startswith(
        "id,url,source_type,claim,evidence,confidence,tags,workstream,retrieved_at"
    )

    # Parse data row
    reader = csv.DictReader(content.splitlines())
    rows = list(reader)
    assert len(rows) == 1

    row = rows[0]
    assert row["url"] == "https://example.com"
    assert row["claim"] == "Test claim"
    assert float(row["confidence"]) == 0.85
    # Tags should be JSON-encoded in CSV
    tags = json.loads(row["tags"])
    assert tags == ["tag1", "tag2"]


@pytest.mark.asyncio
async def test_export_research_empty_database(tmp_path: Path) -> None:
    """Test export with empty database."""
    db_path = tmp_path / "test.db"
    export_path = tmp_path / "exports"

    # Create empty database
    async with ResearchDB(db_path):
        pass  # Just initialize

    # Export to JSONL
    await export_research_jsonl(db_path, export_path)
    jsonl_file = export_path / "research.jsonl"
    assert jsonl_file.exists()
    assert jsonl_file.read_text() == ""

    # Export to CSV
    await export_research_csv(db_path, export_path)
    csv_file = export_path / "research.csv"
    assert csv_file.exists()
    # CSV should have headers even when empty
    content = csv_file.read_text()
    assert "id,url,source_type,claim,evidence,confidence,tags,workstream,retrieved_at" in content


@pytest.mark.asyncio
async def test_export_bundle(tmp_path: Path) -> None:
    """Test complete bundle export."""
    project_path = tmp_path / "project"
    project_path.mkdir()
    db_path = tmp_path / "test.db"

    # Create project files
    (project_path / "kernel.md").write_text("Kernel content.")
    (project_path / "outline.md").write_text("Outline content.")

    # Create and populate database
    async with ResearchDB(db_path) as db:
        await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Test claim",
            evidence="Test evidence",
            confidence=0.8,
            tags=["test"],
            workstream="research",
        )

    # Export bundle
    await export_bundle(project_path, db_path)

    # Verify all outputs exist
    export_path = project_path / "exports"
    assert (export_path / "requirements.md").exists()
    assert (export_path / "research.jsonl").exists()
    assert (export_path / "research.csv").exists()

    # Verify requirements content
    requirements_content = (export_path / "requirements.md").read_text()
    assert "Kernel content." in requirements_content
    assert "Outline content." in requirements_content


@pytest.mark.asyncio
async def test_export_bundle_custom_export_path(tmp_path: Path) -> None:
    """Test bundle export with custom export path."""
    project_path = tmp_path / "project"
    project_path.mkdir()
    db_path = tmp_path / "test.db"
    custom_export_path = tmp_path / "custom_exports"

    # Create minimal project
    (project_path / "kernel.md").write_text("Kernel.")

    # Create empty database
    async with ResearchDB(db_path):
        pass

    # Export to custom path
    await export_bundle(project_path, db_path, custom_export_path)

    # Verify outputs in custom location
    assert (custom_export_path / "requirements.md").exists()
    assert (custom_export_path / "research.jsonl").exists()
    assert (custom_export_path / "research.csv").exists()


@pytest.mark.asyncio
async def test_export_idempotency(tmp_path: Path) -> None:
    """Test that re-running export produces identical files."""
    project_path = tmp_path / "project"
    project_path.mkdir()
    db_path = tmp_path / "test.db"
    export_path = tmp_path / "exports"

    # Create project files
    (project_path / "kernel.md").write_text("Kernel content.")
    elements_dir = project_path / "elements"
    elements_dir.mkdir()
    (elements_dir / "requirements.md").write_text("Requirements.")

    # Create and populate database
    async with ResearchDB(db_path) as db:
        await db.insert_finding(
            url="https://example.com",
            source_type="web",
            claim="Claim 1",
            evidence="Evidence 1",
            confidence=0.7,
            tags=["a", "b"],
            workstream="research",
        )
        await db.insert_finding(
            url="https://example.org",
            source_type="paper",
            claim="Claim 2",
            evidence="Evidence 2",
            confidence=0.9,
            tags=["c"],
            workstream="synthesis",
        )

    # First export
    await export_bundle(project_path, db_path, export_path)

    # Read first export
    requirements1 = (export_path / "requirements.md").read_text()
    jsonl1 = (export_path / "research.jsonl").read_text()
    csv1 = (export_path / "research.csv").read_text()

    # Second export
    await export_bundle(project_path, db_path, export_path)

    # Read second export
    requirements2 = (export_path / "requirements.md").read_text()
    jsonl2 = (export_path / "research.jsonl").read_text()
    csv2 = (export_path / "research.csv").read_text()

    # Verify identical
    assert requirements1 == requirements2
    assert jsonl1 == jsonl2
    assert csv1 == csv2
