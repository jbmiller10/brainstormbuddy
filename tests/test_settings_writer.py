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
    assert "from app.permissions.hooks_lib.format_md import _format_markdown_text" in format_content
    assert "def main() -> None:" in format_content


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


def test_custom_config_dir_and_import_path(tmp_path: Path) -> None:
    """Test that custom config directory and import paths work correctly."""
    # Use custom parameters
    config_dir = write_project_settings(
        repo_root=tmp_path,
        config_dir_name="custom_config",
        import_hooks_from="my.custom.hooks",
    )

    # Check that the return value is correct
    assert config_dir == tmp_path / "custom_config"

    # Check that directories exist with custom name
    assert (tmp_path / "custom_config").exists()
    assert (tmp_path / "custom_config" / "hooks").exists()

    # Check that settings.json exists and has correct hook paths
    settings_path = tmp_path / "custom_config" / "settings.json"
    assert settings_path.exists()

    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)

    assert settings["hooks"]["PreToolUse"] == "custom_config/hooks/gate.py"
    assert settings["hooks"]["PostToolUse"] == "custom_config/hooks/format_md.py"

    # Check that format_md.py uses the custom import path
    format_hook = tmp_path / "custom_config" / "hooks" / "format_md.py"
    with open(format_hook, encoding="utf-8") as f:
        format_content = f.read()
    assert "from my.custom.hooks.format_md import _format_markdown_text" in format_content
