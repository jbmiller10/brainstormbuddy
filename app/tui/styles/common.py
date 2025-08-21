"""Common CSS styles for TUI components."""

# Container styles
CONTAINER_STYLES = """
    .container {
        width: 90%;
        height: 90%;
        max-width: 120;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }

    .container-medium {
        width: 80%;
        height: 80%;
        max-width: 100;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }
"""

# Title and text styles
TITLE_STYLES = """
    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    .instructions {
        margin-bottom: 1;
        color: $text;
    }

    .step-indicator {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }
"""

# Button styles
BUTTON_STYLES = """
    .button-container {
        height: 3;
        align: center middle;
    }

    Button {
        width: 16;
        margin: 0 1;
    }

    .next-button, .create-button, .accept-button {
        background: $success;
    }

    .back-button, .reject-button {
        background: $warning;
    }

    .cancel-button {
        background: $error;
    }
"""

# Content area styles
CONTENT_STYLES = """
    .content-area {
        height: 1fr;
        margin-bottom: 2;
        padding: 1;
    }

    .project-list {
        height: 1fr;
        margin-bottom: 2;
        border: solid $primary;
    }

    .diff-container, .questions-container {
        padding: 1;
        border: solid $primary;
        background: $panel;
    }
"""

# Empty state styles
EMPTY_STATE_STYLES = """
    .empty-state {
        align: center middle;
        height: 100%;
        color: $text-muted;
        text-align: center;
    }
"""

# Input styles
INPUT_STYLES = """
    Input {
        width: 100%;
        margin-bottom: 1;
    }

    TextArea {
        width: 100%;
        height: 100%;
    }
"""

# List item styles
LIST_STYLES = """
    .question-item {
        margin-bottom: 1;
        padding: 0 1;
    }
"""


def get_common_css(screen_name: str, center_align: bool = True) -> str:
    """
    Get common CSS for a screen with the specified name.

    Args:
        screen_name: Name of the screen class
        center_align: Whether to center align the screen

    Returns:
        Complete CSS string with common styles
    """
    align_style = "align: center middle;" if center_align else ""

    return f"""
    {screen_name} {{
        {align_style}
    }}

    {screen_name} {CONTAINER_STYLES}
    {screen_name} {TITLE_STYLES}
    {screen_name} {BUTTON_STYLES}
    {screen_name} {CONTENT_STYLES}
    {screen_name} {EMPTY_STATE_STYLES}
    {screen_name} {INPUT_STYLES}
    {screen_name} {LIST_STYLES}
    """


def get_modal_css(modal_name: str) -> str:
    """
    Get common CSS for a modal with the specified name.

    Args:
        modal_name: Name of the modal class

    Returns:
        Complete CSS string with modal styles
    """
    return f"""
    {modal_name} {{
        align: center middle;
    }}

    {modal_name} > Container {{
        background: $surface;
        width: 90%;
        height: 80%;
        border: thick $primary;
        padding: 1;
    }}

    {modal_name} .diff-container {{
        height: 1fr;
        margin-bottom: 1;
        border: solid $primary;
        padding: 1;
    }}

    {modal_name} {BUTTON_STYLES}
    """
