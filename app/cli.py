"""Command-line interface for Brainstorm Buddy."""

from pathlib import Path

import typer

from app.permissions.settings_writer import write_project_settings

app = typer.Typer(
    name="bb",
    help="Brainstorm Buddy CLI - Tools for managing brainstorming sessions and Claude configs",
    add_completion=False,
)


@app.command(name="materialize-claude")  # type: ignore[misc]
def materialize_claude(
    dest: Path = typer.Option(  # noqa: B008
        ...,
        "--dest",
        "-d",
        help="Destination path where .claude config will be created",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """
    Generate Claude configuration at the specified destination.

    This command creates a .claude directory with hooks and settings
    that enable Claude Code to work with formatting and permission controls.

    Example:
        poetry run bb materialize-claude --dest /tmp/myproject
    """
    try:
        # Ensure the destination directory exists
        dest.mkdir(parents=True, exist_ok=True)

        # Generate the Claude configuration
        config_dir = write_project_settings(
            repo_root=dest,
            config_dir_name=".claude",
            import_hooks_from="app.permissions.hooks_lib",
        )

        typer.secho(
            f"✓ Successfully created Claude configuration at: {config_dir}",
            fg=typer.colors.GREEN,
        )
        typer.echo(f"  Settings: {config_dir}/settings.json")
        typer.echo(f"  Hooks: {config_dir}/hooks/")
        typer.echo()
        typer.echo("To use this configuration with Claude Code:")
        typer.echo(f"  cd {dest}")
        typer.echo("  claude")

    except Exception as e:
        typer.secho(
            f"✗ Failed to create Claude configuration: {e}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
