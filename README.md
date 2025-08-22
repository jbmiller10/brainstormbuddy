# Brainstorm Buddy

[![CI](https://github.com/jbmiller10/brainstormbuddy/actions/workflows/ci.yml/badge.svg)](https://github.com/jbmiller10/brainstormbuddy/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jbmiller10/brainstormbuddy/branch/main/graph/badge.svg)](https://codecov.io/gh/jbmiller10/brainstormbuddy)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A Python terminal-first brainstorming app that guides through: Capture → Clarify → Kernel → Outline → Research → Synthesis → Export.

## Requirements

- Python 3.11+
- uv (recommended package manager)

## Installation

```bash
# Install dependencies (uv creates venv automatically)
uv pip install -r requirements.txt

# For development, also install dev dependencies
uv pip install -r requirements-dev.txt

# Optional: Install Claude SDK for real AI assistance
uv pip install claude-code-sdk
# Or install with the optional dependency group:
uv pip install -e ".[claude]"
```

### Claude SDK Integration

Brainstorm Buddy can use either a fake LLM client (for testing) or the real Claude Code SDK for AI-powered assistance.

#### Using Real Claude

1. **Install the SDK**:
   ```bash
   uv pip install claude-code-sdk
   ```

2. **Configure Settings** (optional):
   - Set `use_fake_llm_client=false` in your settings
   - The app will automatically detect and use the SDK if installed

3. **Check Status**:
   - In the app, press `:` to open the command palette
   - Type `claude status` to see the current configuration

#### Using Fake Client (Default for Testing)

The fake client provides deterministic responses for testing without requiring API access:
- Automatically used when claude-code-sdk is not installed
- Can be forced by setting `use_fake_llm_client=true` in settings
- Provides realistic responses for all brainstorming stages

## CLI Commands

### Generate Claude Configuration

The `materialize_claude.py` script creates a `.claude` configuration directory at any specified location. This is useful for setting up Claude Code to work with your project with proper permissions and formatting hooks.

```bash
# Generate Claude config at a specific path
uv run materialize_claude.py /path/to/project

# Example: Generate config in /tmp/test
uv run materialize_claude.py /tmp/test
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
uv run materialize_claude.py /tmp/claude-dev
cd /tmp/claude-dev
claude
# Cleanup: rm -rf /tmp/claude-dev

# Option 2: Use --cwd to work from repo while config is elsewhere
uv run materialize_claude.py /tmp/claude-dev
claude --cwd /tmp/claude-dev

# Option 3: Generate in repo root but clean up after (ensure .claude is git-ignored)
uv run materialize_claude.py .
claude
# Cleanup: rm -rf .claude
```

The generated configuration includes:
- Permission settings (deny-first approach)
- Markdown formatting hooks
- Safe write roots for project files

## Development Commands

All commands use `uv run` which automatically manages the virtual environment.

### Run linting

```bash
uv run ruff check .
uv run ruff format .
```

### Run type checking

```bash
uv run mypy . --strict
```

### Run tests

```bash
uv run pytest -q
```

### Run the TUI application

```bash
uv run python -m app.tui.app
```

## Development

This project uses:
- **Textual** for the terminal UI
- **Pydantic** for data validation
- **SQLite with FTS** for research storage
- **Markdown** for document processing
- **uv** for dependency management

## Testing

Run the test suite with:

```bash
uv run pytest -q
```

## Code Quality

### Manual Checks

Ensure code quality with:

```bash
# Linting with ruff
uv run ruff check .
uv run ruff format .

# Type checking with strict mypy
uv run mypy . --strict

# Run all tests
uv run pytest -q
```

### Pre-commit Hooks (Optional)

Install pre-commit hooks to automatically check code quality before commits:

```bash
# Install the git hook scripts
uv run pre-commit install

# (Optional) Run against all files
uv run pre-commit run --all-files
```

The pre-commit hooks will automatically run ruff linting/formatting and other checks on staged files before each commit.
