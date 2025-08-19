"""Command-line interface for Brainstorm Buddy."""

import sys
from pathlib import Path

import typer

from app.permissions.settings_writer import write_project_settings

app = typer.Typer(
    name="bb",
    help="Brainstorm Buddy CLI - Tools for managing brainstorming sessions and Claude configs",
)


@app.command()
def materialize_claude(
    dest: str = typer.Option(..., "--dest", "-d", help="Destination path for .claude config"),
) -> None:
    """Generate Claude configuration at the specified destination."""
    try:
        # Convert string to Path
        dest_path = Path(dest).resolve()

        # Ensure the destination directory exists
        dest_path.mkdir(parents=True, exist_ok=True)

        # Generate the Claude configuration
        config_dir = write_project_settings(
            repo_root=dest_path,
            config_dir_name=".claude",
            import_hooks_from="app.permissions.hooks_lib",
        )

        print(f"✓ Successfully created Claude configuration at: {config_dir}")
        print(f"  Settings: {config_dir}/settings.json")
        print(f"  Hooks: {config_dir}/hooks/")
        print()
        print("To use this configuration with Claude Code:")
        print(f"  cd {dest_path}")
        print("  claude")

    except Exception as e:
        print(f"✗ Failed to create Claude configuration: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    app()
