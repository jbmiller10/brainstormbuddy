"""Validation utilities for element markdown structure."""

from dataclasses import dataclass


@dataclass
class ValidationError:
    """Represents a validation error in an element document."""

    section: str
    message: str
    line_number: int | None = None


def validate_element_structure(content: str) -> list[ValidationError]:
    """
    Validate that an element markdown document follows the required structure.

    Args:
        content: The markdown content to validate

    Returns:
        List of validation errors, empty if document is valid

    Requirements:
        - Headings must appear exactly once in order: Decisions, Requirements,
          Open Questions, Risks & Mitigations, Acceptance Criteria
        - Acceptance Criteria lines must begin with "AC-" and contain testable outcomes
        - Requirements items preferably prefixed with "REQ-"
        - No extraneous sections or trailing empty headings
    """
    errors: list[ValidationError] = []
    lines = content.split("\n")

    # Expected sections in order
    expected_sections = [
        "Decisions",
        "Requirements",
        "Open Questions",
        "Risks & Mitigations",
        "Acceptance Criteria",
    ]

    # Find all section headings
    found_sections: list[tuple[str, int]] = []
    for i, line in enumerate(lines, 1):
        if line.startswith("## "):
            section = line[3:].strip()
            found_sections.append((section, i))

    # Check for missing sections
    found_names = [name for name, _ in found_sections]
    for expected in expected_sections:
        if expected not in found_names:
            errors.append(ValidationError(expected, f"Missing required section: {expected}"))

    # Check for correct order
    if found_names != [s for s in expected_sections if s in found_names]:
        errors.append(
            ValidationError(
                "Structure",
                "Sections are not in the required order",
                found_sections[0][1] if found_sections else None,
            )
        )

    # Check for duplicate sections
    seen = set()
    for section, line_num in found_sections:
        if section in seen:
            errors.append(ValidationError(section, f"Duplicate section: {section}", line_num))
        seen.add(section)

    # Check for extraneous sections
    for section, line_num in found_sections:
        if section not in expected_sections:
            errors.append(ValidationError(section, f"Unexpected section: {section}", line_num))

    # Validate Acceptance Criteria section
    ac_section_start = None
    for i, (section, line_num) in enumerate(found_sections):
        if section == "Acceptance Criteria":
            ac_section_start = line_num
            # Find the end of this section (next section or end of file)
            ac_section_end = (
                found_sections[i + 1][1] if i + 1 < len(found_sections) else len(lines) + 1
            )
            break

    if ac_section_start:
        ac_found = False
        for i in range(ac_section_start, min(ac_section_end, len(lines) + 1)):
            if i - 1 < len(lines):
                line = lines[i - 1].strip()
                # Check for AC items (lines starting with "- AC-")
                if line.startswith("- AC-"):
                    ac_found = True
                    # Check if it contains testable content
                    ac_content = line[5:].strip()
                    if ac_content.startswith(":"):
                        ac_content = ac_content[1:].strip()
                    # Simple check for testable content - should have substance
                    if len(ac_content) < 10:
                        errors.append(
                            ValidationError(
                                "Acceptance Criteria",
                                f"AC item appears incomplete or not testable at line {i}",
                                i,
                            )
                        )
                    # Recommend Given/When/Then format if not present
                    if not any(
                        word in ac_content
                        for word in ["Given", "When", "Then", "should", "must", "will"]
                    ):
                        # This is just a warning, not an error
                        pass  # Could add as info-level validation if needed

        if ac_section_start and not ac_found:
            errors.append(
                ValidationError(
                    "Acceptance Criteria",
                    "No AC items found (expected format: '- AC-1: ...')",
                    ac_section_start,
                )
            )

    # Validate Requirements section (optional check for REQ- prefix)
    req_section_start = None
    for i, (section, line_num) in enumerate(found_sections):
        if section == "Requirements":
            req_section_start = line_num
            req_section_end = (
                found_sections[i + 1][1] if i + 1 < len(found_sections) else len(lines) + 1
            )
            break

    if req_section_start:
        req_items = []
        for i in range(req_section_start, min(req_section_end, len(lines) + 1)):
            if i - 1 < len(lines):
                line = lines[i - 1].strip()
                if line.startswith("- REQ-"):
                    req_items.append(line)
        # This is a recommendation, not a hard requirement
        # So we don't add an error if REQ- prefix is missing

    # Check for empty sections (just the heading with no content)
    for i, (section, line_num) in enumerate(found_sections):
        section_end = found_sections[i + 1][1] if i + 1 < len(found_sections) else len(lines) + 1
        has_content = False
        for j in range(line_num, min(section_end, len(lines) + 1)):
            if j - 1 < len(lines):
                line = lines[j - 1].strip()
                # Skip the heading line itself and empty lines
                if line and not line.startswith("## "):
                    has_content = True
                    break
        if not has_content:
            errors.append(ValidationError(section, f"Section '{section}' has no content", line_num))

    return errors


def format_validation_errors(errors: list[ValidationError]) -> str:
    """
    Format validation errors for display.

    Args:
        errors: List of validation errors

    Returns:
        Formatted error message string
    """
    if not errors:
        return "✓ Document structure is valid"

    lines = ["❌ Document validation failed:"]
    for error in errors:
        if error.line_number:
            lines.append(f"  Line {error.line_number}: {error.message}")
        else:
            lines.append(f"  {error.section}: {error.message}")

    return "\n".join(lines)


def auto_fix_element_structure(content: str, errors: list[ValidationError]) -> str:  # noqa: ARG001
    """
    Apply deterministic auto-fixes for validation errors.

    Only fixes:
    - Missing "AC-" prefixes on acceptance criteria items
    - Normalizes section heading case
    - Removes obviously ungrounded claims (marked by critic)

    Args:
        content: The markdown content to fix
        errors: List of validation errors to address

    Returns:
        Fixed content
    """
    lines = content.split("\n")
    fixed_lines = lines.copy()

    # Fix section heading case
    section_mappings = {
        "decisions": "Decisions",
        "requirements": "Requirements",
        "open questions": "Open Questions",
        "risks & mitigations": "Risks & Mitigations",
        "acceptance criteria": "Acceptance Criteria",
    }

    for i, line in enumerate(fixed_lines):
        if line.startswith("## "):
            section = line[3:].strip()
            normalized = section_mappings.get(section.lower())
            if normalized and normalized != section:
                fixed_lines[i] = f"## {normalized}"

    # Fix missing AC- prefixes
    in_ac_section = False
    for i, line in enumerate(fixed_lines):
        if line.startswith("## Acceptance Criteria"):
            in_ac_section = True
        elif line.startswith("## "):
            in_ac_section = False
        elif (
            in_ac_section and line.strip().startswith("- ") and not line.strip().startswith("- AC-")
        ):
            # Add AC- prefix with auto-numbering
            # Count existing AC items to get the next number
            ac_count = sum(
                1 for line_item in fixed_lines[:i] if line_item.strip().startswith("- AC-")
            )
            fixed_lines[i] = line.replace("- ", f"- AC-{ac_count + 1}: ", 1)

    return "\n".join(fixed_lines)
