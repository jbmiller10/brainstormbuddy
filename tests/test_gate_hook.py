"""Test gate hook functionality for PreToolUse validation."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from app.permissions.hooks_lib.gate import validate_tool_use
from app.permissions.settings_writer import write_project_settings


class TestValidateToolUse:
    """Test the validate_tool_use function directly."""

    def test_deny_bash_tool(self) -> None:
        """Test that Bash tool is always denied."""
        payload = {"tool_name": "Bash", "command": "ls -la"}
        allowed, reason = validate_tool_use(payload)
        assert not allowed
        assert "Bash tool is denied" in reason

    def test_deny_sensitive_paths_env(self) -> None:
        """Test that .env files are denied."""
        payloads = [
            {"tool_name": "Write", "target_path": ".env"},
            {"tool_name": "Edit", "target_path": ".env.local"},
            {"tool_name": "MultiEdit", "target_path": "/home/user/.env.production"},
        ]
        for payload in payloads:
            allowed, reason = validate_tool_use(payload)
            assert not allowed, f"Should deny {payload['target_path']}"
            assert ".env" in reason

    def test_deny_sensitive_paths_secrets(self) -> None:
        """Test that secrets directory is denied."""
        payloads = [
            {"tool_name": "Write", "target_path": "secrets/api_key.txt"},
            {"tool_name": "Edit", "target_path": "/app/secrets/config.json"},
            {"tool_name": "NotebookEdit", "target_path": "secrets/notebook.ipynb"},
        ]
        for payload in payloads:
            allowed, reason = validate_tool_use(payload)
            assert not allowed, f"Should deny {payload['target_path']}"
            assert "secrets/" in reason

    def test_deny_sensitive_paths_git(self) -> None:
        """Test that .git directory is denied."""
        payloads = [
            {"tool_name": "Write", "target_path": ".git/config"},
            {"tool_name": "Edit", "target_path": ".git/hooks/pre-commit"},
            {"tool_name": "MultiEdit", "target_path": "/repo/.git/HEAD"},
        ]
        for payload in payloads:
            allowed, reason = validate_tool_use(payload)
            assert not allowed, f"Should deny {payload['target_path']}"
            assert ".git/" in reason

    def test_allow_normal_write_paths(self) -> None:
        """Test that normal paths are allowed for write operations."""
        payloads = [
            {"tool_name": "Write", "target_path": "src/main.py"},
            {"tool_name": "Edit", "target_path": "/home/user/project/README.md"},
            {"tool_name": "MultiEdit", "target_path": "tests/test_example.py"},
            {"tool_name": "NotebookEdit", "target_path": "notebooks/analysis.ipynb"},
        ]
        for payload in payloads:
            allowed, reason = validate_tool_use(payload)
            assert allowed, f"Should allow {payload['target_path']}: {reason}"
            assert reason == ""

    def test_allow_read_tool(self) -> None:
        """Test that Read tool is allowed."""
        payloads = [
            {"tool_name": "Read", "file_path": ".env"},  # Read is allowed even for sensitive files
            {"tool_name": "Read", "file_path": "src/main.py"},
        ]
        for payload in payloads:
            allowed, reason = validate_tool_use(payload)
            assert allowed, f"Should allow Read for {payload.get('file_path')}: {reason}"
            assert reason == ""

    def test_deny_path_traversal(self) -> None:
        """Test that path traversal attempts are denied."""
        payload = {"tool_name": "Write", "target_path": "../../../etc/passwd"}
        allowed, reason = validate_tool_use(payload)
        assert not allowed
        assert "outside repository" in reason.lower() or "invalid" in reason.lower()

    def test_url_domain_deny_list(self) -> None:
        """Test that denied domains are blocked."""
        payload = {
            "tool_name": "WebFetch",
            "url": "https://malicious.site/api",
            "denied_domains": ["malicious.site", "tracker.com"],
            "allowed_domains": [],
        }
        allowed, reason = validate_tool_use(payload)
        assert not allowed
        assert "malicious.site" in reason
        assert "denied" in reason.lower()

    def test_url_domain_allow_list_not_in_list(self) -> None:
        """Test that domains not in allow list are blocked when allow list is specified."""
        payload = {
            "tool_name": "WebFetch",
            "url": "https://unknown.com/api",
            "allowed_domains": ["github.com", "api.openai.com"],
            "denied_domains": [],
        }
        allowed, reason = validate_tool_use(payload)
        assert not allowed
        assert "unknown.com" in reason
        assert "not in allow list" in reason

    def test_url_domain_allow_list_in_list(self) -> None:
        """Test that domains in allow list are allowed."""
        payload = {
            "tool_name": "WebFetch",
            "url": "https://github.com/api/repos",
            "allowed_domains": ["github.com", "api.openai.com"],
            "denied_domains": [],
        }
        allowed, reason = validate_tool_use(payload)
        assert allowed
        assert reason == ""

    def test_url_domain_wildcard_deny(self) -> None:
        """Test wildcard domain patterns in deny list."""
        payload = {
            "tool_name": "WebFetch",
            "url": "https://subdomain.tracker.com/api",
            "allowed_domains": [],
            "denied_domains": ["*.tracker.com"],
        }
        allowed, reason = validate_tool_use(payload)
        assert not allowed
        assert "tracker.com" in reason

    def test_url_domain_wildcard_allow(self) -> None:
        """Test wildcard domain patterns in allow list."""
        payload = {
            "tool_name": "WebFetch",
            "url": "https://api.openai.com/v1/completions",
            "allowed_domains": ["*.openai.com"],
            "denied_domains": [],
        }
        allowed, reason = validate_tool_use(payload)
        assert allowed
        assert reason == ""

    def test_url_domain_wildcard_base_domain_matches(self) -> None:
        """Test that base domain matches its own wildcard pattern."""
        # Test deny list
        payload = {
            "tool_name": "WebFetch",
            "url": "https://example.com/api",
            "allowed_domains": [],
            "denied_domains": ["*.example.com"],
        }
        allowed, reason = validate_tool_use(payload)
        assert not allowed
        assert "example.com" in reason

        # Test allow list
        payload = {
            "tool_name": "WebFetch",
            "url": "https://github.com/api",
            "allowed_domains": ["*.github.com"],
            "denied_domains": [],
        }
        allowed, reason = validate_tool_use(payload)
        assert allowed
        assert reason == ""

    def test_url_domain_wildcard_no_false_matches(self) -> None:
        """Test that similar domains don't falsely match wildcards."""
        # Should NOT match "badexample.com" against "*.example.com"
        payload = {
            "tool_name": "WebFetch",
            "url": "https://badexample.com/api",
            "allowed_domains": [],
            "denied_domains": ["*.example.com"],
        }
        allowed, reason = validate_tool_use(payload)
        assert allowed  # Should be allowed since it doesn't match the deny pattern
        assert reason == ""

        # Should NOT match "example.co" against "*.example.com"
        payload = {
            "tool_name": "WebFetch",
            "url": "https://example.co/api",
            "allowed_domains": ["*.example.com"],
            "denied_domains": [],
        }
        allowed, reason = validate_tool_use(payload)
        assert not allowed  # Should be denied since it's not in allow list
        assert "not in allow list" in reason

    def test_url_domain_wildcard_deep_subdomains(self) -> None:
        """Test that deep subdomains match wildcard patterns."""
        payload = {
            "tool_name": "WebFetch",
            "url": "https://api.v2.test.example.com/endpoint",
            "allowed_domains": [],
            "denied_domains": ["*.example.com"],
        }
        allowed, reason = validate_tool_use(payload)
        assert not allowed
        assert "example.com" in reason

        # Test with allow list
        payload = {
            "tool_name": "WebFetch",
            "url": "https://api.v2.test.example.com/endpoint",
            "allowed_domains": ["*.example.com"],
            "denied_domains": [],
        }
        allowed, reason = validate_tool_use(payload)
        assert allowed
        assert reason == ""

    def test_url_domain_deny_wins_over_allow(self) -> None:
        """Test that deny list takes precedence over allow list."""
        payload = {
            "tool_name": "WebFetch",
            "url": "https://bad.example.com/api",
            "allowed_domains": ["*.example.com"],
            "denied_domains": ["bad.example.com"],
        }
        allowed, reason = validate_tool_use(payload)
        assert not allowed
        assert "bad.example.com" in reason
        assert "denied" in reason.lower()

    def test_invalid_url(self) -> None:
        """Test that invalid URLs are rejected."""
        payload = {
            "tool_name": "WebFetch",
            "url": "not-a-valid-url",
            "allowed_domains": [],
            "denied_domains": [],
        }
        allowed, reason = validate_tool_use(payload)
        assert not allowed
        assert "Invalid URL" in reason or "invalid" in reason.lower()


class TestGeneratedGateHook:
    """Test the generated gate hook file."""

    def test_generated_gate_hook_imports_from_hooks_lib(self, tmp_path: Path) -> None:
        """Verify the generated gate hook correctly imports from hooks_lib."""
        # Generate settings
        config_dir = write_project_settings(
            repo_root=tmp_path,
            config_dir_name=".claude",
            import_hooks_from="app.permissions.hooks_lib",
        )

        # Read the generated hook file
        hook_path = config_dir / "hooks" / "gate.py"
        hook_content = hook_path.read_text()

        # Verify it imports from the correct module
        assert "from app.permissions.hooks_lib.gate import validate_tool_use" in hook_content
        assert "def main() -> None:" in hook_content
        assert "PreToolUse" in hook_content
        assert "sys.exit(2)" in hook_content  # Should exit with code 2 on deny
        assert "sys.exit(0)" in hook_content  # Should exit with code 0 on allow

    def test_generated_gate_hook_execution_deny_bash(self, tmp_path: Path) -> None:
        """Test that the generated gate hook denies Bash with exit code 2."""
        # Generate settings
        config_dir = write_project_settings(
            repo_root=tmp_path,
            config_dir_name=".claude",
            import_hooks_from="app.permissions.hooks_lib",
        )

        hook_path = config_dir / "hooks" / "gate.py"
        assert hook_path.exists()

        # Prepare test payload
        payload = json.dumps({"tool_name": "Bash", "command": "ls"})

        # Run the hook
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=payload,
            capture_output=True,
            text=True,
        )

        # Should exit with code 2 (denied)
        assert result.returncode == 2
        assert "Denied" in result.stderr
        assert "Bash tool is denied" in result.stderr

    def test_generated_gate_hook_execution_allow_read(self, tmp_path: Path) -> None:
        """Test that the generated gate hook allows Read with exit code 0."""
        # Generate settings
        config_dir = write_project_settings(
            repo_root=tmp_path,
            config_dir_name=".claude",
            import_hooks_from="app.permissions.hooks_lib",
        )

        hook_path = config_dir / "hooks" / "gate.py"
        assert hook_path.exists()

        # Prepare test payload
        payload = json.dumps({"tool_name": "Read", "file_path": "README.md"})

        # Run the hook
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=payload,
            capture_output=True,
            text=True,
        )

        # Should exit with code 0 (allowed)
        assert result.returncode == 0
        assert result.stderr == ""  # No error output

    def test_generated_gate_hook_execution_deny_sensitive_path(self, tmp_path: Path) -> None:
        """Test that the generated gate hook denies sensitive paths."""
        # Generate settings
        config_dir = write_project_settings(
            repo_root=tmp_path,
            config_dir_name=".claude",
            import_hooks_from="app.permissions.hooks_lib",
        )

        hook_path = config_dir / "hooks" / "gate.py"
        assert hook_path.exists()

        # Test multiple sensitive paths
        test_cases = [
            {"tool_name": "Write", "target_path": ".env"},
            {"tool_name": "Edit", "target_path": "secrets/api.key"},
            {"tool_name": "MultiEdit", "target_path": ".git/config"},
        ]

        for payload_dict in test_cases:
            payload = json.dumps(payload_dict)
            result = subprocess.run(
                [sys.executable, str(hook_path)],
                input=payload,
                capture_output=True,
                text=True,
            )

            # Should exit with code 2 (denied)
            assert result.returncode == 2, f"Should deny {payload_dict['target_path']}"
            assert "Denied" in result.stderr
            assert "sensitive path" in result.stderr.lower()

    def test_generated_gate_hook_invalid_json(self, tmp_path: Path) -> None:
        """Test that the generated gate hook handles invalid JSON gracefully."""
        # Generate settings
        config_dir = write_project_settings(
            repo_root=tmp_path,
            config_dir_name=".claude",
            import_hooks_from="app.permissions.hooks_lib",
        )

        hook_path = config_dir / "hooks" / "gate.py"
        assert hook_path.exists()

        # Send invalid JSON
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input="not valid json",
            capture_output=True,
            text=True,
        )

        # Should exit with code 2 and report JSON error
        assert result.returncode == 2
        assert "Error parsing JSON" in result.stderr

    def test_generated_gate_hook_via_importlib(self, tmp_path: Path) -> None:
        """Test the generated gate hook can be imported and executed via importlib."""
        # Generate settings
        config_dir = write_project_settings(
            repo_root=tmp_path,
            config_dir_name=".claude",
            import_hooks_from="app.permissions.hooks_lib",
        )

        # Load the generated gate.py hook using importlib
        hook_path = config_dir / "hooks" / "gate.py"
        assert hook_path.exists()

        spec = importlib.util.spec_from_file_location("gate_hook", str(hook_path))
        assert spec is not None and spec.loader is not None

        gate_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate_module)

        # The module should have a main function
        assert hasattr(gate_module, "main")
        assert callable(gate_module.main)

        # The module should have imported validate_tool_use
        assert hasattr(gate_module, "validate_tool_use")
        assert callable(gate_module.validate_tool_use)

    def test_hook_files_are_executable(self, tmp_path: Path) -> None:
        """Test that generated hook files have executable permissions."""
        # Generate settings
        config_dir = write_project_settings(repo_root=tmp_path)

        gate_hook = config_dir / "hooks" / "gate.py"
        format_hook = config_dir / "hooks" / "format_md.py"

        # Check that files have execute permissions for owner
        assert gate_hook.stat().st_mode & 0o100
        assert format_hook.stat().st_mode & 0o100

    def test_custom_config_dir_gate_hook(self, tmp_path: Path) -> None:
        """Test that gate hook works with custom config directory."""
        # Use custom parameters
        config_dir = write_project_settings(
            repo_root=tmp_path,
            config_dir_name="custom_config",
            import_hooks_from="my.custom.hooks",
        )

        # Check that gate hook exists and has correct import
        gate_hook = config_dir / "hooks" / "gate.py"
        assert gate_hook.exists()

        hook_content = gate_hook.read_text()
        assert "from my.custom.hooks.gate import validate_tool_use" in hook_content
