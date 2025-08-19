import importlib.util
from pathlib import Path

import pytest

# Skip if hook file doesn't exist (e.g., in CI)
hook_path = Path(".claude/hooks/format_md.py")
if not hook_path.exists():
    pytest.skip("Hook file not available", allow_module_level=True)

SPEC = importlib.util.spec_from_file_location("format_md", str(hook_path))
fmt = importlib.util.module_from_spec(SPEC)  # type: ignore
assert SPEC and SPEC.loader
SPEC.loader.exec_module(fmt)


def test_format_markdown_text_basic() -> None:
    raw = "#  Title\\n\\n-  item\\n-  item2"
    out = fmt._format_markdown_text(raw)
    assert isinstance(out, str)
    assert "# Title" in out  # normalized header
