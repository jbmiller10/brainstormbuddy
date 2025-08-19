## Purpose

This repository implements a **Python, terminal‑first brainstorming app** (“Brainstorm Buddy”) that guides: **Capture → Clarify → Kernel → Outline → Research → Synthesis → Export**.
We use **Claude Code** with **custom system prompts** and **stage‑gated tool policies** (we **do not** rely on `plan` mode). The app is a Textual‑based TUI; artifacts (kernel/outline/elements) are Markdown; research is stored in SQLite (FTS).

## Ground rules for Claude in this repo

* Be explicit and concrete. Prefer numbered steps and checklists.
* Keep diffs small, focused, and reviewable. Show a plan, then the diff. Avoid drive‑by refactors.
* Always run lint+typecheck+tests after edits and report results.
* It’s acceptable to say “I don’t know” when repo context is insufficient.
* **Never** use destructive shell commands. Do not modify files outside the repo. Do not touch `.env*` or `secrets/**`.
* Prefer quoting relevant lines when reasoning about code or specs.
* When the task spans multiple files, propose a batch diff and apply only after the user approves.


> Tickets may override the allowed/denied tools per task.

## Claude Configuration (Materialize on Demand)

This repo does **not** maintain a `.claude` directory at the root. Instead, we generate Claude configurations on-demand when needed. This keeps the repository clean and allows for flexible configuration testing.

### Quick Start for Claude Code

```bash
# Generate a temporary Claude config
uv run materialize_claude.py /tmp/claude-work

# Run Claude Code from that directory
cd /tmp/claude-work
claude

# Or use --cwd to stay in repo root
claude --cwd /tmp/claude-work

# Cleanup when done
rm -rf /tmp/claude-work
```

### Alternative: Generate in repo (git-ignored)

```bash
# Generate in repo root (ensure .claude is in .gitignore)
uv run materialize_claude.py .

# Work with Claude Code normally
claude

# Clean up after session
rm -rf .claude
```

### Why This Approach?

- **Clean repository**: No configuration files committed to version control
- **Flexible testing**: Generate configs with different settings for testing
- **Portable**: Create configurations anywhere on the system
- **Temporary by design**: Encourages cleanup after development sessions

## Commands

Use **Python 3.11+** and **uv** for dependency management.

### Setup

```bash
# Install dependencies (uv creates venv automatically)
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

### Development Commands

```bash
# Run linting
uv run ruff check .
uv run ruff format .

# Run type checking
uv run mypy . --strict

# Run tests
uv run pytest -q

# Run the TUI application
uv run python -m app.tui.app
```

## Repository structure (target)

```
app/
  core/         # config, state, events, models
  llm/          # Claude Code client, session factory, stage prompts
  permissions/  # settings writer, hooks
  research/     # sqlite/fts, ingest, dedupe
  files/        # scaffold, md IO, diff/patch
  export/       # consolidated exports
  tui/          # Textual app/views/widgets
tests/
.claude/        # project-level settings + hooks (generated)
projects/       # runtime brainstorm projects (created by the app)
exports/        # generated outputs
```

## Coding standards

* Python: type hints everywhere; `mypy --strict` must pass.
* Lint: `ruff` defaults; auto‑fix safe issues when possible.
* Tests: `pytest -q`; add or update tests for each change.
* Commit messages: conventional (`feat: …`, `fix: …`, `chore: …`) with a one‑line imperative summary; body if necessary.

## Implementation stages (for the app)

1. **Capture/Clarify** (read‑only; no web; no writes).
2. **Kernel/Outline** (writes limited to project docs; formatting hook runs).
3. **Research** (WebSearch/WebFetch only when explicitly allowed; writes to research files and DB).
4. **Synthesis** (no web; edits to workstream docs; export bundle).

## Subagents (project‑scoped)

* **researcher**: Allowed `Read, Write (project docs), WebSearch/WebFetch (when enabled)`. Extract atomic findings with sources.
* **critic**: Read‑only review; flags risks and inconsistencies; no web.
* **architect**: Turns kernel + findings into requirements; writes to element pages; no web.

> Subagent files live under `.claude/agents/` and may be created/updated by tickets.

## Prompt style (recommended)

Use simple tags to structure tasks and outputs.

```
<instructions>Goal, constraints, deliverables.</instructions>
<context>Paths, filenames, target interfaces, examples.</context>
<steps>Enumerate; keep atomic, testable.</steps>
<format>Describe exact output: diff, commands, files created.</format>
```

## Review checklist (every change)

* [ ] Small, coherent diff
* [ ] Lint + typecheck + tests pass
* [ ] No writes outside sandbox
* [ ] No Bash or Web\* unless explicitly allowed
* [ ] Clear commit message and updated docs if needed
