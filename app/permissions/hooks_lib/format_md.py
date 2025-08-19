"""Markdown formatting utilities for hooks."""

import mdformat


def _format_markdown_text(text: str) -> str:
    """
    Format markdown text using mdformat.

    Args:
        text: Raw markdown text to format

    Returns:
        Formatted markdown text
    """
    return mdformat.text(text)
