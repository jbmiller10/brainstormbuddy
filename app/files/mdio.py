"""Markdown file I/O utilities."""

from pathlib import Path

from app.files.atomic import atomic_write_text


def read_md(path: Path | str) -> str:
    """
    Read a markdown file and return its contents.

    Args:
        path: Path to the markdown file

    Returns:
        Contents of the markdown file

    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    file_path = Path(path) if isinstance(path, str) else path

    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_md(path: Path | str, text: str) -> None:
    """
    Write text to a markdown file.

    Args:
        path: Path to the markdown file
        text: Content to write to the file

    Raises:
        IOError: If there's an error writing the file
    """
    file_path = Path(path) if isinstance(path, str) else path

    atomic_write_text(file_path, text)
