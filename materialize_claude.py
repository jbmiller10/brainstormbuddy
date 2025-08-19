#!/usr/bin/env python3
"""Standalone script to materialize Claude configuration."""

import sys
from pathlib import Path

from app.permissions.settings_writer import write_project_settings


def main() -> None:
    """Main entry point for materialize-claude command."""
    if len(sys.argv) != 2:
        print("Usage: materialize_claude.py <destination_path>")
        print("Example: uv run materialize_claude.py /tmp/claude-work")
        sys.exit(1)

    dest = Path(sys.argv[1]).resolve()

    try:
        # Ensure the destination directory exists
        dest.mkdir(parents=True, exist_ok=True)

        # Generate the Claude configuration
        config_dir = write_project_settings(
            repo_root=dest,
            config_dir_name=".claude",
            import_hooks_from="app.permissions.hooks_lib",
        )

        print(f"✓ Successfully created Claude configuration at: {config_dir}")
        print(f"  Settings: {config_dir}/settings.json")
        print(f"  Hooks: {config_dir}/hooks/")
        print()
        print("To use this configuration with Claude Code:")
        print(f"  cd {dest}")
        print("  claude")

    except Exception as e:
        print(f"✗ Failed to create Claude configuration: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
