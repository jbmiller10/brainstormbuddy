import importlib.util

SPEC = importlib.util.spec_from_file_location("format_md", ".claude/hooks/format_md.py")
fmt = importlib.util.module_from_spec(SPEC)  # type: ignore
assert SPEC and SPEC.loader
SPEC.loader.exec_module(fmt)


def test_format_markdown_text_basic() -> None:
    raw = "#  Title\\n\\n-  item\\n-  item2"
    out = fmt._format_markdown_text(raw)
    assert isinstance(out, str)
    assert "# Title" in out  # normalized header
