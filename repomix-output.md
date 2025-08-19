This file is a merged representation of a subset of the codebase, containing files not matching ignore patterns, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching these patterns are excluded: *lock, *.md, *repomix*
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
app/
  core/
    config.py
  files/
    atomic.py
    diff.py
    mdio.py
    scaffold.py
  llm/
    prompts/
      clarify.md
      kernel.md
      outline.md
      research.md
      synthesis.md
    claude_client.py
    sessions.py
  permissions/
    settings_writer.py
  tui/
    views/
      __init__.py
      main_screen.py
    widgets/
      __init__.py
      command_palette.py
      context_panel.py
      file_tree.py
      session_viewer.py
    __init__.py
    app.py
  __init__.py
brainstormbuddy/
  .obsidian/
    app.json
    appearance.json
    core-plugins.json
    graph.json
    workspace.json
  Welcome.md
tests/
  test_config.py
  test_diff.py
  test_format_md_hook.py
  test_llm_fake.py
  test_mdio.py
  test_policies.py
  test_scaffold.py
  test_settings_writer.py
  test_smoke.py
  test_tui_imports.py
.gitignore
.pre-commit-config.yaml
pyproject.toml
```

# Files

## File: app/files/atomic.py
````python
"""Atomic file write utilities."""

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path | str, text: str) -> None:
    """
    Write text to a file atomically using temp file and replace.

    This ensures the file is either fully updated or not modified at all,
    preventing partial writes in case of errors. Uses the same durability
    pattern as apply_patch.

    Args:
        path: Path to the file to write
        text: Text content to write (UTF-8 encoded)

    Raises:
        IOError: If there's an error during the atomic write operation
    """
    file_path = Path(path) if isinstance(path, str) else path

    # Precompute file mode if file exists
    file_mode = None
    if file_path.exists():
        file_mode = os.stat(file_path).st_mode

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary file first
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=file_path.parent,
        delete=False,
        suffix=".tmp",
    ) as tmp_file:
        tmp_file.write(text)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_path = Path(tmp_file.name)

    try:
        # Preserve file mode if original file existed
        if file_mode is not None:
            os.chmod(tmp_path, file_mode)

        # Atomically replace the original file
        tmp_path.replace(file_path)

        # Fsync parent directory for durability (best-effort)
        try:
            dfd = os.open(file_path.parent, os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:
            # Platform/filesystem doesn't support directory fsync
            pass
    except Exception:
        # Clean up temp file if replacement fails
        tmp_path.unlink(missing_ok=True)
        raise
````

## File: tests/test_format_md_hook.py
````python
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
````

## File: tests/test_mdio.py
````python
"""Unit tests for Markdown I/O utilities."""

import tempfile
from pathlib import Path

import pytest

from app.files.mdio import read_md, write_md


def test_write_md_creates_nested_directories() -> None:
    """Test that write_md creates parent directories if they don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write to a deeply nested path that doesn't exist
        nested_path = Path(tmpdir) / "level1" / "level2" / "level3" / "test.md"
        content = "# Test Content\n\nThis is a test."

        write_md(nested_path, content)

        # Verify file was created and content is correct
        assert nested_path.exists()
        assert read_md(nested_path) == content


def test_write_md_overwrites_existing_file() -> None:
    """Test that write_md correctly overwrites an existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"

        # Write initial content
        initial_content = "# Initial\n\nFirst version."
        write_md(file_path, initial_content)
        assert read_md(file_path) == initial_content

        # Overwrite with new content
        new_content = "# Updated\n\nSecond version."
        write_md(file_path, new_content)
        assert read_md(file_path) == new_content


def test_unicode_content_roundtrip() -> None:
    """Test that Unicode content is correctly written and read back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "unicode_test.md"

        # Test various Unicode characters
        unicode_content = "# Unicode Test æøå—π🙂\n\n" + \
                         "Chinese: 你好世界\n" + \
                         "Japanese: こんにちは\n" + \
                         "Arabic: مرحبا بالعالم\n" + \
                         "Emoji: 🚀 🌟 ✨\n" + \
                         "Math: ∑ ∫ √ ∞ π"

        write_md(file_path, unicode_content)
        read_content = read_md(file_path)

        assert read_content == unicode_content


def test_idempotent_write_same_content() -> None:
    """Test that writing the same content twice is idempotent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "idempotent_test.md"
        content = "# Idempotent Test\n\nSame content written twice."

        # First write
        write_md(file_path, content)
        first_content = read_md(file_path)

        # Second write with identical content
        write_md(file_path, content)
        second_content = read_md(file_path)

        # Content should be identical
        assert first_content == second_content == content
        # File should exist and have been replaced (mtime may differ)
        assert file_path.exists()


def test_read_md_with_string_path() -> None:
    """Test that read_md works with string paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"
        content = "# String Path Test"

        write_md(str(file_path), content)
        assert read_md(str(file_path)) == content


def test_write_md_with_string_path() -> None:
    """Test that write_md works with string paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.md"
        content = "# String Path Test"

        write_md(str(file_path), content)
        assert read_md(file_path) == content


def test_read_md_nonexistent_file() -> None:
    """Test that read_md raises FileNotFoundError for non-existent files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_path = Path(tmpdir) / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            read_md(nonexistent_path)


def test_empty_file_roundtrip() -> None:
    """Test that empty files are handled correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "empty.md"

        write_md(file_path, "")
        assert read_md(file_path) == ""


def test_large_content_roundtrip() -> None:
    """Test that large content is correctly written and read back."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "large.md"

        # Create a large content string (1MB+)
        large_content = "# Large File\n\n" + ("This is a line of text. " * 100 + "\n") * 5000

        write_md(file_path, large_content)
        read_content = read_md(file_path)

        assert read_content == large_content


def test_special_characters_in_content() -> None:
    """Test that special characters are preserved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "special.md"

        special_content = "# Special Characters\n\n" + \
                         "Quotes: \"double\" 'single'\n" + \
                         "Backslash: \\ \\\\ \\\\\\\n" + \
                         "Tabs: \t\t\tindented\n" + \
                         "NULL char exclusion test (should work without null)"

        write_md(file_path, special_content)
        assert read_md(file_path) == special_content


def test_preserve_exact_content() -> None:
    """Test that content with no trailing newline is preserved exactly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "exact.md"

        # Content with no trailing newline
        content_no_newline = "# No trailing newline"
        write_md(file_path, content_no_newline)
        assert read_md(file_path) == content_no_newline

        # Content with trailing newline
        content_with_newline = "# With trailing newline\n"
        write_md(file_path, content_with_newline)
        assert read_md(file_path) == content_with_newline
````

## File: app/core/config.py
````python
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: str = "projects"
    exports_dir: str = "exports"
    log_dir: str = "logs"
    enable_web_tools: bool = False

    class Config:
        env_prefix = "BRAINSTORMBUDDY_"


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings()
````

## File: app/files/mdio.py
````python
"""Markdown file I/O utilities."""

from pathlib import Path

from app.files.atomic import atomic_write_text


def read_md(path: Path | str) -> str:
    """
    Read a markdown file and return its contents.

    Args:
        path: Path to the markdown file

    Returns:
        Contents of the markdown file

    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    file_path = Path(path) if isinstance(path, str) else path

    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_md(path: Path | str, text: str) -> None:
    """
    Write text to a markdown file.

    Args:
        path: Path to the markdown file
        text: Content to write to the file

    Raises:
        IOError: If there's an error writing the file
    """
    file_path = Path(path) if isinstance(path, str) else path

    atomic_write_text(file_path, text)
````

## File: app/files/scaffold.py
````python
"""Project scaffold utility for creating standardized project structures."""

from datetime import datetime
from pathlib import Path

import yaml

from app.files.atomic import atomic_write_text


def scaffold_project(slug: str, base: Path | str = "projects") -> Path:
    """
    Create a project directory structure with seed files.

    Args:
        slug: Project identifier (will be used as directory name)
        base: Base directory for projects (default: "projects")

    Returns:
        Path to the created/existing project directory

    The function is idempotent - running it multiple times with the same
    slug will not cause errors or duplicate content.
    """
    base_path = Path(base) if isinstance(base, str) else base
    project_path = base_path / slug

    # Create directory structure
    _create_directories(project_path)

    # Create seed files
    _create_project_yaml(project_path / "project.yaml", slug)
    _create_kernel_md(project_path / "kernel.md", slug)
    _create_outline_md(project_path / "outline.md", slug)

    return project_path


def _create_directories(project_path: Path) -> None:
    """Create the required directory structure."""
    directories = [
        project_path,
        project_path / "elements",
        project_path / "research",
        project_path / "exports",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def _create_project_yaml(file_path: Path, slug: str) -> None:
    """Create project.yaml with basic metadata if it doesn't exist."""
    if file_path.exists():
        return

    project_data = {
        "name": slug,
        "created": datetime.now().isoformat(),
        "stage": "capture",
        "description": f"Brainstorming project: {slug}",
        "tags": [],
        "metadata": {
            "version": "1.0.0",
            "format": "brainstormbuddy-project",
        },
    }

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(project_data, f, default_flow_style=False, sort_keys=False)


def _create_kernel_md(file_path: Path, slug: str) -> None:
    """Create kernel.md with minimal structure if it doesn't exist."""
    if file_path.exists():
        return

    content = f"""---
title: Kernel
project: {slug}
created: {datetime.now().isoformat()}
stage: kernel
---

# Kernel

## Core Concept

*The essential idea or problem to explore.*

## Key Questions

*What are we trying to answer or solve?*

## Success Criteria

*How will we know when we've achieved our goal?*
"""

    atomic_write_text(file_path, content)


def _create_outline_md(file_path: Path, slug: str) -> None:
    """Create outline.md with minimal structure if it doesn't exist."""
    if file_path.exists():
        return

    content = f"""---
title: Outline
project: {slug}
created: {datetime.now().isoformat()}
stage: outline
---

# Outline

## Executive Summary

*High-level overview of the project.*

## Main Sections

### Section 1

*Key points and structure.*

### Section 2

*Key points and structure.*

### Section 3

*Key points and structure.*

## Next Steps

*What needs to be done next?*
"""

    atomic_write_text(file_path, content)


def ensure_project_exists(slug: str, base: Path | str = "projects") -> Path:
    """
    Ensure a project exists, creating it if necessary.

    This is an alias for scaffold_project for clarity in different contexts.
    """
    return scaffold_project(slug, base)
````

## File: app/llm/prompts/clarify.md
````markdown
<instructions>
You are in the clarify stage of brainstorming. Your goal is to help the user refine and sharpen their initial idea through targeted questions. Ask 3-7 numbered questions that probe different aspects of their concept. Do not provide advice or solutions - only questions that help clarify thinking.
</instructions>

<context>
The user has provided an initial brainstorming topic or problem. You have read-only access to any existing project documents. Your role is to help them think more deeply about what they're trying to achieve before moving to the kernel stage.
</context>

<format>
Present your response as:
1. A brief acknowledgment of their topic (1 sentence)
2. Numbered questions (3-7 total) that explore:
   - Core objectives and success criteria
   - Constraints and boundaries
   - Key stakeholders or audiences
   - Underlying assumptions
   - Scope and scale

Keep the entire response under 300 words. Focus on questions that will lead to actionable insights in the next stages.
</format>
````

## File: app/llm/prompts/kernel.md
````markdown
<instructions>
You are in the kernel stage of brainstorming. Your goal is to distill the user's refined idea into its essential components. Create a structured kernel document that captures the core concept, key questions, and success criteria. This will serve as the foundation for the outline stage.
</instructions>

<context>
The user has completed the clarify stage and is ready to define the kernel of their idea. You can read existing project documents and will propose a diff for projects/<slug>/kernel.md. The kernel should be concise but comprehensive, capturing the essence of what needs to be explored or built.
</context>

<format>
Propose a diff for the kernel.md file with these sections:

## Core Concept
A clear, 2-3 sentence description of the essential idea or problem.

## Key Questions
3-5 fundamental questions that must be answered for success.

## Success Criteria
3-5 measurable outcomes that define success.

## Constraints
Key limitations or boundaries to work within.

## Primary Value Proposition
One paragraph describing the main value or impact.

Keep the entire kernel under 250 words. Use markdown formatting and be specific rather than generic.
</format>
````

## File: app/llm/prompts/outline.md
````markdown
<instructions>
You are in the outline stage of brainstorming. Your goal is to expand the kernel into 6-10 workstreams, each with a defined scope and exploration questions. Create both an outline.md overview and individual element files for each workstream.
</instructions>

<context>
The user has completed the kernel stage. You can read the kernel.md and will propose diffs for outline.md and elements/*.md files. Each workstream should be a logical component of the overall concept, with clear boundaries and specific questions to explore.
</context>

<format>
First, propose a diff for outline.md with:

# Project Outline

## Overview
One paragraph synthesis of how workstreams connect.

## Workstreams
1. **[Workstream Name]**: Brief description (1 sentence)
2. **[Workstream Name]**: Brief description (1 sentence)
[... 6-10 total workstreams]

## Dependencies
Key relationships between workstreams.

Then, for each workstream, propose a diff for elements/[workstream-slug].md:

# [Workstream Name]

## Scope
What this workstream covers and excludes.

## Key Questions
1. [Specific exploration question]
2. [Specific exploration question]
3. [Specific exploration question]
[... 3-6 questions per workstream]

## Success Metrics
How to measure completion or success.

## Related Workstreams
Links to other relevant elements.

Keep each element file under 200 words. Be specific and actionable.
</format>
````

## File: app/llm/prompts/research.md
````markdown
<instructions>
You are in the research stage as a "researcher" agent. Your goal is to extract atomic findings from provided sources and structure them for integration into the project's knowledge base. Do not perform any web calls - work only with the provided content. Output findings as machine-readable JSONL for SQLite FTS ingestion.
</instructions>

<context>
You have access to read project documents and provided research content. Your role is to decompose complex information into discrete, verifiable claims with proper attribution. Each finding should be self-contained and traceable to its source. Focus on relevance to the project's kernel and workstreams.
</context>

<format>
Output ONLY a single fenced code block of type jsonl containing one JSON object per line. Do not include any text outside the fenced block. Each line must be a valid JSON object with these exact keys:

- id: UUID string (e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
- url: Source URL or document reference
- source_type: Type of source (e.g., "article", "documentation", "research_paper")
- claim: One specific, falsifiable statement extracted from the source
- evidence: Direct quote or paraphrase supporting the claim (max 100 words)
- confidence: Float between 0.0 and 1.0 based on source reliability and claim specificity
- tags: Comma-separated keywords for categorization (e.g., "architecture,performance,caching")
- workstream: Which project workstream this finding supports
- retrieved_at: ISO8601 timestamp (e.g., "2024-01-15T14:30:00Z")

Example (exactly 2 lines in the jsonl block):

```jsonl
{"id": "f47ac10b-58cc-4372-a567-0e02b2c3d479", "url": "https://docs.python.org/3/library/sqlite3.html", "source_type": "documentation", "claim": "SQLite FTS5 extension provides full-text search with BM25 ranking", "evidence": "FTS5 is an SQLite virtual table module that provides full-text search functionality with built-in BM25 ranking algorithm for relevance scoring", "confidence": 0.95, "tags": "sqlite,fts,search,ranking", "workstream": "research", "retrieved_at": "2024-01-15T10:45:00Z"}
{"id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", "url": "https://textual.textualize.io/guide/", "source_type": "article", "claim": "Textual provides reactive data binding for TUI components", "evidence": "Textual's reactive attributes automatically update the UI when their values change, enabling declarative UI patterns", "confidence": 0.90, "tags": "textual,tui,reactive,ui", "workstream": "interface", "retrieved_at": "2024-01-15T10:47:00Z"}
```
</format>
````

## File: app/llm/prompts/synthesis.md
````markdown
<instructions>
You are in the synthesis stage as an "architect" agent. Your goal is to transform the kernel and research findings into structured requirements and implementation guidance. Do not perform any web calls. Output your synthesis as a diff proposal for element markdown files under elements/<slug>.md.
</instructions>

<context>
You have access to the project's kernel, outline, and research findings. Your role is to synthesize these inputs into actionable specifications that bridge conceptual design and implementation. Focus on clarity, completeness, and risk mitigation.
</context>

<format>
Propose diffs for elements/<slug>.md files with these sections:

## Decisions
Key architectural and design choices made based on research. Each decision should reference supporting findings and rationale.

## Requirements
Concrete, testable requirements derived from the kernel and research. Use numbered lists with clear success criteria.

## Open Questions
Unresolved issues requiring further investigation or stakeholder input. Include potential impact and suggested resolution approaches.

## Risks & Mitigations
Identified risks with probability, impact, and mitigation strategies. Focus on technical, resource, and scope risks.

## Acceptance Criteria
Measurable conditions that must be met for this workstream to be considered complete. Link to specific requirements and success metrics.

Keep each section concise (50-100 words). Use bullet points and numbered lists for clarity. Reference research findings by ID where applicable. Total file should be under 500 words.
</format>
````

## File: app/tui/views/main_screen.py
````python
"""Main screen view with three-pane structure."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header

from app.tui.widgets import CommandPalette, ContextPanel, FileTree, SessionViewer


class MainScreen(Screen[None]):
    """Main three-pane screen for the application."""

    def compose(self) -> ComposeResult:
        """Compose the main three-pane layout."""
        yield Header()
        with Horizontal():
            yield FileTree()
            yield SessionViewer()
            yield ContextPanel()
        yield Footer()
        yield CommandPalette()
````

## File: app/tui/widgets/__init__.py
````python
"""Reusable widget components for the TUI."""

from .command_palette import CommandPalette
from .context_panel import ContextPanel
from .file_tree import FileTree
from .session_viewer import SessionViewer

__all__ = ["CommandPalette", "ContextPanel", "FileTree", "SessionViewer"]
````

## File: app/tui/widgets/command_palette.py
````python
"""Command palette widget for executing app commands."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, OptionList


class CommandPalette(Container):
    """Command palette overlay for executing commands."""

    DEFAULT_CSS = """
    CommandPalette {
        layer: modal;
        align: center middle;
        width: 60;
        height: auto;
        max-height: 20;
        background: $panel;
        border: thick $primary;
        padding: 1;
        display: none;
    }

    CommandPalette.visible {
        display: block;
    }

    CommandPalette Input {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close palette"),
    ]

    def __init__(self) -> None:
        """Initialize the command palette."""
        super().__init__(id="command-palette")
        self.commands = [
            ("new project", "Create a new brainstorming project"),
            ("clarify", "Enter clarify stage for current project"),
            ("kernel", "Define the kernel of your idea"),
            ("outline", "Create workstream outline"),
            ("research import", "Import research findings"),
            ("synthesis", "Synthesize findings into final output"),
            ("export", "Export project to various formats"),
        ]

    def compose(self) -> ComposeResult:
        """Compose the command palette UI."""
        yield Input(placeholder="Type a command...", id="command-input")
        options = [f"{cmd}: {desc}" for cmd, desc in self.commands]
        yield OptionList(*options, id="command-list")

    def show(self) -> None:
        """Show the command palette."""
        self.add_class("visible")
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

    def hide(self) -> None:
        """Hide the command palette."""
        self.remove_class("visible")

    def action_close(self) -> None:
        """Close the command palette."""
        self.hide()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        command = event.value.lower().strip()
        self.execute_command(command)
        self.hide()

    def execute_command(self, command: str) -> None:
        """Execute the selected command."""
        # Placeholder for command execution
        from textual import log

        log(f"Executing command: {command}")
````

## File: app/tui/widgets/context_panel.py
````python
"""Context panel widget for displaying relevant cards and information."""

from textual.containers import VerticalScroll
from textual.widgets import Static


class ContextPanel(VerticalScroll):
    """Right-side panel for context cards and relevant information."""

    DEFAULT_CSS = """
    ContextPanel {
        width: 35;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    .context-card {
        background: $panel;
        border: solid $primary-lighten-2;
        padding: 1;
        margin-bottom: 1;
    }
    """

    def __init__(self) -> None:
        """Initialize the context panel."""
        super().__init__(id="context-panel")

    def on_mount(self) -> None:
        """Add placeholder context cards."""
        self.mount(
            Static(
                "[bold]Current Stage[/bold]\n[dim]Capture[/dim]",
                classes="context-card",
            )
        )
        self.mount(
            Static(
                "[bold]Project Info[/bold]\n[dim]No project selected[/dim]",
                classes="context-card",
            )
        )
        self.mount(
            Static(
                "[bold]Recent Actions[/bold]\n[dim]• App started\n• Waiting for command[/dim]",
                classes="context-card",
            )
        )
````

## File: app/tui/widgets/file_tree.py
````python
"""File tree widget for project navigation."""

from textual.widgets import Tree


class FileTree(Tree[str]):
    """File tree for navigating project documents."""

    DEFAULT_CSS = """
    FileTree {
        width: 30;
        background: $surface;
        border: solid $primary;
    }
    """

    def __init__(self) -> None:
        """Initialize the file tree with placeholder content."""
        super().__init__("Projects", id="file-tree")

    def on_mount(self) -> None:
        """Populate the tree with placeholder project structure."""
        root = self.root
        root.expand()

        # Add placeholder project structure
        project1 = root.add("📁 example-project", expand=False)
        project1.add_leaf("📄 kernel.md")
        project1.add_leaf("📄 outline.md")
        project1.add_leaf("📄 project.yaml")

        elements = project1.add("📁 elements", expand=False)
        elements.add_leaf("📄 workstream-1.md")
        elements.add_leaf("📄 workstream-2.md")

        research = project1.add("📁 research", expand=False)
        research.add_leaf("📄 findings.md")

        exports = project1.add("📁 exports", expand=False)
        exports.add_leaf("📄 synthesis.md")
````

## File: app/tui/widgets/session_viewer.py
````python
"""Session viewer widget for displaying editor content or Claude streams."""

from textual.widgets import RichLog


class SessionViewer(RichLog):
    """Main content viewer for editing documents or viewing session output."""

    DEFAULT_CSS = """
    SessionViewer {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    """

    def __init__(self) -> None:
        """Initialize the session viewer."""
        super().__init__(id="session-viewer", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        """Display welcome message on mount."""
        self.write("[bold cyan]Welcome to Brainstorm Buddy[/bold cyan]\n")
        self.write("\nA terminal-first brainstorming app that guides you through:\n")
        self.write("• [yellow]Capture[/yellow] → [yellow]Clarify[/yellow] → ")
        self.write("[yellow]Kernel[/yellow] → [yellow]Outline[/yellow] → ")
        self.write("[yellow]Research[/yellow] → [yellow]Synthesis[/yellow] → ")
        self.write("[yellow]Export[/yellow]\n")
        self.write("\n[dim]Press ':' to open the command palette[/dim]")
````

## File: brainstormbuddy/.obsidian/app.json
````json
{}
````

## File: brainstormbuddy/.obsidian/appearance.json
````json
{}
````

## File: brainstormbuddy/.obsidian/core-plugins.json
````json
{
  "file-explorer": true,
  "global-search": true,
  "switcher": true,
  "graph": true,
  "backlink": true,
  "canvas": true,
  "outgoing-link": true,
  "tag-pane": true,
  "footnotes": false,
  "properties": false,
  "page-preview": true,
  "daily-notes": true,
  "templates": true,
  "note-composer": true,
  "command-palette": true,
  "slash-command": false,
  "editor-status": true,
  "bookmarks": true,
  "markdown-importer": false,
  "zk-prefixer": false,
  "random-note": false,
  "outline": true,
  "word-count": true,
  "slides": false,
  "audio-recorder": false,
  "workspaces": false,
  "file-recovery": true,
  "publish": false,
  "sync": true,
  "bases": true,
  "webviewer": false
}
````

## File: brainstormbuddy/.obsidian/graph.json
````json
{
  "collapse-filter": true,
  "search": "",
  "showTags": false,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": true,
  "colorGroups": [],
  "collapse-display": true,
  "showArrow": false,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.518713248970312,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250,
  "scale": 1,
  "close": true
}
````

## File: brainstormbuddy/.obsidian/workspace.json
````json
{
  "main": {
    "id": "c9770cc6bfb7b9dd",
    "type": "split",
    "children": [
      {
        "id": "387ea85083a296f6",
        "type": "tabs",
        "children": [
          {
            "id": "ac74706926fea592",
            "type": "leaf",
            "state": {
              "type": "markdown",
              "state": {
                "file": "Welcome.md",
                "mode": "source",
                "source": false
              },
              "icon": "lucide-file",
              "title": "Welcome"
            }
          }
        ]
      },
      {
        "id": "7a3b0dc4a998c716",
        "type": "tabs",
        "children": [
          {
            "id": "3b33062978337689",
            "type": "leaf",
            "state": {
              "type": "graph",
              "state": {},
              "icon": "lucide-git-fork",
              "title": "Graph view"
            }
          }
        ]
      }
    ],
    "direction": "vertical"
  },
  "left": {
    "id": "ff992d2badc930c6",
    "type": "split",
    "children": [
      {
        "id": "7179f113afc8c1b1",
        "type": "tabs",
        "children": [
          {
            "id": "b510e60ac73b5ffd",
            "type": "leaf",
            "state": {
              "type": "file-explorer",
              "state": {
                "sortOrder": "alphabetical",
                "autoReveal": false
              },
              "icon": "lucide-folder-closed",
              "title": "Files"
            }
          },
          {
            "id": "c947aeb017ea6771",
            "type": "leaf",
            "state": {
              "type": "search",
              "state": {
                "query": "",
                "matchingCase": false,
                "explainSearch": false,
                "collapseAll": false,
                "extraContext": false,
                "sortOrder": "alphabetical"
              },
              "icon": "lucide-search",
              "title": "Search"
            }
          },
          {
            "id": "5c82e1dd20dfb01b",
            "type": "leaf",
            "state": {
              "type": "bookmarks",
              "state": {},
              "icon": "lucide-bookmark",
              "title": "Bookmarks"
            }
          }
        ]
      }
    ],
    "direction": "horizontal",
    "width": 300
  },
  "right": {
    "id": "3bc2bd1cfd7999fa",
    "type": "split",
    "children": [
      {
        "id": "e6cc26d4072cfb9f",
        "type": "tabs",
        "children": [
          {
            "id": "db35ce30a57e9f72",
            "type": "leaf",
            "state": {
              "type": "backlink",
              "state": {
                "collapseAll": false,
                "extraContext": false,
                "sortOrder": "alphabetical",
                "showSearch": false,
                "searchQuery": "",
                "backlinkCollapsed": false,
                "unlinkedCollapsed": true
              },
              "icon": "links-coming-in",
              "title": "Backlinks"
            }
          },
          {
            "id": "9e144b07e94c02c9",
            "type": "leaf",
            "state": {
              "type": "outgoing-link",
              "state": {
                "linksCollapsed": false,
                "unlinkedCollapsed": true
              },
              "icon": "links-going-out",
              "title": "Outgoing links"
            }
          },
          {
            "id": "af8ee537cc1ed312",
            "type": "leaf",
            "state": {
              "type": "tag",
              "state": {
                "sortOrder": "frequency",
                "useHierarchy": true,
                "showSearch": false,
                "searchQuery": ""
              },
              "icon": "lucide-tags",
              "title": "Tags"
            }
          },
          {
            "id": "89a06c137d5cbc28",
            "type": "leaf",
            "state": {
              "type": "outline",
              "state": {
                "followCursor": false,
                "showSearch": false,
                "searchQuery": ""
              },
              "icon": "lucide-list",
              "title": "Outline"
            }
          }
        ]
      }
    ],
    "direction": "horizontal",
    "width": 300,
    "collapsed": true
  },
  "left-ribbon": {
    "hiddenItems": {
      "switcher:Open quick switcher": false,
      "graph:Open graph view": false,
      "canvas:Create new canvas": false,
      "daily-notes:Open today's daily note": false,
      "templates:Insert template": false,
      "command-palette:Open command palette": false,
      "bases:Create new base": false
    }
  },
  "active": "3b33062978337689",
  "lastOpenFiles": [
    "Welcome.md"
  ]
}
````

## File: brainstormbuddy/Welcome.md
````markdown
This is your new *vault*.

Make a note of something, [[create a link]], or try [the Importer](https://help.obsidian.md/Plugins/Importer)!

When you're ready, delete this note and make the vault your own.
````

## File: tests/test_config.py
````python
import pytest

from app.core.config import Settings, load_settings


def test_default_settings() -> None:
    settings = Settings()
    assert settings.data_dir == "projects"
    assert settings.exports_dir == "exports"
    assert settings.log_dir == "logs"
    assert settings.enable_web_tools is False


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAINSTORMBUDDY_DATA_DIR", "custom_projects")
    monkeypatch.setenv("BRAINSTORMBUDDY_EXPORTS_DIR", "custom_exports")
    monkeypatch.setenv("BRAINSTORMBUDDY_LOG_DIR", "custom_logs")
    monkeypatch.setenv("BRAINSTORMBUDDY_ENABLE_WEB_TOOLS", "true")

    settings = Settings()
    assert settings.data_dir == "custom_projects"
    assert settings.exports_dir == "custom_exports"
    assert settings.log_dir == "custom_logs"
    assert settings.enable_web_tools is True


def test_partial_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAINSTORMBUDDY_DATA_DIR", "override_data")

    settings = Settings()
    assert settings.data_dir == "override_data"
    assert settings.exports_dir == "exports"
    assert settings.log_dir == "logs"
    assert settings.enable_web_tools is False


def test_load_settings_singleton() -> None:
    settings1 = load_settings()
    settings2 = load_settings()
    assert settings1 is settings2


def test_load_settings_returns_settings_instance() -> None:
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert settings.data_dir == "projects"
    assert settings.exports_dir == "exports"
    assert settings.log_dir == "logs"
    assert settings.enable_web_tools is False
````

## File: tests/test_llm_fake.py
````python
"""Unit tests for FakeClaudeClient implementation."""

import pytest

from app.llm.claude_client import (
    Event,
    FakeClaudeClient,
    MessageDone,
    TextDelta,
)


@pytest.mark.asyncio
async def test_fake_client_yields_events_in_order() -> None:
    """Test that FakeClaudeClient yields events in the expected order."""
    client = FakeClaudeClient()
    events: list[Event] = []

    async for event in client.stream("test prompt"):
        events.append(event)

    assert len(events) == 3
    assert isinstance(events[0], TextDelta)
    assert events[0].text == "First chunk of text"
    assert isinstance(events[1], TextDelta)
    assert events[1].text == "Second chunk of text"
    assert isinstance(events[2], MessageDone)


@pytest.mark.asyncio
async def test_fake_client_accepts_all_parameters() -> None:
    """Test that FakeClaudeClient accepts all expected parameters."""
    client = FakeClaudeClient()
    events: list[Event] = []

    async for event in client.stream(
        prompt="test prompt",
        system_prompt="system context",
        allowed_tools=["tool1", "tool2"],
        denied_tools=["tool3"],
        permission_mode="restricted",
        cwd="/test/path",
    ):
        events.append(event)

    assert len(events) == 3
    assert all(isinstance(e, TextDelta | MessageDone) for e in events)


@pytest.mark.asyncio
async def test_event_types_are_frozen() -> None:
    """Test that Event dataclasses are frozen and immutable."""
    delta = TextDelta("test")
    done = MessageDone()

    with pytest.raises(AttributeError):
        delta.text = "modified"  # type: ignore

    with pytest.raises(AttributeError):
        done.extra = "field"  # type: ignore


@pytest.mark.asyncio
async def test_stream_can_be_consumed_multiple_times() -> None:
    """Test that the stream method can be called multiple times."""
    client = FakeClaudeClient()

    first_run = [event async for event in client.stream("prompt1")]
    second_run = [event async for event in client.stream("prompt2")]

    assert len(first_run) == 3
    assert len(second_run) == 3
    assert first_run[0] == second_run[0]  # Same deterministic output
````

## File: tests/test_scaffold.py
````python
"""Tests for the project scaffold utility."""

import tempfile
from pathlib import Path

import yaml

from app.files.scaffold import ensure_project_exists, scaffold_project


class TestScaffoldProject:
    """Test suite for scaffold_project function."""

    def test_creates_directory_structure(self) -> None:
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            # Verify project directory exists
            assert project_path.exists()
            assert project_path.is_dir()
            assert project_path == base / "test-project"

            # Verify subdirectories exist
            assert (project_path / "elements").exists()
            assert (project_path / "elements").is_dir()
            assert (project_path / "research").exists()
            assert (project_path / "research").is_dir()
            assert (project_path / "exports").exists()
            assert (project_path / "exports").is_dir()

    def test_creates_seed_files(self) -> None:
        """Test that all required seed files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            # Verify files exist
            assert (project_path / "project.yaml").exists()
            assert (project_path / "kernel.md").exists()
            assert (project_path / "outline.md").exists()

            # Verify files are not empty
            assert (project_path / "project.yaml").stat().st_size > 0
            assert (project_path / "kernel.md").stat().st_size > 0
            assert (project_path / "outline.md").stat().st_size > 0

    def test_project_yaml_content(self) -> None:
        """Test that project.yaml has correct structure and content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            with open(project_path / "project.yaml", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            assert data["name"] == "test-project"
            assert "created" in data
            assert data["stage"] == "capture"
            assert "description" in data
            assert isinstance(data["tags"], list)
            assert data["metadata"]["version"] == "1.0.0"
            assert data["metadata"]["format"] == "brainstormbuddy-project"

    def test_kernel_md_content(self) -> None:
        """Test that kernel.md has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            content = (project_path / "kernel.md").read_text(encoding="utf-8")

            # Check frontmatter
            assert "---" in content
            assert "title: Kernel" in content
            assert "project: test-project" in content
            assert "stage: kernel" in content

            # Check main headers
            assert "# Kernel" in content
            assert "## Core Concept" in content
            assert "## Key Questions" in content
            assert "## Success Criteria" in content

    def test_outline_md_content(self) -> None:
        """Test that outline.md has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            content = (project_path / "outline.md").read_text(encoding="utf-8")

            # Check frontmatter
            assert "---" in content
            assert "title: Outline" in content
            assert "project: test-project" in content
            assert "stage: outline" in content

            # Check main headers
            assert "# Outline" in content
            assert "## Executive Summary" in content
            assert "## Main Sections" in content
            assert "### Section 1" in content
            assert "## Next Steps" in content

    def test_idempotency(self) -> None:
        """Test that running scaffold_project twice doesn't cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # First run
            project_path1 = scaffold_project("test-project", base)

            # Get initial file modification times
            yaml_mtime1 = (project_path1 / "project.yaml").stat().st_mtime
            kernel_mtime1 = (project_path1 / "kernel.md").stat().st_mtime
            outline_mtime1 = (project_path1 / "outline.md").stat().st_mtime

            # Second run (should not error)
            project_path2 = scaffold_project("test-project", base)

            # Paths should be the same
            assert project_path1 == project_path2

            # Files should not be modified (times should be the same)
            yaml_mtime2 = (project_path2 / "project.yaml").stat().st_mtime
            kernel_mtime2 = (project_path2 / "kernel.md").stat().st_mtime
            outline_mtime2 = (project_path2 / "outline.md").stat().st_mtime

            assert yaml_mtime1 == yaml_mtime2
            assert kernel_mtime1 == kernel_mtime2
            assert outline_mtime1 == outline_mtime2

    def test_idempotency_preserves_content(self) -> None:
        """Test that re-running doesn't overwrite existing content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # First run
            project_path = scaffold_project("test-project", base)

            # Modify a file
            kernel_path = project_path / "kernel.md"
            custom_content = "# Custom Kernel Content\n\nThis was modified."
            kernel_path.write_text(custom_content, encoding="utf-8")

            # Second run
            scaffold_project("test-project", base)

            # Content should be preserved
            assert kernel_path.read_text(encoding="utf-8") == custom_content

    def test_string_base_path(self) -> None:
        """Test that base can be provided as a string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = scaffold_project("test-project", tmpdir)

            assert project_path.exists()
            assert project_path.parent == Path(tmpdir)

    def test_path_base_path(self) -> None:
        """Test that base can be provided as a Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            project_path = scaffold_project("test-project", base)

            assert project_path.exists()
            assert project_path.parent == base

    def test_nested_base_path(self) -> None:
        """Test creating projects in nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "nested" / "projects"
            project_path = scaffold_project("test-project", base)

            assert project_path.exists()
            assert project_path.parent == base
            assert base.exists()

    def test_ensure_project_exists_alias(self) -> None:
        """Test that ensure_project_exists works as an alias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            path1 = ensure_project_exists("test-project", base)
            path2 = scaffold_project("test-project", base)

            assert path1 == path2
            assert path1.exists()

    def test_multiple_projects(self) -> None:
        """Test creating multiple projects in the same base directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            project1 = scaffold_project("project-one", base)
            project2 = scaffold_project("project-two", base)

            assert project1.exists()
            assert project2.exists()
            assert project1 != project2
            assert project1.name == "project-one"
            assert project2.name == "project-two"

    def test_slug_with_special_characters(self) -> None:
        """Test that slugs with hyphens and underscores work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            project1 = scaffold_project("my-cool-project", base)
            project2 = scaffold_project("my_cool_project", base)

            assert project1.exists()
            assert project2.exists()
            assert project1.name == "my-cool-project"
            assert project2.name == "my_cool_project"
````

## File: .gitignore
````
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# poetry
poetry.lock

# pdm
.pdm.toml
.pdm-python
.pdm-build/

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# IDE
.idea/
.vscode/
*.swp
*.swo
*.kate-swp

# Project specific
projects/
exports/
.claude/
````

## File: app/llm/claude_client.py
````python
"""Claude client interface with streaming support and fake implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass


@dataclass(frozen=True)
class TextDelta:
    """Represents a text chunk in the stream."""

    text: str


@dataclass(frozen=True)
class ToolUseStart:
    """Indicates the start of tool usage."""

    tool_name: str
    tool_id: str


@dataclass(frozen=True)
class ToolUseEnd:
    """Indicates the end of tool usage."""

    tool_id: str
    result: str | None = None


@dataclass(frozen=True)
class MessageDone:
    """Indicates the message stream is complete."""

    pass


Event = TextDelta | ToolUseStart | ToolUseEnd | MessageDone


class ClaudeClient(ABC):
    """Abstract interface for Claude API clients."""

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        allowed_tools: list[str] | None = None,
        denied_tools: list[str] | None = None,
        permission_mode: str = "standard",
        cwd: str | None = None,
    ) -> AsyncGenerator[Event, None]:
        """
        Stream events from Claude API.

        Args:
            prompt: User prompt to send to Claude
            system_prompt: Optional system prompt to set context
            allowed_tools: List of allowed tool names
            denied_tools: List of denied tool names
            permission_mode: Permission mode for tool usage
            cwd: Current working directory for tool execution

        Yields:
            Event objects representing stream chunks
        """
        raise NotImplementedError
        yield  # pragma: no cover


class FakeClaudeClient(ClaudeClient):
    """Fake implementation for testing with deterministic output."""

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        allowed_tools: list[str] | None = None,
        denied_tools: list[str] | None = None,
        permission_mode: str = "standard",
        cwd: str | None = None,
    ) -> AsyncGenerator[Event, None]:
        """Yield a deterministic sequence of events for testing."""
        # Parameters are intentionally unused in fake implementation
        _ = (prompt, system_prompt, allowed_tools, denied_tools, permission_mode, cwd)
        yield TextDelta("First chunk of text")
        yield TextDelta("Second chunk of text")
        yield MessageDone()
````

## File: app/llm/sessions.py
````python
"""Session policy registry for stage-gated tool permissions and prompts."""

from dataclasses import dataclass
from pathlib import Path

from app.core.config import load_settings


@dataclass(frozen=True)
class SessionPolicy:
    """Configuration for a brainstorming session stage."""

    stage: str
    system_prompt_path: Path
    allowed_tools: list[str]
    denied_tools: list[str]
    write_roots: list[str]
    permission_mode: str
    web_tools_allowed: list[str]


def get_policy(stage: str) -> SessionPolicy:
    """
    Get the policy configuration for a given stage.

    Args:
        stage: One of 'clarify', 'kernel', 'outline', 'research', 'synthesis'

    Returns:
        SessionPolicy with appropriate configuration

    Raises:
        ValueError: If stage is not recognized
    """
    settings = load_settings()
    base_prompt_path = Path(__file__).resolve().parent / "prompts"

    policies = {
        "clarify": SessionPolicy(
            stage="clarify",
            system_prompt_path=base_prompt_path / "clarify.md",
            allowed_tools=["Read"],
            denied_tools=["Write", "Edit", "Bash", "WebSearch", "WebFetch"],
            write_roots=[],
            permission_mode="readonly",
            web_tools_allowed=[],
        ),
        "kernel": SessionPolicy(
            stage="kernel",
            system_prompt_path=base_prompt_path / "kernel.md",
            allowed_tools=["Read", "Write", "Edit"],
            denied_tools=["Bash", "WebSearch", "WebFetch"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=[],
        ),
        "outline": SessionPolicy(
            stage="outline",
            system_prompt_path=base_prompt_path / "outline.md",
            allowed_tools=["Read", "Write", "Edit"],
            denied_tools=["Bash", "WebSearch", "WebFetch"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=[],
        ),
        "research": SessionPolicy(
            stage="research",
            system_prompt_path=base_prompt_path / "research.md",
            allowed_tools=(
                ["Read", "Write", "Edit", "WebSearch", "WebFetch"]
                if settings.enable_web_tools
                else ["Read", "Write", "Edit"]
            ),
            denied_tools=["Bash"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=["WebSearch", "WebFetch"] if settings.enable_web_tools else [],
        ),
        "synthesis": SessionPolicy(
            stage="synthesis",
            system_prompt_path=base_prompt_path / "synthesis.md",
            allowed_tools=["Read", "Write", "Edit"],
            denied_tools=["Bash", "WebSearch", "WebFetch"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=[],
        ),
    }

    if stage not in policies:
        raise ValueError(f"Unknown stage: {stage}. Valid stages are: {', '.join(policies.keys())}")

    return policies[stage]
````

## File: app/permissions/settings_writer.py
````python
"""Settings writer for Claude project configuration."""

import json
from pathlib import Path
from typing import Any


def write_project_settings(repo_root: Path = Path(".")) -> None:
    """
    Write Claude project settings with deny-first permissions and hook configuration.

    Args:
        repo_root: Root directory of the repository (default: current directory)
    """
    repo_root = Path(repo_root)
    claude_dir = repo_root / ".claude"
    hooks_dir = claude_dir / "hooks"

    # Ensure directories exist
    claude_dir.mkdir(exist_ok=True)
    hooks_dir.mkdir(exist_ok=True)

    # Define settings structure
    settings: dict[str, Any] = {
        "permissions": {
            "allow": ["Read", "Edit", "Write"],
            "deny": ["Bash", "WebSearch", "WebFetch"],
            "denyPaths": [".env*", "secrets/**", ".git/**"],
            "writeRoots": ["projects/**", "exports/**"],
        },
        "hooks": {
            "PreToolUse": ".claude/hooks/gate.py",
            "PostToolUse": ".claude/hooks/format_md.py",
        },
    }

    # Write settings.json
    settings_path = claude_dir / "settings.json"
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")  # Add trailing newline

    # Create hook stub files
    _create_hook_stub(hooks_dir / "gate.py", "PreToolUse")
    _create_hook_stub(hooks_dir / "format_md.py", "PostToolUse")


def _create_hook_stub(hook_path: Path, hook_type: str) -> None:
    """
    Create a placeholder hook file with TODO content.

    Args:
        hook_path: Path to the hook file
        hook_type: Type of hook (PreToolUse or PostToolUse)
    """
    hook_content = f'''#!/usr/bin/env python3
"""Claude {hook_type} hook."""

# TODO: Implement {hook_type} hook logic
# This hook is called {hook_type.lower().replace("tool", " tool ")}

def main():
    """Main hook entry point."""
    pass


if __name__ == "__main__":
    main()
'''

    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(hook_content)

    # Make the hook executable (Python will handle this cross-platform)
    hook_path.chmod(0o755)
````

## File: app/tui/views/__init__.py
````python
"""View modules for the TUI application."""

from .main_screen import MainScreen

__all__ = ["MainScreen"]
````

## File: app/tui/__init__.py
````python
"""TUI module for Brainstorm Buddy."""
````

## File: app/__init__.py
````python
"""Brainstorm Buddy - Python terminal-first brainstorming app."""

__version__ = "0.1.0"
````

## File: tests/test_policies.py
````python
"""Unit tests for session policy registry."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.llm.sessions import SessionPolicy, get_policy


def test_get_policy_clarify() -> None:
    """Test clarify stage policy configuration."""
    policy = get_policy("clarify")

    assert policy.stage == "clarify"
    assert "app/llm/prompts/clarify.md" in str(policy.system_prompt_path)
    assert policy.allowed_tools == ["Read"]
    assert set(policy.denied_tools) == {"Write", "Edit", "Bash", "WebSearch", "WebFetch"}
    assert policy.write_roots == []
    assert policy.permission_mode == "readonly"
    assert policy.web_tools_allowed == []


def test_get_policy_kernel() -> None:
    """Test kernel stage policy configuration."""
    policy = get_policy("kernel")

    assert policy.stage == "kernel"
    assert "app/llm/prompts/kernel.md" in str(policy.system_prompt_path)
    assert set(policy.allowed_tools) == {"Read", "Write", "Edit"}
    assert set(policy.denied_tools) == {"Bash", "WebSearch", "WebFetch"}
    assert policy.write_roots == ["projects/**"]
    assert policy.permission_mode == "restricted"
    assert policy.web_tools_allowed == []


def test_get_policy_outline() -> None:
    """Test outline stage policy configuration."""
    policy = get_policy("outline")

    assert policy.stage == "outline"
    assert "app/llm/prompts/outline.md" in str(policy.system_prompt_path)
    assert set(policy.allowed_tools) == {"Read", "Write", "Edit"}
    assert set(policy.denied_tools) == {"Bash", "WebSearch", "WebFetch"}
    assert policy.write_roots == ["projects/**"]
    assert policy.permission_mode == "restricted"
    assert policy.web_tools_allowed == []


def test_get_policy_research_with_web_disabled() -> None:
    """Test research stage policy with web tools disabled."""
    with patch("app.llm.sessions.load_settings") as mock_settings:
        mock_settings.return_value.enable_web_tools = False
        policy = get_policy("research")

    assert policy.stage == "research"
    assert "app/llm/prompts/research.md" in str(policy.system_prompt_path)
    assert set(policy.allowed_tools) == {"Read", "Write", "Edit"}
    assert "Bash" in policy.denied_tools
    assert policy.write_roots == ["projects/**"]
    assert policy.permission_mode == "restricted"
    assert policy.web_tools_allowed == []


def test_get_policy_research_with_web_enabled() -> None:
    """Test research stage policy with web tools enabled."""
    with patch("app.llm.sessions.load_settings") as mock_settings:
        mock_settings.return_value.enable_web_tools = True
        policy = get_policy("research")

    assert policy.stage == "research"
    assert "app/llm/prompts/research.md" in str(policy.system_prompt_path)
    assert set(policy.allowed_tools) == {"Read", "Write", "Edit", "WebSearch", "WebFetch"}
    assert "Bash" in policy.denied_tools
    assert policy.write_roots == ["projects/**"]
    assert policy.permission_mode == "restricted"
    assert set(policy.web_tools_allowed) == {"WebSearch", "WebFetch"}


def test_get_policy_synthesis() -> None:
    """Test synthesis stage policy configuration."""
    policy = get_policy("synthesis")

    assert policy.stage == "synthesis"
    assert "app/llm/prompts/synthesis.md" in str(policy.system_prompt_path)
    assert set(policy.allowed_tools) == {"Read", "Write", "Edit"}
    assert set(policy.denied_tools) == {"Bash", "WebSearch", "WebFetch"}
    assert policy.write_roots == ["projects/**"]
    assert policy.permission_mode == "restricted"
    assert policy.web_tools_allowed == []


def test_get_policy_invalid_stage() -> None:
    """Test that invalid stage raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        get_policy("invalid_stage")

    assert "Unknown stage: invalid_stage" in str(exc_info.value)
    assert "Valid stages are:" in str(exc_info.value)


def test_session_policy_is_frozen() -> None:
    """Test that SessionPolicy is immutable."""
    policy = SessionPolicy(
        stage="test",
        system_prompt_path=Path("test.md"),
        allowed_tools=[],
        denied_tools=[],
        write_roots=[],
        permission_mode="test",
        web_tools_allowed=[],
    )

    with pytest.raises(AttributeError):
        policy.stage = "modified"  # type: ignore


def test_policies_have_correct_prompt_paths() -> None:
    """Test that all policies have correctly formed prompt paths."""
    stages = ["clarify", "kernel", "outline", "research", "synthesis"]

    for stage in stages:
        policy = get_policy(stage)
        assert policy.system_prompt_path.suffix == ".md"
        assert "app/llm/prompts" in str(policy.system_prompt_path)
        # Note: synthesis and research stages use prompts that don't exist yet
        # but the paths should still be correctly formed
````

## File: tests/test_settings_writer.py
````python
"""Tests for Claude settings writer."""

import json
from pathlib import Path

from app.permissions.settings_writer import write_project_settings


def test_write_project_settings_creates_structure(tmp_path: Path) -> None:
    """Test that write_project_settings creates the expected file structure."""
    # Run the settings writer
    write_project_settings(repo_root=tmp_path)

    # Check that directories exist
    assert (tmp_path / ".claude").exists()
    assert (tmp_path / ".claude" / "hooks").exists()

    # Check that settings.json exists
    settings_path = tmp_path / ".claude" / "settings.json"
    assert settings_path.exists()

    # Check that hook files exist
    assert (tmp_path / ".claude" / "hooks" / "gate.py").exists()
    assert (tmp_path / ".claude" / "hooks" / "format_md.py").exists()


def test_settings_json_has_correct_structure(tmp_path: Path) -> None:
    """Test that settings.json contains the expected structure."""
    write_project_settings(repo_root=tmp_path)

    settings_path = tmp_path / ".claude" / "settings.json"
    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)

    # Check permissions structure
    assert "permissions" in settings
    assert "allow" in settings["permissions"]
    assert "deny" in settings["permissions"]
    assert "denyPaths" in settings["permissions"]
    assert "writeRoots" in settings["permissions"]

    # Check allowed tools
    assert set(settings["permissions"]["allow"]) == {"Read", "Edit", "Write"}

    # Check denied tools
    assert set(settings["permissions"]["deny"]) == {"Bash", "WebSearch", "WebFetch"}

    # Check denied paths
    assert ".env*" in settings["permissions"]["denyPaths"]
    assert "secrets/**" in settings["permissions"]["denyPaths"]
    assert ".git/**" in settings["permissions"]["denyPaths"]

    # Check write roots
    assert "projects/**" in settings["permissions"]["writeRoots"]
    assert "exports/**" in settings["permissions"]["writeRoots"]


def test_hooks_configuration(tmp_path: Path) -> None:
    """Test that hooks are correctly configured in settings.json."""
    write_project_settings(repo_root=tmp_path)

    settings_path = tmp_path / ".claude" / "settings.json"
    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)

    # Check hooks structure
    assert "hooks" in settings
    assert "PreToolUse" in settings["hooks"]
    assert "PostToolUse" in settings["hooks"]

    # Check hook paths
    assert settings["hooks"]["PreToolUse"] == ".claude/hooks/gate.py"
    assert settings["hooks"]["PostToolUse"] == ".claude/hooks/format_md.py"


def test_hook_files_have_content(tmp_path: Path) -> None:
    """Test that hook files contain placeholder content."""
    write_project_settings(repo_root=tmp_path)

    gate_hook = tmp_path / ".claude" / "hooks" / "gate.py"
    format_hook = tmp_path / ".claude" / "hooks" / "format_md.py"

    # Check gate.py content
    with open(gate_hook, encoding="utf-8") as f:
        gate_content = f.read()
    assert "PreToolUse" in gate_content
    assert "TODO" in gate_content
    assert "def main():" in gate_content

    # Check format_md.py content
    with open(format_hook, encoding="utf-8") as f:
        format_content = f.read()
    assert "PostToolUse" in format_content
    assert "TODO" in format_content
    assert "def main():" in format_content


def test_hook_files_are_executable(tmp_path: Path) -> None:
    """Test that hook files have executable permissions."""
    write_project_settings(repo_root=tmp_path)

    gate_hook = tmp_path / ".claude" / "hooks" / "gate.py"
    format_hook = tmp_path / ".claude" / "hooks" / "format_md.py"

    # Check that files have execute permissions for owner
    assert gate_hook.stat().st_mode & 0o100
    assert format_hook.stat().st_mode & 0o100


def test_idempotent_operation(tmp_path: Path) -> None:
    """Test that running write_project_settings multiple times is safe."""
    # Run twice
    write_project_settings(repo_root=tmp_path)
    write_project_settings(repo_root=tmp_path)

    # Should not raise errors and files should still exist
    assert (tmp_path / ".claude" / "settings.json").exists()
    assert (tmp_path / ".claude" / "hooks" / "gate.py").exists()
    assert (tmp_path / ".claude" / "hooks" / "format_md.py").exists()
````

## File: tests/test_smoke.py
````python
"""Smoke tests to verify basic imports and structure."""


def test_app_imports() -> None:
    """Test that the app module can be imported."""
    import app

    assert app is not None
    assert hasattr(app, "__version__")


def test_tui_app_imports() -> None:
    """Test that the TUI app can be imported."""
    from app.tui import app as tui_module
    from app.tui.app import BrainstormBuddyApp

    assert tui_module is not None
    assert BrainstormBuddyApp is not None
    assert hasattr(BrainstormBuddyApp, "TITLE")
    assert BrainstormBuddyApp.TITLE == "Brainstorm Buddy"
````

## File: tests/test_tui_imports.py
````python
"""Import tests for TUI modules to ensure no import errors."""


def test_tui_app_imports() -> None:
    """Test that the main TUI app module imports successfully."""
    from app.tui.app import BrainstormBuddyApp, main  # noqa: F401

    assert BrainstormBuddyApp is not None
    assert main is not None


def test_tui_views_imports() -> None:
    """Test that all view modules import successfully."""
    from app.tui.views import MainScreen  # noqa: F401
    from app.tui.views.main_screen import MainScreen as MS  # noqa: F401

    assert MainScreen is MS


def test_tui_widgets_imports() -> None:
    """Test that all widget modules import successfully."""
    from app.tui.widgets import (  # noqa: F401
        CommandPalette,
        ContextPanel,
        FileTree,
        SessionViewer,
    )
    from app.tui.widgets.command_palette import CommandPalette as CP  # noqa: F401
    from app.tui.widgets.context_panel import ContextPanel as CTX  # noqa: F401
    from app.tui.widgets.file_tree import FileTree as FT  # noqa: F401
    from app.tui.widgets.session_viewer import SessionViewer as SV  # noqa: F401

    assert CommandPalette is CP
    assert ContextPanel is CTX
    assert FileTree is FT
    assert SessionViewer is SV


def test_widget_instantiation() -> None:
    """Test that widgets can be instantiated without errors."""
    from app.tui.widgets import (
        CommandPalette,
        ContextPanel,
        FileTree,
        SessionViewer,
    )

    # Create instances to ensure no initialization errors
    file_tree = FileTree()
    session_viewer = SessionViewer()
    context_panel = ContextPanel()
    command_palette = CommandPalette()

    assert file_tree is not None
    assert session_viewer is not None
    assert context_panel is not None
    assert command_palette is not None
````

## File: .pre-commit-config.yaml
````yaml
# See https://pre-commit.com for more information
# See https://pre-commit.com/hooks.html for more hooks
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    # Ruff version.
    rev: v0.7.0
    hooks:
      # Run the linter.
      - id: ruff
        args: [--fix]
      # Run the formatter.
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: check-toml
      - id: debug-statements
      - id: mixed-line-ending
        args: ['--fix=lf']

# Optional: Add mypy hook (commented out by default as it can be slow)
# - repo: https://github.com/pre-commit/mirrors-mypy
#   rev: v1.13.0
#   hooks:
#     - id: mypy
#       additional_dependencies: [types-all]
#       args: [--strict, --ignore-missing-imports]
````

## File: app/files/diff.py
````python
"""Diff and patch utilities for atomic file operations."""

import difflib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Patch:
    """Represents a patch to be applied to a file."""

    original: str
    modified: str
    diff_lines: list[str]


def compute_patch(old: str, new: str) -> Patch:
    """
    Compute a patch representing the difference between two strings.

    Args:
        old: Original text content
        new: Modified text content

    Returns:
        Patch object containing the diff information
    """
    # Split into lines while preserving line endings
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    # Generate unified diff
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        lineterm="",
    )

    return Patch(
        original=old,
        modified=new,
        diff_lines=list(diff),
    )


def apply_patch(path: Path | str, patch: Patch) -> None:
    """
    Apply a patch to a file atomically using temp file and replace.

    This ensures the file is either fully updated or not modified at all,
    preventing partial writes in case of errors.

    Args:
        path: Path to the file to patch
        patch: Patch object to apply

    Raises:
        IOError: If there's an error during the atomic write operation
    """
    file_path = Path(path) if isinstance(path, str) else path

    # Precompute file mode if file exists
    file_mode = None
    if file_path.exists():
        file_mode = os.stat(file_path).st_mode

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary file first
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=file_path.parent,
        delete=False,
        suffix=".tmp",
    ) as tmp_file:
        tmp_file.write(patch.modified)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_path = Path(tmp_file.name)

    try:
        # Preserve file mode if original file existed
        if file_mode is not None:
            os.chmod(tmp_path, file_mode)

        # Atomically replace the original file
        tmp_path.replace(file_path)

        # Fsync parent directory for durability (best-effort)
        try:
            dfd = os.open(file_path.parent, os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:
            # Platform/filesystem doesn't support directory fsync
            pass
    except Exception:
        # Clean up temp file if replacement fails
        tmp_path.unlink(missing_ok=True)
        raise


def generate_diff_preview(
    old: str,
    new: str,
    context_lines: int = 3,
    from_label: str | None = None,
    to_label: str | None = None,
) -> str:
    """
    Generate a human-readable diff preview.

    Args:
        old: Original text content
        new: Modified text content
        context_lines: Number of context lines to show around changes
        from_label: Optional label for the original file (defaults to "before")
        to_label: Optional label for the modified file (defaults to "after")

    Returns:
        String representation of the diff suitable for display
    """
    # Split into lines while preserving line endings
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    # Generate unified diff with specified context
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=from_label if from_label is not None else "before",
        tofile=to_label if to_label is not None else "after",
        n=context_lines,
        lineterm="",
    )

    diff_lines = list(diff)

    if not diff_lines:
        return "No changes detected."

    # Join with newlines for readable output
    return "\n".join(diff_lines)


def is_unchanged(patch: Patch) -> bool:
    """
    Check if a patch represents no changes.

    Args:
        patch: Patch object to check

    Returns:
        True if the patch represents no changes, False otherwise
    """
    return patch.original == patch.modified or len(patch.diff_lines) == 0


def apply_patch_from_strings(path: Path | str, old_content: str, new_content: str) -> Patch | None:
    """
    Helper function to compute and apply a patch in one operation.

    Args:
        path: Path to the file to patch
        old_content: Expected current content (for verification)
        new_content: New content to write

    Returns:
        The applied Patch object, or None if no changes were needed

    Raises:
        ValueError: If the current file content doesn't match old_content
        IOError: If there's an error during the write operation
    """
    file_path = Path(path) if isinstance(path, str) else path

    # Read current content if file exists
    if file_path.exists():
        with open(file_path, encoding="utf-8") as f:
            current = f.read()
        if current != old_content:
            raise ValueError(f"Current content of {file_path} doesn't match expected old_content")

    # Compute patch
    patch = compute_patch(old_content, new_content)

    # Only apply if there are changes
    if not is_unchanged(patch):
        apply_patch(file_path, patch)
        return patch

    return None


def apply_patches(patches: list[tuple[Path | str, str, str]]) -> list[Patch]:
    """
    Apply multiple file edits atomically (all-or-nothing).

    This function ensures that either all patches are applied successfully,
    or none are applied at all. It writes all temporary files first, then
    replaces all targets atomically. On any failure, all temporary files
    are cleaned up and original files remain unchanged.

    Args:
        patches: List of tuples containing (path, old_content, new_content)

    Returns:
        List of Patch objects for each changed file

    Raises:
        IOError: If there's an error during the atomic write operations
        ValueError: If any file's current content doesn't match expected
    """
    # Prepare all patches and temp files
    temp_files: list[tuple[Path, Path, int | None, str, bool]] = []
    computed_patches: list[Patch] = []
    backup_files: list[tuple[Path, Path]] = []

    try:
        for path_input, old_content, new_content in patches:
            file_path = Path(path_input) if isinstance(path_input, str) else path_input

            # Track whether file existed before operation
            existed_before = file_path.exists()

            # Read and verify current content if file exists
            if existed_before:
                with open(file_path, encoding="utf-8") as f:
                    current = f.read()
                if current != old_content:
                    raise ValueError(
                        f"Current content of {file_path} doesn't match expected old_content"
                    )
                # Preserve file mode
                file_mode = os.stat(file_path).st_mode
            else:
                file_mode = None
                current = ""
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Compute patch
            patch = compute_patch(old_content, new_content)

            # Skip unchanged files
            if is_unchanged(patch):
                continue

            computed_patches.append(patch)

            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=file_path.parent,
                delete=False,
                suffix=".tmp",
            ) as tmp_file:
                tmp_file.write(new_content)
                tmp_path = Path(tmp_file.name)

            # Store temp file info for later replacement
            temp_files.append((file_path, tmp_path, file_mode, current, existed_before))

        # Create backups of existing files before replacement
        for target_path, _, _, original_content, existed_before in temp_files:
            if existed_before:
                # Create backup file
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=target_path.parent,
                    delete=False,
                    suffix=".backup",
                ) as backup_file:
                    backup_file.write(original_content)
                    backup_path = Path(backup_file.name)
                backup_files.append((target_path, backup_path))

        # Now replace all files
        completed_replacements = []
        try:
            for target_path, temp_path, file_mode, _, _ in temp_files:
                # Preserve file mode if it existed
                if file_mode is not None:
                    os.chmod(temp_path, file_mode)

                # Atomic replace
                temp_path.replace(target_path)
                completed_replacements.append(target_path)

        except Exception as e:
            # Restore original files from backups or remove newly created files
            for target_path in completed_replacements:
                # Find if this file existed before the operation
                existed_before = False
                for file_path, _, _, _, file_existed in temp_files:
                    if file_path == target_path:
                        existed_before = file_existed
                        break

                if existed_before:
                    # Find the backup for this file and restore it
                    for orig_path, backup_path in backup_files:
                        if orig_path == target_path:
                            backup_path.replace(target_path)
                            break
                else:
                    # File didn't exist before, remove it
                    target_path.unlink(missing_ok=True)

            # Clean up any remaining temp files
            for target_path, temp_path, _, _, _ in temp_files:
                if target_path not in completed_replacements:
                    temp_path.unlink(missing_ok=True)

            # Clean up backup files
            for _, backup_path in backup_files:
                backup_path.unlink(missing_ok=True)

            raise OSError(f"Failed to atomically replace files: {e}") from e

        # Success - clean up backup files
        for _, backup_path in backup_files:
            backup_path.unlink(missing_ok=True)

    except Exception:
        # Clean up any temp files created before the error
        for _, temp_path, _, _, _ in temp_files:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
        raise

    return computed_patches
````

## File: app/tui/app.py
````python
"""Textual App for Brainstorm Buddy with three-pane layout."""

from textual.app import App, ComposeResult
from textual.binding import Binding

from app.tui.views import MainScreen
from app.tui.widgets import CommandPalette


class BrainstormBuddyApp(App[None]):
    """Main Textual application for Brainstorm Buddy."""

    TITLE = "Brainstorm Buddy"
    SUB_TITLE = "Terminal-first brainstorming app"
    CSS_PATH = None  # Use default CSS from widgets

    BINDINGS = [
        Binding(":", "command_palette", "Command", priority=True),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app with three-pane layout."""
        yield MainScreen()

    def action_command_palette(self) -> None:
        """Show the command palette."""
        palette = self.query_one("#command-palette", CommandPalette)
        palette.show()


def main() -> None:
    """Run the Brainstorm Buddy app."""
    app = BrainstormBuddyApp()
    app.run()


if __name__ == "__main__":
    main()
````

## File: tests/test_diff.py
````python
"""Tests for diff and patch utilities."""

import os
from pathlib import Path
from unittest.mock import patch as mock_patch

import pytest

from app.files.diff import (
    apply_patch,
    apply_patch_from_strings,
    apply_patches,
    compute_patch,
    generate_diff_preview,
    is_unchanged,
)


def test_compute_patch_no_changes() -> None:
    """Test computing patch when content is unchanged."""
    content = "Hello\nWorld\n"
    patch = compute_patch(content, content)

    assert patch.original == content
    assert patch.modified == content
    assert is_unchanged(patch)


def test_compute_patch_with_changes() -> None:
    """Test computing patch with actual changes."""
    old = "Hello\nWorld\n"
    new = "Hello\nBeautiful\nWorld\n"
    patch = compute_patch(old, new)

    assert patch.original == old
    assert patch.modified == new
    assert not is_unchanged(patch)
    assert len(patch.diff_lines) > 0


def test_apply_patch_creates_new_file(tmp_path: Path) -> None:
    """Test applying patch to create a new file."""
    file_path = tmp_path / "test.md"
    content = "# Test Document\n\nThis is a test."

    patch = compute_patch("", content)
    apply_patch(file_path, patch)

    assert file_path.exists()
    with open(file_path, encoding="utf-8") as f:
        assert f.read() == content


def test_apply_patch_replaces_existing_file(tmp_path: Path) -> None:
    """Test applying patch to replace an existing file."""
    file_path = tmp_path / "test.md"
    old_content = "Old content"
    new_content = "New content"

    # Create initial file
    file_path.write_text(old_content)

    # Apply patch
    patch = compute_patch(old_content, new_content)
    apply_patch(file_path, patch)

    assert file_path.read_text() == new_content


def test_apply_patch_atomic_on_error(tmp_path: Path) -> None:
    """Test that apply_patch preserves original on replace failure."""
    # 1) Create file_path with "Original"
    file_path = tmp_path / "test.md"
    file_path.write_text("Original")

    # 2) Compute patch "Original" -> "New content"
    patch = compute_patch("Original", "New content")

    # 3) Monkeypatch Path.replace to raise PermissionError
    def mock_replace_failure(self: Path, target: Path) -> None:  # noqa: ARG001
        raise PermissionError("Simulated replace failure")

    # 4) Call apply_patch inside pytest.raises
    with mock_patch.object(Path, "replace", mock_replace_failure):
        with pytest.raises(PermissionError) as exc_info:
            apply_patch(file_path, patch)

        assert "Simulated replace failure" in str(exc_info.value)

    # 5) Assert file still contains "Original"
    assert file_path.read_text() == "Original"

    # 6) Assert no *.tmp files remain in parent directory
    temp_files = list(tmp_path.glob("*.tmp"))
    assert len(temp_files) == 0


def test_generate_diff_preview() -> None:
    """Test generating human-readable diff preview."""
    old = "Line 1\nLine 2\nLine 3\n"
    new = "Line 1\nModified Line 2\nLine 3\n"

    preview = generate_diff_preview(old, new)

    assert "Line 2" in preview
    assert "Modified Line 2" in preview
    assert "-" in preview  # Removal indicator
    assert "+" in preview  # Addition indicator
    # Verify line breaks are present
    assert "\n" in preview
    lines = preview.split("\n")
    assert len(lines) > 1  # Should have multiple lines


def test_generate_diff_preview_no_changes() -> None:
    """Test diff preview when there are no changes."""
    content = "Same content"
    preview = generate_diff_preview(content, content)

    assert preview == "No changes detected."


def test_is_unchanged() -> None:
    """Test the is_unchanged helper function."""
    # Test with identical content
    patch1 = compute_patch("same", "same")
    assert is_unchanged(patch1)

    # Test with different content
    patch2 = compute_patch("old", "new")
    assert not is_unchanged(patch2)


def test_apply_patch_from_strings_success(tmp_path: Path) -> None:
    """Test the helper function for applying patches from strings."""
    file_path = tmp_path / "test.md"
    old_content = "Original\n"
    new_content = "Modified\n"

    # Create initial file
    file_path.write_text(old_content)

    # Apply patch
    patch = apply_patch_from_strings(file_path, old_content, new_content)

    assert patch is not None
    assert file_path.read_text() == new_content


def test_apply_patch_from_strings_no_changes(tmp_path: Path) -> None:
    """Test that no patch is applied when content is unchanged."""
    file_path = tmp_path / "test.md"
    content = "Same content\n"

    file_path.write_text(content)
    patch = apply_patch_from_strings(file_path, content, content)

    assert patch is None
    assert file_path.read_text() == content


def test_apply_patch_from_strings_content_mismatch(tmp_path: Path) -> None:
    """Test that ValueError is raised when current content doesn't match expected."""
    file_path = tmp_path / "test.md"
    file_path.write_text("Actual content")

    with pytest.raises(ValueError) as exc_info:
        apply_patch_from_strings(file_path, "Expected content", "New content")

    assert "doesn't match expected old_content" in str(exc_info.value)


def test_apply_patch_creates_parent_directories(tmp_path: Path) -> None:
    """Test that apply_patch creates parent directories if they don't exist."""
    file_path = tmp_path / "nested" / "dir" / "test.md"
    content = "Test content"

    patch = compute_patch("", content)
    apply_patch(file_path, patch)

    assert file_path.exists()
    assert file_path.read_text() == content


def test_multi_line_diff() -> None:
    """Test diff computation with multi-line changes."""
    old = """# Document

First paragraph.

Second paragraph.

Third paragraph.
"""
    new = """# Document

First paragraph.

Modified second paragraph with more text.

Third paragraph.

Fourth paragraph added.
"""

    patch = compute_patch(old, new)
    assert not is_unchanged(patch)

    preview = generate_diff_preview(old, new)
    assert "Modified second paragraph" in preview
    assert "Fourth paragraph added" in preview


def test_generate_diff_preview_context_lines() -> None:
    """Test that context_lines parameter affects the diff output."""
    old = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\n"
    new = "Line 1\nLine 2\nLine 3\nModified Line 4\nLine 5\nLine 6\nLine 7\nLine 8\n"

    # Test with different context sizes
    preview_small = generate_diff_preview(old, new, context_lines=1)
    preview_large = generate_diff_preview(old, new, context_lines=3)

    # Both should contain the change
    assert "Modified Line 4" in preview_small
    assert "Modified Line 4" in preview_large

    # Larger context should include more surrounding lines
    lines_small = preview_small.split("\n")
    lines_large = preview_large.split("\n")

    # The larger context should have more lines
    # (accounting for header lines and the actual diff content)
    assert len(lines_large) >= len(lines_small)


def test_generate_diff_preview_with_labels() -> None:
    """Test that custom labels appear in the diff header."""
    old = "A\n"
    new = "B\n"

    # Call with custom labels
    preview = generate_diff_preview(
        old, new, context_lines=1, from_label="old.md", to_label="new.md"
    )

    # Assert the preview contains the custom labels
    assert "--- old.md" in preview
    assert "+++ new.md" in preview

    # Ensure both "-" (deletion) and "+" (addition) markers appear
    assert "-A" in preview
    assert "+B" in preview


def test_apply_patches_success(tmp_path: Path) -> None:
    """Test successful multi-file patch application."""
    # Create initial files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file3 = tmp_path / "nested" / "file3.txt"

    file1.write_text("Original content 1")
    file2.write_text("Original content 2")
    # file3 doesn't exist yet - will be created

    # Prepare patches
    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "Original content 1", "Modified content 1"),
        (file2, "Original content 2", "Modified content 2"),
        (file3, "", "New file content 3"),  # New file
    ]

    # Apply patches
    results = apply_patches(patches_list)

    # Verify all files were updated
    assert len(results) == 3
    assert file1.read_text() == "Modified content 1"
    assert file2.read_text() == "Modified content 2"
    assert file3.exists()
    assert file3.read_text() == "New file content 3"

    # Verify patch objects
    for patch in results:
        assert not is_unchanged(patch)


def test_apply_patches_rollback_on_failure(tmp_path: Path) -> None:
    """Test that all files remain unchanged when any replacement fails."""
    # Create initial files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    file1.write_text("Original content 1")
    file2.write_text("Original content 2")

    original1 = file1.read_text()
    original2 = file2.read_text()

    # Prepare patches
    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "Original content 1", "Modified content 1"),
        (file2, "Original content 2", "Modified content 2"),
    ]

    # Mock Path.replace to fail on the second file
    call_count = 0
    original_replace = Path.replace

    def mock_replace(self: Path, target: Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise PermissionError("Simulated failure on second file")
        original_replace(self, target)

    with mock_patch.object(Path, "replace", mock_replace):
        with pytest.raises(IOError) as exc_info:
            apply_patches(patches_list)

        assert "Failed to atomically replace files" in str(exc_info.value)

    # Verify original files are unchanged
    assert file1.read_text() == original1
    assert file2.read_text() == original2

    # Verify no temp files left behind
    temp_files = list(tmp_path.glob("*.tmp"))
    assert len(temp_files) == 0


def test_apply_patch_atomic_failure(tmp_path: Path) -> None:
    """Test that apply_patch cleans temp and preserves original on replace failure."""
    file_path = tmp_path / "test.txt"
    original_content = "Original content"
    new_content = "New content"

    # Create initial file
    file_path.write_text(original_content)

    # Create a patch
    patch = compute_patch(original_content, new_content)

    # Mock Path.replace to raise an exception
    def mock_replace_error(self: Path, target: Path) -> None:  # noqa: ARG001
        raise PermissionError("Simulated replace failure")

    with mock_patch.object(Path, "replace", mock_replace_error):
        with pytest.raises(PermissionError) as exc_info:
            apply_patch(file_path, patch)

        assert "Simulated replace failure" in str(exc_info.value)

    # Verify original file is unchanged
    assert file_path.read_text() == original_content

    # Verify no temp files left behind
    temp_files = list(tmp_path.glob("*.tmp"))
    assert len(temp_files) == 0


def test_apply_patches_rollback_removes_new_files(tmp_path: Path) -> None:
    """Test that rollback removes files that didn't exist before the batch operation."""
    # Create file1 with content "Orig1"
    file1 = tmp_path / "file1.txt"
    file1.write_text("Orig1")

    # Do NOT create file2 (it will be new)
    file2 = tmp_path / "file2.txt"

    # Prepare patches
    patches_list: list[tuple[Path | str, str, str]] = [
        (file1, "Orig1", "Mod1"),  # Modify existing file
        (file2, "", "New2"),  # Create new file
    ]

    # Monkeypatch Path.replace to succeed on first, fail on second
    call_count = 0
    original_replace = Path.replace

    def mock_replace(self: Path, target: Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise PermissionError("Simulated failure on second replace")
        original_replace(self, target)

    # Act: call apply_patches and assert it raises OSError
    with mock_patch.object(Path, "replace", mock_replace):
        with pytest.raises(OSError) as exc_info:
            apply_patches(patches_list)

        assert "Failed to atomically replace files" in str(exc_info.value)

    # Assert file1 content remains "Orig1"
    assert file1.read_text() == "Orig1"

    # Assert file2 does not exist (it must be removed)
    assert not file2.exists()

    # Assert no *.tmp or *.backup files remain in tmp_path
    temp_files = list(tmp_path.glob("*.tmp"))
    backup_files = list(tmp_path.glob("*.backup"))
    assert len(temp_files) == 0
    assert len(backup_files) == 0


@pytest.mark.skipif(os.name == "nt", reason="chmod semantics differ on Windows")
def test_apply_patch_preserves_mode(tmp_path: Path) -> None:
    """Test that apply_patch preserves file mode on POSIX systems."""
    # Create a file with mode 0o744 and content "Old"
    file_path = tmp_path / "test.txt"
    file_path.write_text("Old")
    os.chmod(file_path, 0o744)

    # Verify initial mode
    initial_mode = os.stat(file_path).st_mode & 0o777
    assert initial_mode == 0o744

    # Compute patch for "Old" -> "New"
    patch = compute_patch("Old", "New")

    # Apply patch
    apply_patch(file_path, patch)

    # Assert file content changed
    assert file_path.read_text() == "New"

    # Assert file mode is preserved
    final_mode = os.stat(file_path).st_mode & 0o777
    assert final_mode == 0o744
````

## File: pyproject.toml
````toml
[tool.poetry]
name = "brainstormbuddy"
version = "0.1.0"
description = "Python terminal-first brainstorming app using Claude Code"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
packages = [{include = "app"}]

[tool.poetry.dependencies]
python = "^3.11"
textual = "^0.86.0"
pydantic = "^2.10.0"
pydantic-settings = "^2.0"
PyYAML = "^6.0"
aiofiles = "^24.1.0"
markdown-it-py = "^3.0.0"
mdformat = "^0.7.17"
aiosqlite = "^0.20.0"
typing-extensions = "^4.12.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.23.0"
ruff = "^0.7.0"
mypy = "^1.13.0"
pre-commit = "^4.3.0"
types-PyYAML = "^6.0"

[tool.ruff]
line-length = 100
target-version = "py311"

# Exclude common directories
exclude = [
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".venv",
    "venv",
]

[tool.ruff.lint]
# Enable select rules
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ARG",  # flake8-unused-arguments
    "SIM",  # flake8-simplify
]

ignore = [
    "E501",  # line too long - handled by formatter
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false

[tool.mypy]
python_version = "3.11"
strict = true

# Additional strict options (all enabled by strict=true, but explicit for clarity)
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
check_untyped_defs = true
no_implicit_reexport = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true

# Ignore missing imports for third-party packages without stubs
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-ra",
    "--strict-markers",
    "--ignore=docs",
    "--ignore=.git",
    "--tb=short",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "asyncio: marks tests as async tests",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning",
]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
````
