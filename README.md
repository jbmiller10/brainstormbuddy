# Brainstorm Buddy

A Python terminal-first brainstorming app that guides through: Capture → Clarify → Kernel → Outline → Research → Synthesis → Export.

## Requirements

- Python 3.11+
- Poetry

## Installation

### With Poetry (default)

```bash
poetry install
```

## Commands

### Run linting

```bash
poetry run ruff .
```

### Run type checking

```bash
poetry run mypy .
```

### Run tests

```bash
poetry run pytest -q
```

### Run the TUI application

```bash
poetry run python -m app.tui.app
```

### Alternative: With uv (optional)

```bash
uv venv
uv pip install -r requirements.txt
python -m app.tui.app
```

## Development

This project uses:
- **Textual** for the terminal UI
- **Pydantic** for data validation
- **SQLite with FTS** for research storage
- **Markdown** for document processing
- **Poetry** for dependency management

## Testing

Run the test suite with:

```bash
poetry run pytest -q
```

## Code Quality

Ensure code quality with:

```bash
poetry run ruff .
poetry run mypy .
```