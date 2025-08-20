"""Tests for CLI commands."""

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from app.cli import app

runner = CliRunner()


def test_materialize_claude_with_default_config_dir(tmp_path: Path) -> None:
    """Test materialize-claude command with default config_dir_name."""
    dest = tmp_path / "test_workspace"

    # Since materialize-claude is the only command, it becomes the default
    result = runner.invoke(app, ["--dest", str(dest)])

    assert result.exit_code == 0
    assert "Successfully created Claude configuration" in result.stdout

    # Check that the .claude directory was created (default)
    config_dir = dest / ".claude"
    assert config_dir.exists()
    assert (config_dir / "settings.json").exists()
    assert (config_dir / "hooks" / "gate.py").exists()
    assert (config_dir / "hooks" / "format_md.py").exists()

    # Verify settings.json content
    with open(config_dir / "settings.json", encoding="utf-8") as f:
        settings = json.load(f)
    assert "permissions" in settings
    assert "hooks" in settings


def test_materialize_claude_with_custom_config_dir(tmp_path: Path) -> None:
    """Test materialize-claude command with custom config_dir_name."""
    dest = tmp_path / "test_workspace"
    custom_name = ".custom-claude"

    result = runner.invoke(app, ["--dest", str(dest), "--config-dir-name", custom_name])

    assert result.exit_code == 0
    assert "Successfully created Claude configuration" in result.stdout

    # Check that the custom directory was created
    config_dir = dest / custom_name
    assert config_dir.exists()
    assert (config_dir / "settings.json").exists()
    assert (config_dir / "hooks" / "gate.py").exists()
    assert (config_dir / "hooks" / "format_md.py").exists()

    # Verify settings.json content references the custom dir
    with open(config_dir / "settings.json", encoding="utf-8") as f:
        settings = json.load(f)
    assert settings["hooks"]["PreToolUse"] == f"{custom_name}/hooks/gate.py"
    assert settings["hooks"]["PostToolUse"] == f"{custom_name}/hooks/format_md.py"


def test_materialize_claude_creates_parent_directories(tmp_path: Path) -> None:
    """Test that materialize-claude creates parent directories if they don't exist."""
    dest = tmp_path / "deep" / "nested" / "path"

    result = runner.invoke(app, ["--dest", str(dest)])

    assert result.exit_code == 0
    assert dest.exists()
    assert (dest / ".claude").exists()


def test_materialize_claude_error_handling() -> None:
    """Test materialize-claude error handling for invalid paths."""
    # Use an invalid path that will cause an error
    with patch("app.cli.write_project_settings", side_effect=Exception("Test error")):
        result = runner.invoke(app, ["--dest", "/tmp/test"])

        assert result.exit_code == 1
        assert "Failed to create Claude configuration" in result.stderr
        assert "Test error" in result.stderr


def test_materialize_claude_short_flags(tmp_path: Path) -> None:
    """Test materialize-claude command with short flags."""
    dest = tmp_path / "test_workspace"
    custom_name = ".short-flags"

    result = runner.invoke(app, ["-d", str(dest), "-c", custom_name])

    assert result.exit_code == 0
    assert (dest / custom_name).exists()


def test_materialize_claude_logs_correct_paths(tmp_path: Path) -> None:
    """Test that materialize-claude logs the correct paths."""
    dest = tmp_path / "test_workspace"
    custom_name = ".my-claude"

    result = runner.invoke(app, ["--dest", str(dest), "--config-dir-name", custom_name])

    assert result.exit_code == 0
    # Check that the output contains the correct paths
    assert str(dest / custom_name) in result.stdout
    assert f"Settings: {dest / custom_name}/settings.json" in result.stdout
    assert f"Hooks: {dest / custom_name}/hooks/" in result.stdout
    assert f"cd {dest}" in result.stdout
