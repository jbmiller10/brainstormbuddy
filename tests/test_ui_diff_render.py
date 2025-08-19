"""Tests for UI diff rendering without Rich markup interpretation."""

from app.tui.widgets.kernel_approval import KernelApprovalModal


def test_kernel_approval_modal_diff_renders_without_markup() -> None:
    """Test that diff content in KernelApprovalModal renders literally without markup."""
    # Create diff content with Rich markup characters that should render literally
    diff_content = """--- kernel.md (current)
+++ kernel.md (proposed)
@@ -1,5 +1,7 @@
 ## Core Concept
-The old [red]concept[/red] here.
+The new [green]concept[/green] with improvements.
+Added `backticks` for code.

 ## Key Questions
-1. Question with {brackets}
+1. Question with [bold]emphasis[/bold]
+2. Code example: `print("hello")`
"""

    modal = KernelApprovalModal(diff_content, "test-project")

    # We can't compose without an app context, so let's check the compose method directly
    # by examining the code statically
    import inspect

    compose_source = inspect.getsource(modal.compose)

    # Verify that markup=False is set in the compose method
    assert (
        "markup=False" in compose_source
    ), "The compose method should set markup=False on the diff Static widget"

    # Also verify the diff content is stored correctly
    assert modal.diff_content == diff_content


def test_diff_content_preserves_special_characters() -> None:
    """Test that special characters in diffs are preserved literally."""
    # Create diff with various special characters that could be interpreted as markup
    diff_with_special_chars = """@@ -10,7 +10,9 @@
-    old_line with [color] tags
+    new_line with {curly} braces
+    another line with `backticks` and **asterisks**
     unchanged line
-    line with <angle> brackets
+    line with [square] brackets and __underscores__
"""

    modal = KernelApprovalModal(diff_with_special_chars, "special-chars-test")

    # The diff content should be stored exactly as provided
    assert modal.diff_content == diff_with_special_chars
    assert "[color]" in modal.diff_content
    assert "{curly}" in modal.diff_content
    assert "`backticks`" in modal.diff_content
    assert "**asterisks**" in modal.diff_content
    assert "[square]" in modal.diff_content
    assert "__underscores__" in modal.diff_content
