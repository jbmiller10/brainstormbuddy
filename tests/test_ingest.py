"""Tests for the findings ingest parser."""

from app.research.ingest import Finding, parse_findings


def test_parse_markdown_bullets_basic() -> None:
    """Test parsing basic markdown bullet format."""
    text = """
    - AI improves efficiency | Studies show 40% improvement | https://example.com/ai | 0.85
    - ML needs data | Large datasets required | https://ml.org/data | 0.9
    """

    findings = parse_findings(text, "research")

    assert len(findings) == 2
    assert findings[0].claim == "AI improves efficiency"
    assert findings[0].evidence == "Studies show 40% improvement"
    assert findings[0].url == "https://example.com/ai"
    assert findings[0].confidence == 0.85
    assert findings[0].workstream == "research"
    assert findings[0].source_type == "web"
    assert findings[0].tags == []

    assert findings[1].claim == "ML needs data"
    assert findings[1].confidence == 0.9


def test_parse_markdown_bullets_with_tags() -> None:
    """Test parsing markdown bullets with tags."""
    text = """
    * Deep learning breakthrough | New architecture discovered | https://arxiv.org/123 | 0.95 | neural, architecture
    - Python dominates ML | 80% of projects use Python | https://survey.com | 0.8 | python, ml, stats
    """

    findings = parse_findings(text, "default")

    assert len(findings) == 2
    assert findings[0].tags == ["neural", "architecture"]
    assert findings[0].source_type == "paper"  # arxiv URL auto-detected
    assert findings[1].tags == ["python", "ml", "stats"]


def test_parse_markdown_bullets_with_source_type() -> None:
    """Test parsing markdown bullets with explicit source type."""
    text = """
    - Quantum computing advances | New qubit design | https://example.com | 0.7 | quantum, computing | paper
    + Blockchain use cases | Financial applications growing | https://chain.io | 0.6 | blockchain | report
    """

    findings = parse_findings(text, "tech")

    assert len(findings) == 2
    assert findings[0].source_type == "paper"
    assert findings[1].source_type == "report"
    assert findings[1].workstream == "tech"


def test_parse_json_array_basic() -> None:
    """Test parsing JSON array format."""
    text = """[
        {
            "claim": "AI safety is critical",
            "evidence": "Alignment research shows risks",
            "url": "https://safety.ai",
            "confidence": 0.92
        },
        {
            "claim": "GPUs accelerate training",
            "evidence": "10x faster than CPUs",
            "url": "https://nvidia.com/research",
            "confidence": 0.88,
            "tags": ["gpu", "performance"],
            "source_type": "whitepaper"
        }
    ]"""

    findings = parse_findings(text, "ai-safety")

    assert len(findings) == 2
    assert findings[0].claim == "AI safety is critical"
    assert findings[0].confidence == 0.92
    assert findings[0].workstream == "ai-safety"
    assert findings[0].source_type == "web"

    assert findings[1].tags == ["gpu", "performance"]
    assert findings[1].source_type == "whitepaper"


def test_parse_json_with_workstream() -> None:
    """Test JSON parsing with explicit workstream."""
    text = """[
        {
            "claim": "Test claim",
            "evidence": "Test evidence",
            "url": "https://test.com",
            "confidence": 0.5,
            "workstream": "custom-stream"
        }
    ]"""

    findings = parse_findings(text, "default")

    assert len(findings) == 1
    assert findings[0].workstream == "custom-stream"  # Uses explicit value, not default


def test_deduplication_by_claim_and_url() -> None:
    """Test deduplication keeps highest confidence for same (claim, url)."""
    text = """
    - First claim | Evidence A | https://same.url | 0.6
    - FIRST CLAIM | Evidence B | https://same.url | 0.8
    - first claim | Evidence C | https://same.url | 0.7
    - First claim | Different evidence | https://different.url | 0.9
    """

    findings = parse_findings(text, "test")

    # Should have 2 findings: one for same.url (highest conf=0.8) and one for different.url
    assert len(findings) == 2

    # Find the one with same.url
    same_url_finding = next(f for f in findings if f.url == "https://same.url")
    assert same_url_finding.confidence == 0.8  # Highest confidence kept
    assert same_url_finding.evidence == "Evidence B"  # From the 0.8 confidence entry

    # Find the one with different.url
    diff_url_finding = next(f for f in findings if f.url == "https://different.url")
    assert diff_url_finding.confidence == 0.9


def test_confidence_clamping() -> None:
    """Test that confidence values are clamped to [0, 1] range."""
    text = """[
        {
            "claim": "Over confident",
            "evidence": "Too high",
            "url": "https://high.com",
            "confidence": 1.5
        },
        {
            "claim": "Under confident",
            "evidence": "Too low",
            "url": "https://low.com",
            "confidence": -0.3
        }
    ]"""

    findings = parse_findings(text, "test")

    assert len(findings) == 2
    assert findings[0].confidence == 1.0  # Clamped from 1.5
    assert findings[1].confidence == 0.0  # Clamped from -0.3


def test_empty_input() -> None:
    """Test handling of empty input."""
    assert parse_findings("", "test") == []
    assert parse_findings("   \n  \n  ", "test") == []
    assert parse_findings("[]", "test") == []


def test_invalid_json() -> None:
    """Test that invalid JSON falls back to markdown parsing."""
    text = """[{invalid json}
    - Valid markdown | With evidence | https://url.com | 0.5
    """

    findings = parse_findings(text, "test")

    assert len(findings) == 1
    assert findings[0].claim == "Valid markdown"


def test_mixed_bullet_styles() -> None:
    """Test that different bullet markers work."""
    text = """
    - Dash bullet | Evidence | https://url1.com | 0.5
    * Asterisk bullet | Evidence | https://url2.com | 0.6
    + Plus bullet | Evidence | https://url3.com | 0.7
    """

    findings = parse_findings(text, "test")

    assert len(findings) == 3
    assert findings[0].url == "https://url1.com"
    assert findings[1].url == "https://url2.com"
    assert findings[2].url == "https://url3.com"


def test_malformed_markdown_lines() -> None:
    """Test handling of malformed markdown lines."""
    text = """
    - Valid line | Evidence | https://valid.com | 0.8
    - Missing confidence | Evidence | https://invalid.com
    - | | | 0.5
    - Only claim provided
    Not a bullet line
    - Another valid | More evidence | https://valid2.com | 0.7
    """

    findings = parse_findings(text, "test")

    # Only the valid lines should be parsed
    assert len(findings) == 2
    assert findings[0].url == "https://valid.com"
    assert findings[1].url == "https://valid2.com"


def test_json_missing_required_fields() -> None:
    """Test JSON objects missing required fields are skipped."""
    text = """[
        {
            "claim": "Valid finding",
            "evidence": "Good evidence",
            "url": "https://valid.com",
            "confidence": 0.8
        },
        {
            "claim": "Missing URL",
            "evidence": "Some evidence",
            "confidence": 0.5
        },
        {
            "url": "https://noevidence.com",
            "confidence": 0.6
        },
        {
            "claim": "Another valid",
            "evidence": "More evidence",
            "url": "https://valid2.com",
            "confidence": 0.9
        }
    ]"""

    findings = parse_findings(text, "test")

    # Only entries with all required fields should be parsed
    assert len(findings) == 2
    assert findings[0].url == "https://valid.com"
    assert findings[1].url == "https://valid2.com"


def test_tags_parsing_variations() -> None:
    """Test different ways tags can be specified."""
    text = """[
        {
            "claim": "Array tags",
            "evidence": "Evidence",
            "url": "https://url1.com",
            "confidence": 0.5,
            "tags": ["tag1", "tag2"]
        },
        {
            "claim": "String tags",
            "evidence": "Evidence",
            "url": "https://url2.com",
            "confidence": 0.6,
            "tags": "tag3, tag4, tag5"
        }
    ]"""

    findings = parse_findings(text, "test")

    assert len(findings) == 2
    assert findings[0].tags == ["tag1", "tag2"]
    assert findings[1].tags == ["tag3", "tag4", "tag5"]


def test_arxiv_url_detection() -> None:
    """Test that arxiv URLs are automatically classified as papers."""
    text = """
    - ArXiv paper | Research findings | https://arxiv.org/abs/2301.12345 | 0.9
    - Another source | More findings | https://ARXIV.org/pdf/2301.54321.pdf | 0.85
    """

    findings = parse_findings(text, "research")

    assert len(findings) == 2
    assert findings[0].source_type == "paper"
    assert findings[1].source_type == "paper"


def test_whitespace_normalization() -> None:
    """Test that claims are normalized for deduplication."""
    text = """
    -   Claim with spaces   | Evidence | https://url.com | 0.7
    - claim WITH spaces | Different | https://url.com | 0.8
    """

    findings = parse_findings(text, "test")

    # Should dedupe to one finding with highest confidence
    assert len(findings) == 1
    assert findings[0].confidence == 0.8


def test_empty_tags_field() -> None:
    """Test handling of empty tags in various formats."""
    text = """
    - Claim | Evidence | https://url1.com | 0.5 |  | web
    - Claim2 | Evidence | https://url2.com | 0.6 | , , | paper
    """

    findings = parse_findings(text, "test")

    assert len(findings) == 2
    assert findings[0].tags == []
    assert findings[1].tags == []


def test_finding_dataclass() -> None:
    """Test the Finding dataclass directly."""
    finding = Finding(
        url="https://test.com",
        source_type="web",
        claim="Test claim",
        evidence="Test evidence",
        confidence=0.75,
    )

    assert finding.url == "https://test.com"
    assert finding.source_type == "web"
    assert finding.claim == "Test claim"
    assert finding.evidence == "Test evidence"
    assert finding.confidence == 0.75
    assert finding.tags == []  # Default value
    assert finding.workstream is None  # Default value

    # With all fields
    finding2 = Finding(
        url="https://test2.com",
        source_type="paper",
        claim="Another claim",
        evidence="More evidence",
        confidence=0.9,
        tags=["ai", "ml"],
        workstream="research",
    )

    assert finding2.tags == ["ai", "ml"]
    assert finding2.workstream == "research"
