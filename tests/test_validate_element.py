"""Tests for element structure validation."""

from app.files.validate_element import (
    ValidationError,
    auto_fix_element_structure,
    format_validation_errors,
    validate_element_structure,
)


class TestValidateElementStructure:
    """Test element structure validation."""

    def test_valid_document(self) -> None:
        """Test validation of a properly structured document."""
        content = """# UI/UX Workstream

## Decisions
- Use React for the frontend framework
- Implement Material-UI for consistent design

## Requirements
- REQ-1: The application must be responsive
- REQ-2: Support dark mode

## Open Questions
- Q1: Which state management library to use?

## Risks & Mitigations
- R1: Performance issues with large datasets → Implement virtualization

## Acceptance Criteria
- AC-1: Given a user visits the site, When they toggle dark mode, Then the theme should change
- AC-2: Given a mobile device, When the user accesses the app, Then it should be responsive
"""
        errors = validate_element_structure(content)
        assert len(errors) == 0

    def test_missing_section(self) -> None:
        """Test detection of missing required sections."""
        content = """# Workstream

## Decisions
- Some decision

## Requirements
- REQ-1: Some requirement

## Acceptance Criteria
- AC-1: Some criteria
"""
        errors = validate_element_structure(content)
        assert any("Open Questions" in e.message for e in errors)
        assert any("Risks & Mitigations" in e.message for e in errors)

    def test_wrong_section_order(self) -> None:
        """Test detection of incorrect section order."""
        content = """# Workstream

## Requirements
- REQ-1: Some requirement

## Decisions
- Some decision

## Open Questions
- Q1: Some question

## Risks & Mitigations
- R1: Some risk

## Acceptance Criteria
- AC-1: Some criteria
"""
        errors = validate_element_structure(content)
        assert any("order" in e.message.lower() for e in errors)

    def test_missing_ac_prefix(self) -> None:
        """Test detection of acceptance criteria without AC- prefix."""
        content = """# Workstream

## Decisions
- Decision

## Requirements
- REQ-1: Requirement

## Open Questions
- Q1: Question

## Risks & Mitigations
- R1: Risk → Mitigation

## Acceptance Criteria
- Given something, When action, Then result
- Another criteria without prefix
"""
        errors = validate_element_structure(content)
        assert any("AC items" in e.message for e in errors)

    def test_empty_section(self) -> None:
        """Test detection of empty sections."""
        content = """# Workstream

## Decisions

## Requirements
- REQ-1: Some requirement

## Open Questions
- Q1: Question

## Risks & Mitigations
- R1: Risk

## Acceptance Criteria
- AC-1: Criteria
"""
        errors = validate_element_structure(content)
        assert any("no content" in e.message for e in errors)

    def test_duplicate_section(self) -> None:
        """Test detection of duplicate sections."""
        content = """# Workstream

## Decisions
- Decision 1

## Requirements
- REQ-1: Requirement

## Decisions
- Decision 2

## Open Questions
- Q1: Question

## Risks & Mitigations
- R1: Risk

## Acceptance Criteria
- AC-1: Criteria
"""
        errors = validate_element_structure(content)
        assert any("Duplicate" in e.message for e in errors)

    def test_extraneous_section(self) -> None:
        """Test detection of unexpected sections."""
        content = """# Workstream

## Decisions
- Decision

## Requirements
- REQ-1: Requirement

## Random Section
- Some content

## Open Questions
- Q1: Question

## Risks & Mitigations
- R1: Risk

## Acceptance Criteria
- AC-1: Criteria
"""
        errors = validate_element_structure(content)
        assert any("Unexpected section" in e.message for e in errors)


class TestAutoFixElementStructure:
    """Test auto-fix functionality."""

    def test_fix_section_case(self) -> None:
        """Test fixing section heading case."""
        content = """# Workstream

## decisions
- Decision

## REQUIREMENTS
- REQ-1: Requirement

## open questions
- Q1: Question

## risks & mitigations
- R1: Risk

## acceptance criteria
- AC-1: Criteria
"""
        errors = validate_element_structure(content)
        fixed = auto_fix_element_structure(content, errors)

        assert "## Decisions" in fixed
        assert "## Requirements" in fixed
        assert "## Open Questions" in fixed
        assert "## Risks & Mitigations" in fixed
        assert "## Acceptance Criteria" in fixed

    def test_fix_missing_ac_prefix(self) -> None:
        """Test adding AC- prefix to acceptance criteria."""
        content = """# Workstream

## Decisions
- Decision

## Requirements
- REQ-1: Requirement

## Open Questions
- Q1: Question

## Risks & Mitigations
- R1: Risk

## Acceptance Criteria
- Given something, When action, Then result
- Another criteria without prefix
- AC-3: This one already has prefix
"""
        errors = validate_element_structure(content)
        fixed = auto_fix_element_structure(content, errors)

        lines = fixed.split("\n")
        ac_lines = [
            line
            for line in lines
            if line.strip().startswith("- ")
            and "Acceptance Criteria" in "\n".join(lines[: lines.index(line)])
        ]

        # Check that AC prefixes were added
        assert any("AC-1:" in line for line in ac_lines)
        assert any("AC-2:" in line for line in ac_lines)
        assert any("AC-3:" in line for line in ac_lines)


class TestFormatValidationErrors:
    """Test error formatting."""

    def test_no_errors(self) -> None:
        """Test formatting when no errors."""
        result = format_validation_errors([])
        assert "✓" in result
        assert "valid" in result.lower()

    def test_with_errors(self) -> None:
        """Test formatting with errors."""
        errors = [
            ValidationError("Decisions", "Missing section"),
            ValidationError("Requirements", "Empty section", line_number=10),
        ]
        result = format_validation_errors(errors)
        assert "❌" in result
        assert "Missing section" in result
        assert "Line 10" in result
