"""Markdown parsing and extraction utilities."""

import re


def extract_section_paragraph(md: str, header: str = "## Core Concept") -> str | None:
    """
    Extract the first non-empty paragraph after a specific header.

    Finds the specified header (case-insensitive, trimmed) and returns the first
    non-empty paragraph content following it. Stops at the next header of same
    or higher level. Strips markdown emphasis markers.

    Args:
        md: The markdown content to parse
        header: The header to search for (e.g., "## Core Concept")

    Returns:
        The first non-empty paragraph after the header with emphasis stripped,
        or None if the section is not found or has no content.

    Examples:
        >>> md = '''
        ... ## Core Concept
        ... *A revolutionary approach to task management*
        ...
        ... ## Other Section
        ... '''
        >>> extract_section_paragraph(md)
        'A revolutionary approach to task management'

        >>> md = '''
        ... ## CORE CONCEPT
        ... First paragraph here.
        ... '''
        >>> extract_section_paragraph(md)
        'First paragraph here.'
    """
    if not md or not header:
        return None

    # Parse header level from the header string (count # symbols)
    header_level = len(header) - len(header.lstrip("#"))
    if header_level == 0:
        return None

    # Clean header text for comparison
    header_text = header.lstrip("#").strip().lower()

    lines = md.split("\n")
    header_found = False
    content_lines: list[str] = []
    in_code_fence = False

    for _i, line in enumerate(lines):
        stripped = line.strip()

        # Check if this is our target header (case-insensitive)
        if not header_found:
            if stripped.startswith("#"):
                # Extract level and text from current line
                current_level = len(stripped) - len(stripped.lstrip("#"))
                current_text = stripped.lstrip("#").strip().lower()

                if current_level == header_level and current_text == header_text:
                    header_found = True
            continue

        # We've found the header, now collect content
        # Check for code fence markers (``` or ~~~)
        if stripped.startswith(("```", "~~~")):
            # If we already have prose content, stop extraction before the fence
            if content_lines:
                break
            # Otherwise, toggle the code fence flag to skip the code block
            in_code_fence = not in_code_fence
            continue

        # Skip lines inside code fences
        if in_code_fence:
            continue

        # Check if we've hit another header of same or higher level
        if stripped.startswith("#"):
            current_level = len(stripped) - len(stripped.lstrip("#"))
            if current_level <= header_level:
                # Stop - we've reached the next section
                break

        # Skip empty lines at the beginning
        if not stripped and not content_lines:
            continue

        # If we have content and hit an empty line, consider paragraph complete
        if not stripped and content_lines:
            break

        # Add non-empty line to content
        if stripped:
            content_lines.append(stripped)

    if not content_lines:
        return None

    # Join lines and strip markdown emphasis
    paragraph = " ".join(content_lines)

    # Remove bold markers (**text** or __text__)
    paragraph = re.sub(r"\*\*(.+?)\*\*", r"\1", paragraph)
    paragraph = re.sub(r"__(.+?)__", r"\1", paragraph)

    # Remove italic markers (*text* or _text_)
    # Be careful not to remove standalone asterisks (e.g., bullet points)
    paragraph = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", paragraph)
    paragraph = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"\1", paragraph)

    return paragraph.strip()
