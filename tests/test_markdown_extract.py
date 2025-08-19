"""Unit tests for markdown extraction utilities."""

from app.files.markdown import extract_section_paragraph


def test_extract_basic_paragraph() -> None:
    """Test extracting a simple paragraph after a header."""
    md = """
# Document Title

## Core Concept

This is the core concept paragraph that should be extracted.

## Another Section

This should not be extracted.
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "This is the core concept paragraph that should be extracted."


def test_extract_with_no_blank_line_after_header() -> None:
    """Test extraction when there's no blank line after the header."""
    md = """## Core Concept
The concept starts immediately after the header.

## Next Section
Other content."""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "The concept starts immediately after the header."


def test_extract_with_multiple_blank_lines() -> None:
    """Test extraction with extra blank lines."""
    md = """
## Core Concept


The concept has multiple blank lines before it.

More content here.

## Another Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "The concept has multiple blank lines before it."


def test_extract_with_nested_headers() -> None:
    """Test that extraction stops at subheaders within the section."""
    md = """
## Core Concept

Main concept paragraph here.

### Subsection

This is under a subsection and should not be included.

## Another Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "Main concept paragraph here."


def test_extract_with_different_capitalization() -> None:
    """Test case-insensitive header matching."""
    test_cases = [
        ("## CORE CONCEPT\nUppercase header.", "## Core Concept"),
        ("## core concept\nLowercase header.", "## Core Concept"),
        ("## Core CONCEPT\nMixed case header.", "## Core Concept"),
        ("## CoRe CoNcEpT\nRandom case header.", "## Core Concept"),
    ]

    for md, header in test_cases:
        result = extract_section_paragraph(md, header)
        assert result is not None
        assert "header" in result.lower()


def test_extract_strips_markdown_emphasis() -> None:
    """Test that markdown emphasis markers are stripped."""
    md = """
## Core Concept

*This is an italicized concept* with **bold text** and _more italics_ plus __more bold__.

## Next Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "This is an italicized concept with bold text and more italics plus more bold."


def test_extract_multiline_paragraph() -> None:
    """Test extracting a paragraph that spans multiple lines."""
    md = """
## Core Concept

This is a paragraph
that spans multiple
lines in the source.

## Another Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "This is a paragraph that spans multiple lines in the source."


def test_extract_missing_section() -> None:
    """Test that None is returned when section doesn't exist."""
    md = """
## Different Section

Some content here.

## Another Section

More content.
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result is None


def test_extract_empty_section() -> None:
    """Test that None is returned when section has no content."""
    md = """
## Core Concept

## Next Section

Content in next section.
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result is None


def test_extract_different_header_levels() -> None:
    """Test extraction with different header levels."""
    md1 = """
# Core Concept

Level 1 header content.

# Another Section
"""
    result1 = extract_section_paragraph(md1, "# Core Concept")
    assert result1 == "Level 1 header content."

    md3 = """
### Core Concept

Level 3 header content.

### Another Section
"""
    result3 = extract_section_paragraph(md3, "### Core Concept")
    assert result3 == "Level 3 header content."


def test_extract_with_list_items() -> None:
    """Test extracting content that includes list markers."""
    md = """
## Core Concept

* This is a bullet point that should be extracted
- Along with this one
+ And this one too

## Next Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    # The function joins lines, so list items become one paragraph
    assert result is not None
    assert "This is a bullet point" in result
    assert "Along with this one" in result
    assert "And this one too" in result


def test_extract_only_first_paragraph() -> None:
    """Test that only the first paragraph is extracted."""
    md = """
## Core Concept

This is the first paragraph that should be extracted.

This is the second paragraph that should NOT be extracted.

And definitely not this third one.

## Another Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "This is the first paragraph that should be extracted."
    assert result is not None
    assert "second paragraph" not in result
    assert "third one" not in result


def test_extract_with_code_block() -> None:
    """Test that extraction stops at code blocks."""
    md = """
## Core Concept

This is the concept description.

```python
def example():
    pass
```

More text after code.

## Next Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "This is the concept description."
    assert "def example" not in result
    assert "More text" not in result


def test_extract_with_whitespace_in_header() -> None:
    """Test headers with extra whitespace."""
    md = """
##   Core Concept

Content with extra spaces in header.

## Another Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "Content with extra spaces in header."


def test_extract_empty_input() -> None:
    """Test with empty or None input."""
    assert extract_section_paragraph("", "## Core Concept") is None
    assert extract_section_paragraph("   ", "## Core Concept") is None


def test_extract_invalid_header_format() -> None:
    """Test with invalid header format."""
    md = "## Core Concept\nSome content."

    # Header without # symbols
    assert extract_section_paragraph(md, "Core Concept") is None

    # Empty header
    assert extract_section_paragraph(md, "") is None


def test_extract_preserve_inline_formatting() -> None:
    """Test that inline code and links are preserved (minus emphasis)."""
    md = """
## Core Concept

This has `inline code` and [a link](http://example.com) with **bold** text.

## Next
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result is not None
    assert "`inline code`" in result
    assert "[a link](http://example.com)" in result
    assert "bold" in result
    assert "**bold**" not in result


def test_extract_complex_emphasis_patterns() -> None:
    """Test complex emphasis stripping patterns."""
    md = """
## Core Concept

Text with ***triple emphasis*** and ___underscores___ and mixed **_bold italic_**.

## Next
"""
    result = extract_section_paragraph(md, "## Core Concept")
    # Should strip outer emphasis but preserve the text
    assert result is not None
    assert "triple emphasis" in result
    assert "underscores" in result
    assert "bold italic" in result


def test_extract_default_header() -> None:
    """Test that default header parameter works."""
    md = """
## Core Concept

Default header extraction test.

## Other
"""
    # Should use "## Core Concept" by default
    result = extract_section_paragraph(md)
    assert result == "Default header extraction test."


def test_extract_code_block_first_no_prose() -> None:
    """Test when code block is first content with no prose."""
    md = """
## Core Concept

```python
def example():
    # This is inside the code block
    return 42
```

This text comes after the code block.

## Next Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "This text comes after the code block."
    assert "def example" not in result
    assert "return 42" not in result


def test_extract_code_block_with_tilde_fences() -> None:
    """Test code blocks with tilde fences."""
    md = """
## Core Concept

Some prose content here.

~~~javascript
console.log("Hello");
console.log("World");
~~~

More text after code.

## Next Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "Some prose content here."
    assert "console.log" not in result
    assert "Hello" not in result


def test_extract_nested_code_blocks() -> None:
    """Test multiple code blocks in sequence."""
    md = """
## Core Concept

```python
# First code block
x = 1
```

```javascript
// Second code block
let y = 2;
```

This is the actual prose content.

## Next Section
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "This is the actual prose content."
    assert "x = 1" not in result
    assert "let y = 2" not in result


def test_extract_code_block_no_blank_before() -> None:
    """Test code block immediately after prose with no blank line."""
    md = """
## Core Concept
This is the prose content.
```python
def ignored():
    pass
```
This should not be included.
"""
    result = extract_section_paragraph(md, "## Core Concept")
    assert result == "This is the prose content."
    assert "def ignored" not in result
    assert "This should not be included" not in result
