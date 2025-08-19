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

## CLI Commands

### Generate Claude Configuration

The `materialize-claude` command creates a `.claude` configuration directory at any specified location. This is useful for setting up Claude Code to work with your project with proper permissions and formatting hooks.

```bash
# Generate Claude config at a specific path
poetry run bb materialize-claude --dest /path/to/project

# Example: Generate config in /tmp/test
poetry run bb materialize-claude --dest /tmp/test
```

After generating the configuration, you can run Claude Code in that directory:

```bash
cd /path/to/project
claude
```

#### Temporary Development Workflow

For development work, create throwaway configurations that don't clutter your repository:

```bash
# Option 1: Generate in temporary directory
poetry run bb materialize-claude --dest /tmp/claude-dev
cd /tmp/claude-dev
claude
# Cleanup: rm -rf /tmp/claude-dev

# Option 2: Use --cwd to work from repo while config is elsewhere
poetry run bb materialize-claude --dest /tmp/claude-dev
claude --cwd /tmp/claude-dev

# Option 3: Generate in repo root but clean up after (ensure .claude is git-ignored)
poetry run bb materialize-claude --dest .
claude
# Cleanup: rm -rf .claude
```

The generated configuration includes:
- Permission settings (deny-first approach)
- Markdown formatting hooks
- Safe write roots for project files

## Development Commands

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
