# Brainstorm Buddy

[![CI](https://github.com/jbmiller10/brainstormbuddy/actions/workflows/ci.yml/badge.svg)](https://github.com/jbmiller10/brainstormbuddy/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jbmiller10/brainstormbuddy/branch/main/graph/badge.svg)](https://codecov.io/gh/jbmiller10/brainstormbuddy)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A Python terminal-first brainstorming app that guides through: Capture → Clarify → Kernel → Outline → Research → Synthesis → Export.

## Requirements

- Python 3.11+
- Poetry or uv

## Installation

### With Poetry

```bash
poetry install
```

### With uv

```bash
uv venv
uv pip install -r requirements.txt
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

### Manual Checks

Ensure code quality with:

```bash
# Linting with ruff
poetry run ruff check .
poetry run ruff format .

# Type checking with strict mypy
poetry run mypy .

# Run all tests
poetry run pytest -q
```

### Pre-commit Hooks (Optional)

Install pre-commit hooks to automatically check code quality before commits:

```bash
# Install pre-commit
poetry add --group dev pre-commit

# Install the git hook scripts
poetry run pre-commit install

# (Optional) Run against all files
poetry run pre-commit run --all-files
```

The pre-commit hooks will automatically run ruff linting/formatting and other checks on staged files before each commit.
