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

    # Check write roots
    assert "projects/**" in settings["permissions"]["writeRoots"]


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
