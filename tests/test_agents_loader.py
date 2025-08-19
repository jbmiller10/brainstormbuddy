"""Unit tests for agent specification loader and materializer."""

import tempfile
from pathlib import Path

import pytest

from app.llm.agents import AgentSpec, _parse_agent_markdown, load_agent_specs, materialize_agents


def test_parse_valid_agent_markdown() -> None:
    """Test parsing a valid agent markdown file with all fields."""
    content = """---
name: test_agent
description: A test agent for validation
tools:
  - Read
  - Write
---

This is the agent's system prompt.
It can span multiple lines.
"""

    spec = _parse_agent_markdown(content, "test.md")

    assert spec.name == "test_agent"
    assert spec.description == "A test agent for validation"
    assert spec.tools == ["Read", "Write"]
    assert "This is the agent's system prompt." in spec.prompt
    assert "It can span multiple lines." in spec.prompt


def test_parse_agent_markdown_minimal() -> None:
    """Test parsing agent markdown with only required fields."""
    content = """---
name: minimal_agent
description: Minimal test agent
---

Simple prompt.
"""

    spec = _parse_agent_markdown(content, "minimal.md")

    assert spec.name == "minimal_agent"
    assert spec.description == "Minimal test agent"
    assert spec.tools == []  # Empty list when not specified
    assert spec.prompt == "Simple prompt."


def test_parse_agent_markdown_missing_frontmatter() -> None:
    """Test that missing frontmatter raises appropriate error."""
    content = """This is just markdown without frontmatter."""

    with pytest.raises(ValueError) as exc_info:
        _parse_agent_markdown(content, "invalid.md")

    assert "Missing YAML frontmatter" in str(exc_info.value)
    assert "invalid.md" in str(exc_info.value)


def test_parse_agent_markdown_invalid_yaml() -> None:
    """Test that invalid YAML syntax raises appropriate error."""
    content = """---
name: test
description: [unclosed bracket
---

Content
"""

    with pytest.raises(ValueError) as exc_info:
        _parse_agent_markdown(content, "bad_yaml.md")

    assert "Invalid YAML frontmatter" in str(exc_info.value)
    assert "bad_yaml.md" in str(exc_info.value)


def test_parse_agent_markdown_missing_name() -> None:
    """Test that missing 'name' field raises appropriate error."""
    content = """---
description: Missing name field
---

Content
"""

    with pytest.raises(ValueError) as exc_info:
        _parse_agent_markdown(content, "no_name.md")

    assert "Missing required fields" in str(exc_info.value)
    assert "name" in str(exc_info.value)
    assert "no_name.md" in str(exc_info.value)


def test_parse_agent_markdown_missing_description() -> None:
    """Test that missing 'description' field raises appropriate error."""
    content = """---
name: test_agent
---

Content
"""

    with pytest.raises(ValueError) as exc_info:
        _parse_agent_markdown(content, "no_desc.md")

    assert "Missing required fields" in str(exc_info.value)
    assert "description" in str(exc_info.value)
    assert "no_desc.md" in str(exc_info.value)


def test_parse_agent_markdown_invalid_name_type() -> None:
    """Test that non-string name raises appropriate error."""
    content = """---
name: 123
description: Test agent
---

Content
"""

    with pytest.raises(ValueError) as exc_info:
        _parse_agent_markdown(content, "bad_type.md")

    assert "'name' must be a string" in str(exc_info.value)
    assert "bad_type.md" in str(exc_info.value)


def test_parse_agent_markdown_invalid_tools_type() -> None:
    """Test that non-list tools field raises appropriate error."""
    content = """---
name: test_agent
description: Test agent
tools: "Read"
---

Content
"""

    with pytest.raises(ValueError) as exc_info:
        _parse_agent_markdown(content, "bad_tools.md")

    assert "'tools' must be a list" in str(exc_info.value)
    assert "bad_tools.md" in str(exc_info.value)


def test_parse_agent_markdown_invalid_tool_item() -> None:
    """Test that non-string items in tools list raise appropriate error."""
    content = """---
name: test_agent
description: Test agent
tools:
  - Read
  - 42
---

Content
"""

    with pytest.raises(ValueError) as exc_info:
        _parse_agent_markdown(content, "bad_tool_item.md")

    assert "tools[1] must be a string" in str(exc_info.value)
    assert "bad_tool_item.md" in str(exc_info.value)


def test_load_agent_specs_from_package() -> None:
    """Test loading agent specs from the actual package."""
    specs = load_agent_specs("app.llm.agentspecs")

    # Should load exactly 3 specs
    assert len(specs) == 3

    # Check that all specs have required fields
    spec_names = {spec.name for spec in specs}
    assert "researcher" in spec_names
    assert "critic" in spec_names
    assert "architect" in spec_names

    # Verify each spec
    for spec in specs:
        assert isinstance(spec.name, str)
        assert isinstance(spec.description, str)
        assert isinstance(spec.tools, list)
        assert isinstance(spec.prompt, str)
        assert len(spec.prompt) > 0


def test_load_agent_specs_nonexistent_package() -> None:
    """Test that loading from nonexistent package raises appropriate error."""
    with pytest.raises(ModuleNotFoundError) as exc_info:
        load_agent_specs("nonexistent.package.path")

    assert "Cannot find package" in str(exc_info.value)
    assert "nonexistent.package.path" in str(exc_info.value)


def test_materialize_agents_creates_structure(tmp_path: Path) -> None:
    """Test that materialize_agents creates the correct directory structure."""
    agents_dir = materialize_agents(tmp_path, "app.llm.agentspecs")

    # Check that the directory structure was created
    assert agents_dir.exists()
    assert agents_dir == tmp_path / ".claude" / "agents"

    # Check that files were created
    md_files = list(agents_dir.glob("*.md"))
    assert len(md_files) == 3

    # Check that expected files exist
    filenames = {f.name for f in md_files}
    assert "researcher.md" in filenames
    assert "critic.md" in filenames
    assert "architect.md" in filenames


def test_materialize_agents_content_matches(tmp_path: Path) -> None:
    """Test that materialized content matches the source specs."""
    # Load original specs
    original_specs = load_agent_specs("app.llm.agentspecs")

    # Materialize them
    agents_dir = materialize_agents(tmp_path, "app.llm.agentspecs")

    # Load and verify each materialized file
    for spec in original_specs:
        # Find the corresponding file
        possible_paths = [
            agents_dir / f"{spec.name}.md",
            agents_dir / "researcher.md" if spec.name == "researcher" else None,
            agents_dir / "critic.md" if spec.name == "critic" else None,
            agents_dir / "architect.md" if spec.name == "architect" else None,
        ]

        file_path = None
        for path in possible_paths:
            if path and path.exists():
                file_path = path
                break

        assert file_path is not None, f"Could not find file for {spec.name}"

        # Read and parse the materialized file
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        materialized_spec = _parse_agent_markdown(content, file_path.name)

        # Compare with original
        assert materialized_spec.name == spec.name
        assert materialized_spec.description == spec.description
        assert materialized_spec.tools == spec.tools
        assert materialized_spec.prompt.strip() == spec.prompt.strip()


def test_materialize_agents_preserves_filenames(tmp_path: Path) -> None:
    """Test that original filenames are preserved during materialization."""
    agents_dir = materialize_agents(tmp_path, "app.llm.agentspecs")

    # Check that specific filenames were preserved
    assert (agents_dir / "researcher.md").exists()
    assert (agents_dir / "critic.md").exists()
    assert (agents_dir / "architect.md").exists()


def test_materialize_agents_idempotent(tmp_path: Path) -> None:
    """Test that materializing multiple times is safe and idempotent."""
    # Materialize twice
    agents_dir1 = materialize_agents(tmp_path, "app.llm.agentspecs")
    agents_dir2 = materialize_agents(tmp_path, "app.llm.agentspecs")

    # Should return the same path
    assert agents_dir1 == agents_dir2

    # Should still have exactly 3 files
    md_files = list(agents_dir2.glob("*.md"))
    assert len(md_files) == 3


def test_agent_spec_is_frozen() -> None:
    """Test that AgentSpec is immutable."""
    spec = AgentSpec(name="test", description="Test agent", tools=["Read"], prompt="Test prompt")

    with pytest.raises(AttributeError):
        spec.name = "modified"  # type: ignore


def test_roundtrip_integrity() -> None:
    """Test that specs can be loaded, materialized, and re-loaded without data loss."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Load original specs
        original_specs = load_agent_specs("app.llm.agentspecs")
        original_by_name = {spec.name: spec for spec in original_specs}

        # Materialize to temp directory
        agents_dir = materialize_agents(tmp_path, "app.llm.agentspecs")

        # Manually parse each materialized file
        for md_file in agents_dir.glob("*.md"):
            with open(md_file, encoding="utf-8") as f:
                content = f.read()

            spec = _parse_agent_markdown(content, md_file.name)

            # Compare with original
            original = original_by_name.get(spec.name)
            assert original is not None
            assert spec.name == original.name
            assert spec.description == original.description
            assert spec.tools == original.tools
            # Compare normalized prompts (strip whitespace)
            assert spec.prompt.strip() == original.prompt.strip()
