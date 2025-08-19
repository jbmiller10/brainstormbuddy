"""Test markdown formatting hook functionality using generated hooks."""

import importlib.util
from pathlib import Path

from app.permissions.settings_writer import write_project_settings


def test_format_markdown_text_via_generated_hook(tmp_path: Path) -> None:
    """Test markdown formatting through a generated hook file."""
    # Generate settings with hooks in temp directory
    config_dir = write_project_settings(
        repo_root=tmp_path, config_dir_name=".claude", import_hooks_from="app.permissions.hooks_lib"
    )

    # Load the generated format_md.py hook using importlib
    hook_path = config_dir / "hooks" / "format_md.py"
    assert hook_path.exists(), f"Hook file not found at {hook_path}"

    spec = importlib.util.spec_from_file_location("format_md_hook", str(hook_path))
    assert spec is not None and spec.loader is not None

    format_md_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(format_md_module)

    # Test the _format_markdown_text function from the generated hook
    raw = "#  Title\\n\\n-  item\\n-  item2"
    out = format_md_module._format_markdown_text(raw)

    # Verify formatting worked
    assert isinstance(out, str)
    assert "# Title" in out  # normalized header

    # Test with more complex markdown
    complex_md = "#   Heading with spaces\n\n*  Unordered item\n*  Another item\n\n1.  Ordered item\n2.  Second item"

    formatted = format_md_module._format_markdown_text(complex_md)
    assert isinstance(formatted, str)
    assert "# Heading with spaces" in formatted  # normalized
    assert formatted != complex_md  # should be different after formatting


def test_generated_hook_imports_from_hooks_lib(tmp_path: Path) -> None:
    """Verify the generated hook correctly imports from hooks_lib."""
    # Generate settings
    config_dir = write_project_settings(
        repo_root=tmp_path, config_dir_name=".claude", import_hooks_from="app.permissions.hooks_lib"
    )

    # Read the generated hook file
    hook_path = config_dir / "hooks" / "format_md.py"
    hook_content = hook_path.read_text()

    # Verify it imports from the correct module
    assert "from app.permissions.hooks_lib.format_md import _format_markdown_text" in hook_content
    assert "def main() -> None:" in hook_content
    assert "PostToolUse" in hook_content
