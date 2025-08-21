"""Text utility functions for the TUI."""


def truncate_description(text: str, max_length: int = 200) -> str:
    """
    Truncate text to a maximum length with ellipsis.

    Args:
        text: The text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text
