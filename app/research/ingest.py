"""Parser for ingesting findings from markdown or JSON formats."""

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Finding:
    """Represents a research finding with metadata."""

    url: str
    source_type: str
    claim: str
    evidence: str
    confidence: float
    tags: list[str] = field(default_factory=list)
    workstream: str | None = None


def _normalize_claim(claim: str) -> str:
    """Normalize a claim for deduplication by lowercasing and stripping whitespace."""
    return claim.lower().strip()


def _clamp_confidence(value: float) -> float:
    """Clamp confidence value to [0, 1] range."""
    return max(0.0, min(1.0, value))


def _parse_markdown_bullet(line: str) -> dict[str, Any] | None:
    """Parse a single markdown bullet line into finding fields.

    Expected format variations:
    - claim | evidence | url | confidence
    - claim | evidence | url | confidence | tags
    - claim | evidence | url | confidence | tags | source_type
    """
    # Remove bullet marker (-, *, or +) and leading/trailing whitespace
    line = re.sub(r"^[-*+]\s*", "", line).strip()
    if not line:
        return None

    # Split by pipe separator
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 4:
        return None  # Need at least claim, evidence, url, confidence

    try:
        # Check that claim and evidence are not empty
        if not parts[0].strip() or not parts[1].strip():
            return None

        finding_dict = {
            "claim": parts[0],
            "evidence": parts[1],
            "url": parts[2],
            "confidence": float(parts[3]),
        }

        # Optional tags field (5th position)
        if len(parts) > 4 and parts[4]:
            # Parse comma-separated tags
            finding_dict["tags"] = [t.strip() for t in parts[4].split(",") if t.strip()]

        # Optional source_type field (6th position)
        if len(parts) > 5 and parts[5]:
            finding_dict["source_type"] = parts[5]
        else:
            # Default source type based on URL
            url_str = str(finding_dict["url"]).lower()
            if "arxiv" in url_str:
                finding_dict["source_type"] = "paper"
            else:
                finding_dict["source_type"] = "web"

        return finding_dict
    except (ValueError, IndexError):
        return None


def _parse_json_finding(obj: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a JSON object into finding fields."""
    # Required fields
    required_fields = {"claim", "evidence", "url", "confidence"}
    if not all(field in obj for field in required_fields):
        return None

    try:
        finding_dict = {
            "claim": str(obj["claim"]),
            "evidence": str(obj["evidence"]),
            "url": str(obj["url"]),
            "confidence": float(obj["confidence"]),
        }

        # Optional fields
        if "tags" in obj:
            tags = obj["tags"]
            if isinstance(tags, list):
                finding_dict["tags"] = [str(t) for t in tags]
            elif isinstance(tags, str):
                finding_dict["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

        if "source_type" in obj:
            finding_dict["source_type"] = str(obj["source_type"])
        else:
            # Default source type
            url_str = str(finding_dict["url"]).lower()
            if "arxiv" in url_str:
                finding_dict["source_type"] = "paper"
            else:
                finding_dict["source_type"] = "web"

        if "workstream" in obj:
            finding_dict["workstream"] = str(obj["workstream"])

        return finding_dict
    except (ValueError, KeyError, TypeError):
        return None


def parse_findings(text: str, default_workstream: str) -> list[Finding]:
    """Parse findings from markdown bullets or JSON array format.

    Args:
        text: Input text containing findings in markdown or JSON format
        default_workstream: Default workstream to assign if not specified

    Returns:
        List of Finding objects with duplicates removed (keeping highest confidence)
    """
    findings_data: list[dict[str, Any]] = []

    # Try parsing as JSON first
    text = text.strip()
    if text.startswith("["):
        try:
            json_data = json.loads(text)
            if isinstance(json_data, list):
                for item in json_data:
                    if isinstance(item, dict):
                        parsed = _parse_json_finding(item)
                        if parsed:
                            findings_data.append(parsed)
        except json.JSONDecodeError:
            pass  # Fall through to markdown parsing

    # If not JSON or no findings from JSON, try markdown bullet parsing
    if not findings_data:
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            # Check if line starts with a bullet marker
            if re.match(r"^[-*+]\s+", line):
                parsed = _parse_markdown_bullet(line)
                if parsed:
                    findings_data.append(parsed)

    # Apply default workstream and create Finding objects
    findings: list[Finding] = []
    for data in findings_data:
        if "workstream" not in data or not data["workstream"]:
            data["workstream"] = default_workstream

        # Ensure confidence is in valid range
        data["confidence"] = _clamp_confidence(data["confidence"])

        # Create Finding object
        findings.append(Finding(**data))

    # Deduplicate by (normalized_claim, url), keeping highest confidence
    dedupe_map: dict[tuple[str, str], Finding] = {}
    for finding in findings:
        key = (_normalize_claim(finding.claim), finding.url)
        if key not in dedupe_map or finding.confidence > dedupe_map[key].confidence:
            dedupe_map[key] = finding

    return list(dedupe_map.values())
