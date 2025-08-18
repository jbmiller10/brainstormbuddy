Implementation Plan
Phase 0 — Foundations
[INF‑001] Initialize Python project skeleton

Objective: Create a Poetry project with minimal structure, Textual dependency, and smoke tests.

Prerequisites: None.

Tool policy:

Allowed: Read, Write, Edit, Glob, LS

Denied: Bash, Web*

Requirements

pyproject.toml with Python >=3.11, deps: textual, pydantic, aiofiles, markdown-it-py, mdformat, aiosqlite, pytest, ruff, mypy, typing-extensions.

Package root app/ with __init__.py.

app/tui/app.py minimal Textual App that renders a placeholder title.

tests/test_smoke.py that imports app and asserts importability.

Update README.md with run commands (see CLAUDE.md).

Tasks

Create pyproject.toml with sections for deps and basic tool configs (will be extended later).

Create app/__init__.py and app/tui/app.py with a minimal App subclass.

Add tests/test_smoke.py.

Update README.md with Poetry commands.

Acceptance criteria

Files exist with the specified names and content.

pyproject.toml is syntactically valid (toml).

Smoke test imports app (no runtime execution required).

Validation (no Bash)

Show the full diff.

Print the commands a human should run: poetry install, poetry run pytest -q.

Deliverables

pyproject.toml, app/…, tests/test_smoke.py, README.md.

[INF‑002] Repo hygiene: ruff, mypy, pytest config and pre‑commit

Objective: Add strict lint/type/test configuration.

Prerequisites: INF‑001.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Configure ruff, mypy (--strict), pytest inside pyproject.toml.

Optional: .pre-commit-config.yaml with ruff, basic formatting.

Document quality commands in README.md.

Tasks

Edit pyproject.toml to add tool sections with reasonable defaults.

Add .pre-commit-config.yaml (do not run it; just create).

Update README quality section.

Acceptance criteria

Config sections present; no conflicting options.

README shows exact commands.

Validation

Show diff only.

Deliverables

Updated pyproject.toml, .pre-commit-config.yaml, README.md.

[CFG‑003] Settings loader (app/core/config.py)

Objective: Pydantic settings with env overrides.

Prerequisites: INF‑001.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Class Settings with fields:
data_dir="projects", exports_dir="exports", log_dir="logs", enable_web_tools=False.

load_settings() returns a cached instance.

Unit tests for defaults and env override (simulate via monkeypatch).

Tasks

Implement app/core/config.py.

Add tests/test_config.py.

Acceptance criteria

Tests (logic) demonstrate defaults and overrides.

Validation

Show diff + the exact pytest command for humans.

Deliverables

app/core/config.py, tests/test_config.py.

[FS‑004] Project scaffold utility (app/files/scaffold.py)

Objective: Create /projects/<slug>/ structure with seed files.

Prerequisites: INF‑001, CFG‑003.

Tool policy: Allowed Read, Write, Edit, Glob, LS; Denied Bash, Web*.

Requirements

Function scaffold_project(slug: str, base: Path = Path("projects")) -> Path.

Create dirs: elements/, research/, exports/.

Create files with minimal frontmatter or headings: project.yaml, kernel.md, outline.md.

Idempotent: safe on re‑run.

Tasks

Implement function and helpers.

Add tests/test_scaffold.py (existence + idempotency).

Acceptance criteria

Running twice does not raise; outputs unchanged.

Validation

Show diff + human commands.

Deliverables

app/files/scaffold.py, tests/test_scaffold.py.

Phase 1 — LLM + Policies + Prompts
[LLM‑006] Claude client interface + Fake (app/llm/claude_client.py)

Objective: Unified async streaming interface and a deterministic Fake.

Prerequisites: INF‑001.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Define Event variants: TextDelta, ToolUseStart, ToolUseEnd, MessageDone (dataclasses/TypedDict).

Interface ClaudeClient.stream(prompt, system_prompt, allowed_tools, denied_tools, permission_mode, cwd) -> AsyncIterator[Event].

FakeClaudeClient yields two text deltas and a done.

Tasks

Implement types and the fake client.

Add tests/test_llm_fake.py to assert ordering and content.

Acceptance criteria

Tests pass logically (no command execution required).

Validation

Show diff + human commands.

Deliverables

app/llm/claude_client.py, tests/test_llm_fake.py.

[POL‑010] Session policy registry (app/llm/sessions.py)

Objective: Codify per‑stage permissions and prompts.

Prerequisites: LLM‑006.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Dataclass SessionPolicy with: stage, system_prompt_path, allowed_tools, denied_tools, write_roots, permission_mode, web_allow: list[str].

Registry get_policy(stage: str) -> SessionPolicy with defaults:

clarify: Read only, no web, no writes.

kernel/outline: Write allowed to projects/**, no web.

research: Write to projects/**, web allowed if enable_web_tools, no Bash.

synthesis: Write to projects/**, no web.

Tasks

Implement data model and the policy registry.

Add tests/test_policies.py.

Acceptance criteria

Policies match definitions; invalid stage raises informative error.

Validation

Show diff + human commands.

Deliverables

app/llm/sessions.py, app/core/models.py (if needed), tests.

[PERM‑011] Project .claude settings + hook stubs

Objective: Generate deny‑first settings and hook placeholders.

Prerequisites: POL‑010.

Tool policy: Allowed Read, Write, Edit, LS; Denied Bash, Web*.

Requirements

Function write_project_settings(repo_root=Path(".")) writes .claude/settings.json.

Defaults: allow Read/Edit/Write, deny Bash/Web*, deny .env* & secrets/**.

Configure hooks:

PreToolUse → .claude/hooks/gate.py (to implement later).

PostToolUse → .claude/hooks/format_md.py (to implement later).

Create both hook files with TODO content.

Tasks

Implement writer and simple JSON schema validation.

Add tests/test_settings_writer.py.

Acceptance criteria

Files exist with correct keys; paths are relative; schema validated in test.

Validation

Show diff + human commands.

Deliverables

app/permissions/settings_writer.py, .claude/settings.json (if writing during test), .claude/hooks/*.py placeholders, tests.

[PRM‑012] Stage prompts (clarify, kernel, outline)

Objective: Author short, explicit system prompts under app/llm/prompts/.

Prerequisites: POL‑010.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

clarify.md: ask 3–7 numbered clarifying questions; no advice; one screen.

kernel.md: synthesize Kernel (Problem, Users, Value, Constraints, Risks, Success, Out‑of‑scope); propose diff for projects/<slug>/kernel.md.

outline.md: propose 6–10 workstreams with a one‑sentence scope and 3–6 driving questions each; propose diffs for outline.md and elements/*.md.

Each uses <instructions>, <context>, <format> tags.

Tasks

Create the three prompt files.

Ensure they do not reference web tools.

Acceptance criteria

Files exist, concise, and structured.

Validation

Show full file contents.

Deliverables

app/llm/prompts/*.md.

Phase 2 — TUI shell + IO
[UI‑013] Textual shell (3‑pane) + command palette stub

Objective: Layout only; no business logic.

Prerequisites: INF‑001.

Tool policy: Allowed Read, Write, Edit, Glob, LS; Denied Bash, Web*.

Requirements

Left rail: file tree view (placeholder) for projects/ and docs.

Main: editor/viewer placeholder.

Right: context cards placeholder.

Command palette opens with : and lists stub actions (new project, clarify, kernel, outline, research import, synthesis, export).

Tasks

Implement app.tui.app.App with three regions.

Add views/ and widgets/ placeholders.

Provide tests/test_tui_imports.py to assert views import.

Acceptance criteria

App runs (manually) and renders three panes; palette opens and lists stubs.

Validation

Show diff + human run commands.

Deliverables

app/tui/app.py, app/tui/views/*, app/tui/widgets/*, tests.

[DOC‑014] Markdown IO + atomic diff/patch

Objective: Read/write Markdown and apply patches atomically.

Prerequisites: INF‑001.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

read_md(path) -> str, write_md(path, text) -> None.

compute_patch(old, new) -> Patch, apply_patch(path, patch) -> None using temp file then replace.

Unit tests: unchanged case, insert, replace, multi‑file apply helper.

Tasks

Implement app/files/mdio.py, app/files/diff.py.

Add tests/test_diff.py.

Acceptance criteria

Patch is idempotent; writes are atomic.

Validation

Show diff + human commands.

Deliverables

Source + tests.

Phase 3 — Stage wiring (no web)
[UI‑015] Clarify stage integration (Fake client)

Objective: Start a Clarify session and render streamed questions.

Prerequisites: LLM‑006, PRM‑012, UI‑013.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Use FakeClaudeClient to simulate streaming deltas from clarify.md.

Render 3–7 numbered questions in main panel.

No writes attempted.

Tasks

Wire a “Clarify” command to create a session with the clarifier system prompt.

Stream events to the UI; accumulate output with basic formatting.

Acceptance criteria

Triggering Clarify shows numbered questions; no FS changes.

Validation

Show diff; print manual steps to run TUI and where to click/press.

Deliverables

Updated session view/controller.

[DOC‑016] Kernel stage with diff gate

Objective: Generate proposed kernel.md, preview diff, and apply on approval.

Prerequisites: POL‑010, PRM‑012, DOC‑014, FS‑004.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Prompt from kernel.md file; produce proposed Kernel text.

Compute diff vs projects/<slug>/kernel.md.

Show side‑by‑side preview.

Apply atomically on approval; otherwise discard.

Tasks

Implement session creation for Kernel stage.

Integrate mdio + diff utils.

Add a rollback in case of file write failure.

Acceptance criteria

Accept → file written atomically; Reject → no change.

Errors are surfaced with a clear message.

Validation

Show diff + a small manual test plan.

Deliverables

Updated TUI handlers and helpers.

[DOC‑017] Outline + workstream stubs with batch apply

Objective: Propose outline.md and multiple elements/*.md, apply as a single transaction.

Prerequisites: DOC‑016.

Tool policy: Allowed Read, Write, Edit, Glob; Denied Bash, Web*.

Requirements

Collect multiple proposed files in memory.

Show a combined diff view.

Apply all or none with rollback.

Tasks

Implement batch diff computation.

Implement “Apply All” with a temporary workspace and move into place on success.

Acceptance criteria

Partial failures leave FS unchanged; success writes all.

Validation

Show diff + describe a manual failure injection scenario.

Deliverables

Batch apply utility + UI.

Phase 4 — Agents & Policy Merge
[AGT‑020] Subagent spec loader + seed agents

Objective: Load .claude/agents/*.md with YAML frontmatter; create three seed agents.

Prerequisites: POL‑010.

Tool policy: Allowed Read, Write, Edit, Glob, LS; Denied Bash, Web*.

Requirements

Frontmatter: name, description, optional tools array; body is the system prompt.

Validate fields; return AgentSpec objects.

Create files: researcher.md, critic.md, architect.md with minimal, clear roles.

Tasks

Implement loader in app/llm/agents.py.

Seed agent files.

Acceptance criteria

Invalid files fail with useful error; valid ones load.

Validation

Unit tests: tests/test_agents_loader.py.

Deliverables

Loader, tests, seed agent files.

[AGT‑021] Agent invocation & policy merge

Objective: Select an agent per session and merge requested tools with stage policy (deny wins).

Prerequisites: AGT‑020, POL‑010.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Merge logic: final_allowed = (stage_allowed ∩ agent_requested); denied list is authoritative.

UI: drop‑down or command to choose agent; display final tool set before run.

Tasks

Implement merge function with unit tests.

Wire selection UI; surface final policy before session.

Acceptance criteria

Denied tools remain denied; final set displayed.

Validation

Tests in tests/test_policy_merge.py; show screenshots or describe UI entry point.

Deliverables

Merge code, tests, UI changes.

Phase 5 — Research data (local; no web calls yet)
[DB‑030] Research DB (SQLite + FTS)

Objective: Persist findings with full‑text search.

Prerequisites: INF‑001.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Table: findings(id uuid, url text, source_type text, claim text, evidence text, confidence real, tags text, workstream text, retrieved_at text).

FTS on claim and evidence.

CRUD + FTS query API.

Unit tests.

Tasks

Implement app/research/db.py; create the DB in a provided path (not global).

Add tests for insert/search/update/delete and FTS filtering.

Acceptance criteria

FTS returns expected rows; updates persist.

Validation

Show diff + human commands.

Deliverables

DB module + tests.

[RES‑031] Ingest parser to Finding records

Objective: Normalize LLM or pasted text into atomic findings.

Prerequisites: DB‑030.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

parse_findings(text: str, default_workstream: str) -> list[Finding].

Accept Markdown bullets or simple JSON arrays.

Dedupe by (normalized_claim, url).

Tasks

Implement parser and a dedupe helper.

Unit tests covering MD and JSON inputs.

Acceptance criteria

Mixed inputs parse; duplicates removed; confidence ∈ [0,1].

Validation

Show diff + tests.

Deliverables

Parser + tests.

[RES‑032] External chatbot import (TUI)

Objective: Paste external responses and store findings.

Prerequisites: RES‑031, DB‑030, UI‑013.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Paste area in Research view.

On submit: parse to findings, write to DB, show counts (added/skipped).

Display table with columns: claim, url, confidence, tags, workstream.

Tasks

Implement paste UI and handler.

Wire to DB and table refresh.

Acceptance criteria

Visible feedback with counts; table updates immediately.

Validation

Show diff + manual steps.

Deliverables

Updated app/tui/views/research.py and any helpers.

[UI‑033] Findings table filters

Objective: Filter findings by workstream, tags, min confidence.

Prerequisites: RES‑032.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Filters persist for the session; sorting by retrieved_at desc.

Logic unit‑tested (UI can be smoke‑tested manually).

Tasks

Implement filter state and apply to DB results.

Add unit tests for filter logic.

Acceptance criteria

Changing filters updates table; logic tests pass.

Validation

Show diff + tests.

Deliverables

View updates + tests/test_filters.py.

Phase 6 — Domains & Hooks
[SEC‑034] Domain allow/deny policy editor

Objective: Manage domain allow/deny lists in project settings for future web fetch.

Prerequisites: PERM‑011.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

Data model additions to settings for web_allow and web_deny.

UI to add/remove domains; persist via settings_writer.

No network calls yet.

Tasks

Extend settings schema and writer.

Implement UI editor in settings/agents view.

Acceptance criteria

Persisted lists exist in .claude/settings.json.

Validation

Show diff + sample JSON snippet.

Deliverables

Policy code + UI.

[PERM‑051] Hook hardening (gate.py, format_md.py)

Objective: Implement PreToolUse and PostToolUse logic.

Prerequisites: PERM‑011, DOC‑014.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

gate.py: read JSON from stdin: {tool_name, target_path, args, url?}.

Deny if tool_name in {"Bash"} or path escapes repo or hits sensitive paths; if url present and domain not allowed, deny.

Exit code 2 to block; print reason.

format_md.py: if target is Markdown and tool is Write/Edit, run formatting via Python mdformat API on the file contents (no shell).

Tasks

Implement reusable helpers importable by tests.

Unit tests simulate payloads.

Acceptance criteria

Malicious paths and disallowed domains blocked; Markdown formatted.

Validation

Show diff + tests.

Deliverables

Hook scripts + tests.

Phase 7 — Synthesis & Export
[SYN‑040] Synthesis (architect + critic loop)

Objective: Generate requirements per workstream with acceptance criteria; no web.

Prerequisites: PRM‑012, AGT‑021, DB‑030, DOC‑014.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

app/llm/prompts/synthesis.md describing sections: Decisions, Requirements, Open Questions, Risks & Mitigations, Acceptance Criteria (testable).

Read kernel.md and findings for target workstream; propose elements/<slug>.md edits.

Show diff → approve → apply.

Tasks

Create synthesis prompt.

Implement flow to gather inputs and write element page atomically.

Optional: have critic agent review proposed text before apply (read‑only).

Acceptance criteria

Deterministic section headings; apply only after approval.

Validation

Show diff + manual flow.

Deliverables

Prompt + TUI flow.

[EXP‑042] Exporter (exports/requirements.md, exports/research.{jsonl,csv})

Objective: Build export bundle atomically.

Prerequisites: DB‑030, DOC‑017, SYN‑040.

Tool policy: Allowed Read, Write, Edit, Glob, LS; Denied Bash, Web*.

Requirements

Concatenate Kernel + Outline + elements in a stable order to requirements.md.

Serialize findings to research.jsonl and research.csv with headers.

Atomic writes; idempotent.

Tasks

Implement app/export/exporter.py.

Add tests/test_exporter.py.

Acceptance criteria

Re‑running export produces identical files (unless inputs changed).

CSV header matches fields.

Validation

Show diff + human commands.

Deliverables

Exporter + tests.

Phase 8 — Headless & Metrics
[RUN‑052] Minimal headless runner (python -m app.cli)

Objective: Run key flows without the TUI (no web).

Prerequisites: FS‑004, EXP‑042.

Tool policy: Allowed Read, Write, Edit; Denied Web*.

Bash: Allow for this ticket only to run commands inside the Python process if needed is not required; the runner is a Python module. Keep Bash denied.

Requirements

Commands:

new <slug> → scaffold project.

import-research <slug> <file> → parse and store findings.

export <slug> → write bundle.

Reuse the same modules as TUI; no duplication.

Tasks

Implement app/cli.py with argparse/Typer.

Unit tests for argument parsing and function calls.

Acceptance criteria

CLI functions perform as expected in tests (no shell).

Validation

Show diff + example invocations to be run by a human.

Deliverables

CLI + tests.

[OBS‑053] Usage metrics panel (local)

Objective: Track session counts and elapsed time per stage.

Prerequisites: UI‑013.

Tool policy: Allowed Read, Write, Edit; Denied Bash, Web*.

Requirements

app/core/state.py holds counters and durations.

Panel in Home view displays metrics.

No external calls; purely local.

Tasks

Implement state container and increment hooks at stage start/stop.

Render a simple metrics panel.

Acceptance criteria

Counts tick up during a manual session; no persistence required.

Validation

Show diff + manual check steps.

Deliverables

State + UI.

Phase 9 — E2E quality
[QA‑064] Deterministic E2E with Fake client

Objective: Verify scaffold → kernel → outline → synthesis → export in a temp workspace.

Prerequisites: All prior stage wiring.

Tool policy: Allowed Read, Write, Edit, Glob, LS; Denied Bash, Web*.

Requirements

Use pytest’s tmp_path; wire FakeClaudeClient deterministic outputs for Kernel/Outline/Synthesis.

Assert expected files exist and contain marker headings; exports produced.

Tasks

Add tests/test_e2e_fake.py to drive the sequence.

Provide small fixture text for deterministic outputs.

Acceptance criteria

Test passes locally with fake streams; stable across runs.

Validation

Show diff + human commands.

Deliverables

E2E test.

Optional tickets (enable tightly‑scoped test execution)

If you want agents to run tests/lint themselves:

[OPS‑TEST] Limited Bash for quality gates

Tool policy override: Allow Bash but restrict to commands that match the regex:
^poetry (run )?(ruff|mypy|pytest)( .*)?$

Requirements: Update .claude/settings.json and gate.py to allow only those exact commands; block everything else.

Acceptance: Agent can run poetry run ruff ., poetry run mypy ., poetry run pytest -q during tickets that request it; other shell usage is blocked.

Notes

Each ticket explicitly states tool policy; do not assume Bash or Web* are available unless the ticket grants them.

For any write: compute diff → show → apply atomically.

Keep prompts short and testable.
