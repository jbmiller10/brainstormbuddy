"""Additional tests for validate_element to improve coverage."""

from app.files.validate_element import (
    ValidationError,
    ValidationLevel,
    format_validation_errors,
    validate_element_structure,
)


class TestValidateElementAdditionalCoverage:
    """Additional tests for validate_element coverage."""

    def test_requirements_with_mixed_prefixes(self) -> None:
        """Test validation when some requirements have REQ- prefix and some don't."""
        content = """# Workstream

## Decisions
- Decision 1

## Requirements
- REQ-1: First requirement with prefix
- Regular requirement without prefix
- Another requirement without prefix
- REQ-2: Second requirement with prefix

## Open Questions
- Q1: Question

## Risks & Mitigations
- Risk 1

## Acceptance Criteria
- AC-1: Valid criteria with enough content
"""
        errors = validate_element_structure(content)

        # Should have INFO level suggestions for non-REQ items
        info_errors = [e for e in errors if e.level == ValidationLevel.INFO]
        assert len(info_errors) >= 2  # At least 2 non-REQ items
        assert all("REQ- prefix for consistency" in e.message for e in info_errors)
        assert all(e.section == "Requirements" for e in info_errors)

    def test_requirements_all_without_prefix(self) -> None:
        """Test validation when no requirements have REQ- prefix."""
        content = """# Workstream

## Decisions
- Decision 1

## Requirements
- First requirement without prefix
- Second requirement without prefix
- Third requirement without prefix

## Open Questions
- Q1: Question

## Risks & Mitigations
- Risk 1

## Acceptance Criteria
- AC-1: Valid criteria with enough content
"""
        errors = validate_element_structure(content)

        # Should have one INFO level suggestion about REQ- prefix
        info_errors = [e for e in errors if e.level == ValidationLevel.INFO]
        req_info = [e for e in info_errors if e.section == "Requirements"]
        assert len(req_info) == 1
        assert "Consider using REQ- prefix" in req_info[0].message

    def test_format_validation_errors_with_warnings_only(self) -> None:
        """Test formatting when only warnings exist."""
        errors = [
            ValidationError(
                section="Test",
                message="Warning message",
                line_number=5,
                level=ValidationLevel.WARNING,
            ),
            ValidationError(
                section="Test2",
                message="Another warning",
                level=ValidationLevel.WARNING,
            ),
        ]

        formatted = format_validation_errors(errors)
        assert "⚠️  Document has 2 warnings" in formatted
        assert "Warnings:" in formatted
        assert "Line 5: Warning message" in formatted
        assert "Test2: Another warning" in formatted

    def test_format_validation_errors_with_info_only(self) -> None:
        """Test formatting when only info level issues exist."""
        errors = [
            ValidationError(
                section="Test",
                message="Info message",
                level=ValidationLevel.INFO,
            ),
        ]

        formatted = format_validation_errors(errors)
        assert "ℹ️  Document has 1 suggestions for improvement" in formatted
        assert "Suggestions:" in formatted
        assert "Test: Info message" in formatted

    def test_format_validation_errors_mixed_levels(self) -> None:
        """Test formatting with mixed error levels."""
        errors = [
            ValidationError(
                section="Critical",
                message="Error message",
                line_number=1,
                level=ValidationLevel.ERROR,
            ),
            ValidationError(
                section="Warning",
                message="Warning message",
                line_number=2,
                level=ValidationLevel.WARNING,
            ),
            ValidationError(
                section="Info",
                message="Info message",
                line_number=3,
                level=ValidationLevel.INFO,
            ),
        ]

        formatted = format_validation_errors(errors)
        assert "❌ Document validation failed: 1 errors, 1 warnings, 1 suggestions" in formatted
        assert "Errors:" in formatted
        assert "Warnings:" in formatted
        assert "Suggestions:" in formatted
        assert "Line 1: Error message" in formatted
        assert "Line 2: Warning message" in formatted
        assert "Line 3: Info message" in formatted

    def test_acceptance_criteria_with_action_verbs(self) -> None:
        """Test AC validation with various action verbs."""
        content = """# Workstream

## Decisions
- Decision 1

## Requirements
- REQ-1: Requirement

## Open Questions
- Q1: Question

## Risks & Mitigations
- Risk 1

## Acceptance Criteria
- AC-1: System should handle errors gracefully
- AC-2: User must authenticate before access
- AC-3: Application will log all transactions
- AC-4: Tests can verify the implementation
- AC-5: Code should ensure data integrity
- AC-6: We verify that the system works
"""
        errors = validate_element_structure(content)

        # All ACs have action verbs, so no warnings about testability
        warning_errors = [
            e
            for e in errors
            if e.level == ValidationLevel.WARNING and "may not be testable" in e.message
        ]
        assert len(warning_errors) == 0

    def test_requirements_with_more_than_three_non_req_items(self) -> None:
        """Test that only first 3 non-REQ items get individual suggestions."""
        content = """# Workstream

## Decisions
- Decision 1

## Requirements
- REQ-1: First requirement with prefix
- Item 1 without prefix
- Item 2 without prefix
- Item 3 without prefix
- Item 4 without prefix
- Item 5 without prefix

## Open Questions
- Q1: Question

## Risks & Mitigations
- Risk 1

## Acceptance Criteria
- AC-1: Valid criteria with enough content
"""
        errors = validate_element_structure(content)

        # Should have exactly 3 INFO suggestions for consistency (limited to first 3)
        info_errors = [
            e for e in errors if e.level == ValidationLevel.INFO and "consistency" in e.message
        ]
        assert len(info_errors) == 3  # Only first 3 get individual messages
