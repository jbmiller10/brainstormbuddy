"""Export functionality for bundling project requirements and research data."""

import csv
import json
from io import StringIO
from pathlib import Path

from app.files.atomic import atomic_write_text
from app.research.db import ResearchDB


async def export_requirements(project_path: Path, export_path: Path) -> None:
    """
    Export concatenated requirements document.

    Concatenates kernel.md + outline.md + elements/*.md in stable alphabetical order.

    Args:
        project_path: Path to the project directory
        export_path: Path to the exports directory
    """
    requirements_parts = []

    # Read kernel.md if exists
    kernel_path = project_path / "kernel.md"
    if kernel_path.exists():
        with open(kernel_path, encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                requirements_parts.append("# Kernel\n\n" + content)

    # Read outline.md if exists
    outline_path = project_path / "outline.md"
    if outline_path.exists():
        with open(outline_path, encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                requirements_parts.append("# Outline\n\n" + content)

    # Read element files in alphabetical order
    elements_dir = project_path / "elements"
    if elements_dir.exists() and elements_dir.is_dir():
        element_files = sorted(elements_dir.glob("*.md"))
        for element_file in element_files:
            with open(element_file, encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    element_name = element_file.stem.title()
                    requirements_parts.append(f"# {element_name}\n\n" + content)

    # Join all parts with double newlines
    requirements_content = "\n\n---\n\n".join(requirements_parts)

    # Ensure export directory exists
    export_path.mkdir(parents=True, exist_ok=True)

    # Write requirements.md atomically
    requirements_file = export_path / "requirements.md"
    atomic_write_text(requirements_file, requirements_content)


async def export_research_jsonl(db_path: Path, export_path: Path) -> None:
    """
    Export research findings to JSONL format.

    Args:
        db_path: Path to the SQLite database
        export_path: Path to the exports directory
    """
    # Ensure export directory exists
    export_path.mkdir(parents=True, exist_ok=True)

    findings_lines = []

    # Query all findings from database
    async with ResearchDB(db_path) as db:
        findings = await db.list_findings(limit=10000)  # Get all findings

        for finding in findings:
            # Convert to JSON and add newline
            json_line = json.dumps(finding, ensure_ascii=False, separators=(",", ":"))
            findings_lines.append(json_line)

    # Join with newlines
    jsonl_content = "\n".join(findings_lines)

    # Write research.jsonl atomically
    jsonl_file = export_path / "research.jsonl"
    atomic_write_text(jsonl_file, jsonl_content)


async def export_research_csv(db_path: Path, export_path: Path) -> None:
    """
    Export research findings to CSV format.

    Args:
        db_path: Path to the SQLite database
        export_path: Path to the exports directory
    """
    # Ensure export directory exists
    export_path.mkdir(parents=True, exist_ok=True)

    # CSV headers matching the database schema
    headers = [
        "id",
        "url",
        "source_type",
        "claim",
        "evidence",
        "confidence",
        "tags",
        "workstream",
        "retrieved_at",
    ]

    # Use StringIO to build CSV in memory
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=headers)
    writer.writeheader()

    # Query all findings from database
    async with ResearchDB(db_path) as db:
        findings = await db.list_findings(limit=10000)  # Get all findings

        for finding in findings:
            # Convert tags list to JSON string for CSV
            if isinstance(finding.get("tags"), list):
                finding["tags"] = json.dumps(finding["tags"])
            writer.writerow(finding)

    # Get CSV content
    csv_content = csv_buffer.getvalue()

    # Write research.csv atomically
    csv_file = export_path / "research.csv"
    atomic_write_text(csv_file, csv_content)


async def export_bundle(project_path: Path, db_path: Path, export_path: Path | None = None) -> None:
    """
    Export complete bundle with requirements and research data.

    Produces exports/requirements.md and exports/research.{jsonl,csv} atomically.

    Args:
        project_path: Path to the project directory
        db_path: Path to the SQLite database
        export_path: Optional path to exports directory (defaults to project_path/exports)
    """
    if export_path is None:
        export_path = project_path / "exports"

    # Export all components
    await export_requirements(project_path, export_path)
    await export_research_jsonl(db_path, export_path)
    await export_research_csv(db_path, export_path)
