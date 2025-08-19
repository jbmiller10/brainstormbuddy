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
