## Purpose

You are operating inside a **Python, terminal-first brainstorming app** (“Brainstorm Buddy”) repository. The flow is: **Capture → Clarify → Kernel → Outline → Research → Synthesis → Export**. You will edit code, Markdown, and configuration, and you must respect stage-gated tool policies.
 The app is a Textual‑based TUI; artifacts (kernel/outline/elements) are Markdown; research is stored in SQLite (FTS).

---

## Ground rules

* Be explicit and concrete. Prefer numbered steps and checklists.
* Keep diffs small, focused, and reviewable. Show a plan, then the diff. Avoid drive-by refactors.
* Always run (or print) lint + typecheck + tests after edits and report results.
* If repo context is insufficient, state the uncertainty and proceed with the smallest safe change.
* **Never** use destructive shell commands. Do not write outside the repo. Do not touch `.env*` or `secrets/**`.
* Quote relevant lines when reasoning about code or specs.
* For multi-file changes, prepare a batch diff and apply as one transaction only after approval.
* Tickets may override allowed/denied tools per task. Deny wins.

---

## Repo invariants (uv-first)

* **Package/deps:** Use **PEP 621** `[project]` in `pyproject.toml` as the source of truth. Do **not** add Poetry or pipenv usage.

  * Pin runtime with `uv pip compile pyproject.toml -o requirements.txt`.
  * Pin dev with `requirements-dev.txt` (or install tools ad-hoc via `uv pip install …` in CI).
  * Use `uv venv`, `uv pip install -r …`, and `uv run …` in commands and CI.
* **Pydantic settings:** For **pydantic-settings v2**, configure with `SettingsConfigDict` (not `class Config:`).
* **Atomic I/O:** Reuse `app/files/atomic.atomic_write_text` and the batch utilities in `app/files/diff.py`. Do not duplicate atomic writers.
* **Stage policy:** Follow `app/llm/sessions.get_policy`. Respect `allowed_tools`, `denied_tools`, `write_roots`, and any web-tool toggles. Deny always wins.
* **Hooks & security:** PreToolUse gate must deny Bash, sensitive paths (`.env*`, `secrets/**`, `.git/**`), and disallowed domains when a URL is present. PostToolUse formats Markdown **only if the content changed**.
* **Textual diffs:** When rendering unified diffs in the TUI, do not enable Rich `markup` for raw diffs. Either escape content or set `markup=False`.

---

## Turn protocol (follow every turn)

1. **Restate the assignment (one screen)**

* Ticket ID + title.
* Deliverables (exact file paths).
* Acceptance criteria & validation steps.
* Working directory and tool constraints.

2. **Plan (brief, actionable)**

* Impacted files.
* New/changed tests.
* Any CI/README updates.
* Idempotency/rollback strategy (atomic write or batch apply).

3. **Implement with guardrails**

* No writes outside sandbox and `write_roots`.
* For multi-file edits, build a `BatchDiff` and apply atomically.
* Reuse existing helpers; do not re-implement core utilities.
* If selecting a subagent, compute and display `final_allowed = (stage.allowed ∩ agent.tools) − stage.denied`.

4. **Output format (strict)**

* **Plan** (5–10 lines).
* **Unified diff(s)** for all changes (no prose between diffs).
* **New/updated tests** (paths + short rationale).
* **CI & README changes** (as diffs) if touched.
* **Validation plan** (exact commands):

  ```bash
  uv venv
  uv pip install -r requirements.txt
  uv pip install -r requirements-dev.txt
  uv run ruff check .
  uv run ruff format --check .
  uv run mypy . --strict
  uv run pytest -q
  uv run python -m app.tui.app
  ```
* **Self-review rubric** (explicit pass/fail per item below).

---

## Self-review rubric (check all)

* Single package manager = **uv**; no Poetry artifacts introduced.
* `[project]` deps authoritative; if deps changed, `requirements*.txt` recompiled in this change.
* Pydantic v2 style (`SettingsConfigDict`) everywhere settings are touched.
* Writes are atomic; batch edits rollback on failure; re-runs are idempotent.
* Hooks: gate denies Bash/sensitive paths and enforces domain allow/deny; deny returns exit code 2. Format hook only rewrites `.md` when content changes.
* Tests cover the change; deterministic (no time/race sensitivity).
* No duplicated helpers/utilities.
* TUI diff rendering safe (no Rich markup parsing issues).
* README shows uv commands exactly as in the validation block when docs are updated.

---

## Common pitfalls (pre-commit mental scan)

* Poetry remnants (`[tool.poetry]`) or instructions: avoid adding usage; if encountered, propose an ADR to remove in a follow-up.
* Drift between `[project]` and `requirements*.txt`: re-compile pins with `uv pip compile` and commit them.
* Pydantic v1 config (`class Config:`) anywhere in settings.
* Second atomic writer creeping in; always import the existing helper.
* Raw diff displayed with `markup=True` in Textual.
* Gate stub or incomplete deny logic (Bash, sensitive paths, domain lists).
* Agent policy leak (requested tool allowed despite stage deny).

---

## Minimal ADR template (use only when necessary)

```
# ADR: Decision Required by Ticket <ID>
- Context: <one sentence>
- Decision: <one sentence>
- Alternatives: <A vs B> (why rejected)
- Impact: CI/docs/tests updated as shown in diffs
```

---

## Commands (reference)

Use **Python 3.11+** and **uv**.

```bash
# Install dependencies
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt

# Lint
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy . --strict

# Tests
uv run pytest -q

# Run the TUI
uv run python -m app.tui.app
```

---

## Claude configuration (materialize on demand)

This repo does **not** keep a `.claude` directory under VCS. Generate configs when needed.

```bash
# Generate a temporary Claude config
uv run materialize_claude.py /tmp/claude-work

# Run Claude Code in that workdir
cd /tmp/claude-work && claude
# Or from repo root
claude --cwd /tmp/claude-work

# Cleanup
rm -rf /tmp/claude-work
```

Alternative (git-ignored in repo):

```bash
uv run materialize_claude.py .
claude
rm -rf .claude
```

---

## Stages & subagents (context)

* **Stages:**

  1. Capture/Clarify (read-only; no web; no writes)
  2. Kernel/Outline (writes limited to project docs; formatting hook runs)
  3. Research (WebSearch/WebFetch only when explicitly allowed; writes to research files/DB)
  4. Synthesis (no web; edits to workstream docs; export bundle)

* **Subagents:**

  * **researcher:** `Read`, `Write (project docs)`, `WebSearch/WebFetch` when enabled; extract atomic findings with sources.
  * **critic:** read-only review; flags risks/inconsistencies; no web.
  * **architect:** converts kernel + findings to requirements; writes to element pages; no web.

---

## Prompt/output style

Use simple structural tags when it clarifies outputs:

```
<instructions>Goal, constraints, deliverables.</instructions>
<context>Paths, filenames, target interfaces, examples.</context>
<steps>Enumerate; keep atomic, testable.</steps>
<format>Describe exact output: diff, commands, files created.</format>
```

---

## Review checklist (for your own output)

* [ ] Small, coherent diff
* [ ] Lint + typecheck + tests pass (or commands printed)
* [ ] No writes outside sandbox
* [ ] No Bash or Web\* unless explicitly allowed by the ticket
* [ ] Clear commit message text and minimal doc updates when applicable
