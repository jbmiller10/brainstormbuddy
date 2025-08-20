"""Settings writer for Claude project configuration."""

import json
from pathlib import Path
from typing import Any


def write_project_settings(
    repo_root: Path = Path("."),
    config_dir_name: str = ".claude",
    import_hooks_from: str = "app.permissions.hooks_lib",
) -> Path:
    """
    Write Claude project settings with deny-first permissions and hook configuration.

    Args:
        repo_root: Root directory of the repository (default: current directory)
        config_dir_name: Name of the configuration directory (default: ".claude")
        import_hooks_from: Python module path to import hooks from (default: "app.permissions.hooks_lib")

    Returns:
        Path to the created configuration directory
    """
    repo_root = Path(repo_root)
    config_dir = repo_root / config_dir_name
    hooks_dir = config_dir / "hooks"

    # Ensure directories exist
    config_dir.mkdir(exist_ok=True)
    hooks_dir.mkdir(exist_ok=True)

    # Define settings structure
    settings: dict[str, Any] = {
        "permissions": {
            "allow": ["Read", "Edit", "Write"],
            "deny": ["Bash", "WebSearch", "WebFetch"],
            "denyPaths": [".env*", "secrets/**", ".git/**"],
            "writeRoots": ["projects/**", "exports/**"],
            "webDomains": {
                "allow": [],  # Empty list means allow all domains if web tools are enabled
                "deny": [],  # Domains to explicitly deny even if allowed
            },
        },
        "hooks": {
            "PreToolUse": f"{config_dir_name}/hooks/gate.py",
            "PostToolUse": f"{config_dir_name}/hooks/format_md.py",
        },
    }

    # Write settings.json
    settings_path = config_dir / "settings.json"
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")  # Add trailing newline

    # Create hook stub files
    _create_gate_hook(hooks_dir / "gate.py", import_hooks_from)
    _create_format_md_hook(hooks_dir / "format_md.py", import_hooks_from)

    return config_dir


def _create_gate_hook(hook_path: Path, import_hooks_from: str) -> None:
    """
    Create the PreToolUse gate hook that imports from hooks_lib.

    Args:
        hook_path: Path to the hook file
        import_hooks_from: Python module path to import hooks from
    """
    hook_content = f'''#!/usr/bin/env python3
"""Claude PreToolUse hook: validate tool use against security policies."""

from __future__ import annotations
import json
import sys

# Import validation function from the app's hooks library
from {import_hooks_from}.gate import validate_tool_use


def main() -> None:
    """Main hook entry point."""
    # stdin JSON: dict with tool_name and other tool parameters
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {{e}}", file=sys.stderr)
        sys.exit(2)

    # Validate the tool use
    allowed, reason = validate_tool_use(payload)

    if not allowed:
        # Print reason to stderr and exit with code 2 to deny
        print(f"Denied: {{reason}}", file=sys.stderr)
        sys.exit(2)

    # Allow the tool use
    sys.exit(0)


if __name__ == "__main__":
    main()
'''

    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(hook_content)

    # Make the hook executable (Python will handle this cross-platform)
    hook_path.chmod(0o755)


def _create_format_md_hook(hook_path: Path, import_hooks_from: str) -> None:
    """
    Create the PostToolUse format_md hook that imports from hooks_lib.

    Args:
        hook_path: Path to the hook file
        import_hooks_from: Python module path to import hooks from
    """
    hook_content = f'''#!/usr/bin/env python3
"""Claude PostToolUse hook: format Markdown via mdformat (pure Python)."""

from __future__ import annotations
import json
import sys
from pathlib import Path

# Import formatting function and atomic writer from the app's hooks library
from {import_hooks_from}.format_md import _format_markdown_text
from {import_hooks_from}.io import atomic_replace_text


def main() -> None:
    """Main hook entry point."""
    # stdin JSON: dict with tool_name and target_path keys
    payload = json.load(sys.stdin)
    path = Path(payload.get("target_path") or "")
    if path.suffix.lower() != ".md":
        sys.exit(0)
    # Read, format, write back atomically with durability guarantees
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    formatted = _format_markdown_text(content)
    if formatted != content:
        atomic_replace_text(path, formatted)
    sys.exit(0)


if __name__ == "__main__":
    main()
'''

    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(hook_content)

    # Make the hook executable (Python will handle this cross-platform)
    hook_path.chmod(0o755)
