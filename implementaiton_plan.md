<tickets spec="1.0">

  <ticket id="INF-001">
    <title>Initialize Python project skeleton</title>
    <objective>Create a Poetry-based Python 3.11 project with Textual TUI skeleton and smoke tests.</objective>
    <prerequisites>None</prerequisites>
    <working_directory>Repo root</working_directory>

    <tool_policy>
      <allowed>Read, Write, Edit, Glob, LS</allowed>
      <denied>Bash, WebSearch, WebFetch, MCP</denied>
      <write_sandbox>./</write_sandbox>
      <denied_paths>.env, .env.*, secrets/**</denied_paths>
    </tool_policy>

    <requirements>
      <requirement>Create pyproject.toml targeting Python &gt;=3.11; dependencies: textual, pydantic, aiofiles, markdown-it-py, mdformat, aiosqlite, pytest, ruff, mypy, typing-extensions.</requirement>
      <requirement>Create package skeleton: app/__init__.py and app/tui/app.py with minimal Textual App rendering “Brainstorm Buddy”.</requirement>
      <requirement>Create tests/test_smoke.py asserting package importability.</requirement>
      <requirement>Update README.md with Poetry commands (install, lint, typecheck, tests, run).</requirement>
    </requirements>

    <tasks>
      <step>Create pyproject.toml with project metadata and dependencies.</step>
      <step>Create app/__init__.py and app/tui/app.py (minimal App subclass).</step>
      <step>Add tests/test_smoke.py that imports app and asserts truthy sentinel.</step>
      <step>Amend README.md with exact commands.</step>
      <step>Show the full diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>pyproject.toml is valid TOML and includes required deps.</criterion>
      <criterion>app/tui/app.py launches a minimal Textual app (manual check).</criterion>
      <criterion>tests/test_smoke.py imports app without errors.</criterion>
      <criterion>README lists Poetry commands clearly.</criterion>
    </acceptance_criteria>

    <validation>
      <instruction>Print the exact commands a human should run: "poetry install", "poetry run ruff .", "poetry run mypy .", "poetry run pytest -q", "poetry run python -m app.tui.app".</instruction>
      <artifact_check>Verify files exist at the specified paths.</artifact_check>
    </validation>

    <deliverables>
      <file>pyproject.toml</file>
      <file>app/__init__.py</file>
      <file>app/tui/app.py</file>
      <file>tests/test_smoke.py</file>
      <file>README.md</file>
    </deliverables>
  </ticket>

  <ticket id="INF-002">
    <title>Repo hygiene: ruff, mypy, pytest configuration and pre-commit</title>
    <objective>Add strict linting, typing, and testing config; optional pre-commit.</objective>
    <prerequisites>INF-001</prerequisites>
    <working_directory>Repo root</working_directory>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, WebSearch, WebFetch, MCP</denied>
    </tool_policy>

    <requirements>
      <requirement>Add ruff, mypy (--strict), and pytest configuration blocks to pyproject.toml.</requirement>
      <requirement>Create .pre-commit-config.yaml with ruff (and optional formatter) hooks.</requirement>
      <requirement>Update README.md with quality command section.</requirement>
    </requirements>

    <tasks>
      <step>Amend pyproject.toml with [tool.ruff], [tool.mypy], [tool.pytest.ini_options].</step>
      <step>Create .pre-commit-config.yaml referencing ruff.</step>
      <step>Update README quality commands.</step>
      <step>Show the full diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Configs present and syntactically valid; no conflicting settings.</criterion>
      <criterion>README lists lint/type/test commands.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm presence of config sections and .pre-commit-config.yaml.</artifact_check>
    </validation>

    <deliverables>
      <file>pyproject.toml</file>
      <file>.pre-commit-config.yaml</file>
      <file>README.md</file>
    </deliverables>
  </ticket>

  <ticket id="CFG-003">
    <title>Pydantic settings loader</title>
    <objective>Implement Settings with env overrides and helper loader.</objective>
    <prerequisites>INF-001</prerequisites>
    <working_directory>Repo root</working_directory>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, WebSearch, WebFetch</denied>
    </tool_policy>

    <requirements>
      <requirement>Create app/core/config.py with class Settings(BaseSettings).</requirement>
      <requirement>Fields: data_dir="projects", exports_dir="exports", log_dir="logs", enable_web_tools=False.</requirement>
      <requirement>Provide load_settings() that returns a cached singleton instance.</requirement>
      <requirement>Create tests/test_config.py covering defaults and env overrides (via monkeypatching os.environ in tests).</requirement>
    </requirements>

    <tasks>
      <step>Implement Settings and load_settings().</step>
      <step>Add tests for default values and for env override precedence.</step>
      <step>Show the full diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>All settings default correctly when no env vars set.</criterion>
      <criterion>Env overrides reflect in returned Settings.</criterion>
    </acceptance_criteria>

    <validation>
      <instruction>Print "poetry run pytest -q" for a human to run locally.</instruction>
      <artifact_check>Confirm app/core/config.py and tests/test_config.py exist.</artifact_check>
    </validation>

    <deliverables>
      <file>app/core/config.py</file>
      <file>tests/test_config.py</file>
    </deliverables>
  </ticket>

  <ticket id="FS-004">
    <title>Project scaffold utility</title>
    <objective>Create /projects/&lt;slug&gt;/ tree with seed files; idempotent.</objective>
    <prerequisites>INF-001, CFG-003</prerequisites>
    <working_directory>Repo root</working_directory>

    <tool_policy>
      <allowed>Read, Write, Edit, Glob, LS</allowed>
      <denied>Bash, WebSearch, WebFetch</denied>
    </tool_policy>

    <requirements>
      <requirement>Implement scaffold_project(slug: str, base: Path = "projects") -&gt; Path.</requirement>
      <requirement>Dirs: elements/, research/, exports/.</requirement>
      <requirement>Files: project.yaml, kernel.md, outline.md (with minimal headers/frontmatter).</requirement>
      <requirement>Idempotent: no error and no duplicate content on re-run.</requirement>
      <requirement>Unit tests in tests/test_scaffold.py.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/files/scaffold.py with helpers.</step>
      <step>Add tests verifying structure and idempotency.</step>
      <step>Show the full diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Calling scaffold twice yields identical filesystem state.</criterion>
      <criterion>All required paths exist after first run.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm directory and file presence in a temp folder (document steps).</artifact_check>
    </validation>

    <deliverables>
      <file>app/files/scaffold.py</file>
      <file>tests/test_scaffold.py</file>
    </deliverables>
  </ticket>

  <ticket id="LLM-006">
    <title>Claude client interface + Fake stream</title>
    <objective>Provide an async streaming interface and a deterministic Fake implementation.</objective>
    <prerequisites>INF-001</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Define Event variants: TextDelta, ToolUseStart, ToolUseEnd, MessageDone (typed).</requirement>
      <requirement>Interface: ClaudeClient.stream(prompt, system_prompt, allowed_tools, denied_tools, permission_mode, cwd) -&gt; AsyncIterator[Event].</requirement>
      <requirement>FakeClaudeClient: yields two TextDelta then MessageDone.</requirement>
      <requirement>Unit tests in tests/test_llm_fake.py.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/llm/claude_client.py with types and FakeClaudeClient.</step>
      <step>Add tests consuming the stream and asserting order.</step>
      <step>Show the diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Fake stream yields events in expected order and shape.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm file presence and test coverage.</artifact_check>
    </validation>

    <deliverables>
      <file>app/llm/claude_client.py</file>
      <file>tests/test_llm_fake.py</file>
    </deliverables>
  </ticket>

  <ticket id="POL-010">
    <title>Session policy registry</title>
    <objective>Define per-stage permissions and prompt paths.</objective>
    <prerequisites>LLM-006</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Create dataclass SessionPolicy with fields: stage, system_prompt_path, allowed_tools, denied_tools, write_roots, permission_mode, web_allow(list).</requirement>
      <requirement>Implement get_policy(stage: str) -&gt; SessionPolicy with defaults:
        clarify (Read only, no writes/web),
        kernel/outline (Write to projects/**, no web),
        research (Write to projects/**, optional web, no Bash),
        synthesis (Write to projects/**, no web).
      </requirement>
      <requirement>Unit tests in tests/test_policies.py.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/llm/sessions.py and (if needed) app/core/models.py.</step>
      <step>Add tests covering all stages and invalid stage error.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Policies match definitions exactly.</criterion>
      <criterion>Invalid stage raises informative exception.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm prompt paths reference app/llm/prompts/*.md (placeholders acceptable).</artifact_check>
    </validation>

    <deliverables>
      <file>app/llm/sessions.py</file>
      <file>app/core/models.py</file>
      <file>tests/test_policies.py</file>
    </deliverables>
  </ticket>

  <ticket id="PERM-011">
    <title>Project .claude settings and hook stubs</title>
    <objective>Write deny-first .claude/settings.json and placeholder hooks.</objective>
    <prerequisites>POL-010</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit, LS</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Function write_project_settings(repo_root=".") creates .claude/settings.json.</requirement>
      <requirement>Allow Read/Edit/Write; deny Bash/Web*; deny .env*, secrets/**; set hook entries.</requirement>
      <requirement>Create .claude/hooks/gate.py and .claude/hooks/format_md.py with TODO bodies.</requirement>
      <requirement>Unit tests validate JSON shape and file creation.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/permissions/settings_writer.py.</step>
      <step>Create hook placeholders.</step>
      <step>Add tests in tests/test_settings_writer.py.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>.claude/settings.json exists and matches schema.</criterion>
      <criterion>Hook files exist and are referenced in settings.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Open settings JSON and verify keys/paths.</artifact_check>
    </validation>

    <deliverables>
      <file>app/permissions/settings_writer.py</file>
      <file>.claude/settings.json</file>
      <file>.claude/hooks/gate.py</file>
      <file>.claude/hooks/format_md.py</file>
      <file>tests/test_settings_writer.py</file>
    </deliverables>
  </ticket>

  <ticket id="PRM-012">
    <title>Stage system prompts (clarify, kernel, outline)</title>
    <objective>Create concise prompts under app/llm/prompts/ using tag structure.</objective>
    <prerequisites>POL-010</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>clarify.md: 3–7 numbered questions; no advice; single screen.</requirement>
      <requirement>kernel.md: produce Idea Kernel sections; propose diff for projects/&lt;slug&gt;/kernel.md.</requirement>
      <requirement>outline.md: propose 6–10 workstreams (scope + 3–6 driving questions); propose diffs for outline.md and elements/*.md.</requirement>
      <requirement>Use &lt;instructions&gt;, &lt;context&gt;, &lt;format&gt; tags.</requirement>
    </requirements>

    <tasks>
      <step>Create three prompt files with the required content.</step>
      <step>Show full file contents.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Prompts are concise (≈200–300 words each) and avoid web or shell references.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm file existence and tag structure.</artifact_check>
    </validation>

    <deliverables>
      <file>app/llm/prompts/clarify.md</file>
      <file>app/llm/prompts/kernel.md</file>
      <file>app/llm/prompts/outline.md</file>
    </deliverables>
  </ticket>

  <ticket id="UI-013">
    <title>Textual shell (three-pane) + command palette stub</title>
    <objective>Layout-only TUI with left tree, main panel, right context cards, and palette.</objective>
    <prerequisites>INF-001</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit, Glob, LS</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Three-pane layout scaffold; no business logic.</requirement>
      <requirement>Palette lists stub actions: new project, clarify, kernel, outline, research import, synthesis, export.</requirement>
      <requirement>Import-only test to ensure modules load.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/tui/app.py and views/widgets stubs.</step>
      <step>Add tests/test_tui_imports.py (import checks only).</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>App launches and renders three panes (manual check).</criterion>
      <criterion>Palette opens with listed actions.</criterion>
    </acceptance_criteria>

    <validation>
      <instruction>Print "poetry run python -m app.tui.app" for manual run.</instruction>
    </validation>

    <deliverables>
      <file>app/tui/app.py</file>
      <file>app/tui/views/*</file>
      <file>app/tui/widgets/*</file>
      <file>tests/test_tui_imports.py</file>
    </deliverables>
  </ticket>

  <ticket id="DOC-014">
    <title>Markdown IO and atomic diff/patch</title>
    <objective>Create read/write utilities and atomic patch application.</objective>
    <prerequisites>INF-001</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>read_md(path) -&gt; str; write_md(path, text) -&gt; None.</requirement>
      <requirement>compute_patch(old,new) -&gt; Patch; apply_patch(path, patch) atomic (temp then replace).</requirement>
      <requirement>Unit tests: unchanged, insert, replace, simple multi-file helper.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/files/mdio.py and app/files/diff.py.</step>
      <step>Add tests/test_diff.py.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Patches apply atomically and idempotently.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm functions exist and tests cover scenarios.</artifact_check>
    </validation>

    <deliverables>
      <file>app/files/mdio.py</file>
      <file>app/files/diff.py</file>
      <file>tests/test_diff.py</file>
    </deliverables>
  </ticket>

  <ticket id="UI-015">
    <title>Clarify stage integration (Fake client)</title>
    <objective>Start Clarify session and render streamed numbered questions.</objective>
    <prerequisites>LLM-006, PRM-012, UI-013</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Use FakeClaudeClient with clarify.md as system prompt.</requirement>
      <requirement>Render 3–7 numbered questions in the main panel.</requirement>
      <requirement>No filesystem writes or web calls.</requirement>
    </requirements>

    <tasks>
      <step>Wire a "Clarify" action that launches a session and streams deltas into the view.</step>
      <step>Provide minimal formatting for numbered output.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Triggering Clarify shows numbered questions; no file changes.</criterion>
    </acceptance_criteria>

    <validation>
      <instruction>Print manual run steps.</instruction>
    </validation>

    <deliverables>
      <file>app/tui/views/session.py (or equivalent controller)</file>
    </deliverables>
  </ticket>

  <ticket id="DOC-016">
    <title>Kernel stage with diff gate</title>
    <objective>Generate proposed kernel.md, show diff, apply atomically on approval.</objective>
    <prerequisites>POL-010, PRM-012, DOC-014, FS-004</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Use kernel.md system prompt; propose full Kernel markdown.</requirement>
      <requirement>Compute diff vs projects/&lt;slug&gt;/kernel.md; show side-by-side preview.</requirement>
      <requirement>Apply atomically only on approval; rollback on failure.</requirement>
    </requirements>

    <tasks>
      <step>Build session call; capture proposed text.</step>
      <step>Integrate diff/patch utilities; implement approval gate.</step>
      <step>Implement error surface and rollback.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Accept → kernel.md written atomically; Reject → unchanged.</criterion>
      <criterion>Clear user feedback on success/failure.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Verify resulting file and diff preview behavior.</artifact_check>
    </validation>

    <deliverables>
      <file>Updated TUI handlers and helpers</file>
    </deliverables>
  </ticket>

  <ticket id="DOC-017">
    <title>Outline and workstream stubs with batch apply</title>
    <objective>Propose outline.md and elements/*.md and apply as one transaction.</objective>
    <prerequisites>DOC-016</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit, Glob</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Aggregate multiple proposed files in memory and show combined diff.</requirement>
      <requirement>Apply all-or-none atomically; rollback on any write failure.</requirement>
    </requirements>

    <tasks>
      <step>Implement batch diff builder and preview.</step>
      <step>Implement transactional write using temp workspace then move.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Partial failure leaves filesystem unchanged.</criterion>
      <criterion>Success writes all target files.</criterion>
    </acceptance_criteria>

    <validation>
      <instruction>Describe a manual failure injection for verification.</instruction>
    </validation>

    <deliverables>
      <file>Batch apply utility</file>
      <file>Updated TUI flow</file>
    </deliverables>
  </ticket>

  <ticket id="AGT-020">
    <title>Subagent spec loader + seed agents</title>
    <objective>Load .claude/agents/*.md with YAML frontmatter and create researcher/critic/architect.</objective>
    <prerequisites>POL-010</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit, Glob, LS</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Frontmatter keys: name, description, tools(optional).</requirement>
      <requirement>Body is system prompt (markdown text).</requirement>
      <requirement>Validation errors are explicit and actionable.</requirement>
      <requirement>Seed three agent files with minimal roles.</requirement>
      <requirement>Unit tests in tests/test_agents_loader.py.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/llm/agents.py loader returning AgentSpec objects.</step>
      <step>Create .claude/agents/researcher.md, critic.md, architect.md.</step>
      <step>Add tests covering valid/invalid cases.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Valid specs load; invalid specs raise clear errors.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm files and test coverage.</artifact_check>
    </validation>

    <deliverables>
      <file>app/llm/agents.py</file>
      <file>.claude/agents/researcher.md</file>
      <file>.claude/agents/critic.md</file>
      <file>.claude/agents/architect.md</file>
      <file>tests/test_agents_loader.py</file>
    </deliverables>
  </ticket>

  <ticket id="AGT-021">
    <title>Agent invocation and policy merge</title>
    <objective>Select agent per session; merge agent tools with stage policy (deny wins).</objective>
    <prerequisites>AGT-020, POL-010</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Merge logic: final_allowed = intersection(stage_allowed, agent_requested); apply stage/global denies last.</requirement>
      <requirement>UI exposes agent selection and displays final tool set before starting session.</requirement>
      <requirement>Unit tests for merge logic.</requirement>
    </requirements>

    <tasks>
      <step>Implement merge function and integrate into session creation.</step>
      <step>Add tests in tests/test_policy_merge.py.</step>
      <step>Update UI to select agent and preview final tools.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Denied tools remain denied regardless of agent request.</criterion>
      <criterion>Final tool list visible to user before run.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm tests for edge cases (empty agent tools, overlapping lists).</artifact_check>
    </validation>

    <deliverables>
      <file>Updated session logic</file>
      <file>tests/test_policy_merge.py</file>
      <file>UI update</file>
    </deliverables>
  </ticket>

  <ticket id="DB-030">
    <title>Research DB (SQLite + FTS)</title>
    <objective>Create findings database with FTS and CRUD API.</objective>
    <prerequisites>INF-001</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Schema: findings(id uuid, url text, source_type text, claim text, evidence text, confidence real, tags text, workstream text, retrieved_at text).</requirement>
      <requirement>FTS index on claim and evidence.</requirement>
      <requirement>CRUD and FTS search methods.</requirement>
      <requirement>Unit tests in tests/test_research_db.py.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/research/db.py with init/migrate and APIs.</step>
      <step>Add tests for insert/update/delete/search/FTS.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>FTS queries return expected rows.</criterion>
      <criterion>CRUD operations persist correctly.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Open schema via code and assert FTS presence in tests.</artifact_check>
    </validation>

    <deliverables>
      <file>app/research/db.py</file>
      <file>tests/test_research_db.py</file>
    </deliverables>
  </ticket>

  <ticket id="RES-031">
    <title>Ingest parser for findings</title>
    <objective>Normalize markdown or JSON input into Finding records with dedupe.</objective>
    <prerequisites>DB-030</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>parse_findings(text: str, default_workstream: str) -&gt; list[Finding].</requirement>
      <requirement>Support markdown bullets and simple JSON arrays.</requirement>
      <requirement>Dedupe by (normalized_claim, url); confidence ∈ [0,1].</requirement>
      <requirement>Unit tests for both input formats and dedupe.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/research/ingest.py with parser and dedupe helper.</step>
      <step>Add tests/test_ingest.py.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Mixed inputs parse; duplicates removed deterministically.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm test coverage for edge cases (missing url, empty tags).</artifact_check>
    </validation>

    <deliverables>
      <file>app/research/ingest.py</file>
      <file>tests/test_ingest.py</file>
    </deliverables>
  </ticket>

  <ticket id="RES-032">
    <title>External chatbot import (TUI)</title>
    <objective>Paste external responses and store parsed findings; render table.</objective>
    <prerequisites>RES-031, DB-030, UI-013</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Research view paste area; on submit parse→store→refresh.</requirement>
      <requirement>Show counts: added, skipped (duplicates).</requirement>
      <requirement>Table columns: claim, url, confidence, tags, workstream.</requirement>
    </requirements>

    <tasks>
      <step>Implement paste handler and DB integration.</step>
      <step>Update DataTable rendering and refresh path.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>User sees confirmation with counts and updated table.</criterion>
    </acceptance_criteria>

    <validation>
      <instruction>Provide manual steps to paste sample text and verify rows.</instruction>
    </validation>

    <deliverables>
      <file>app/tui/views/research.py</file>
    </deliverables>
  </ticket>

  <ticket id="UI-033">
    <title>Findings table filters</title>
    <objective>Filter by workstream, tags, and min confidence; persist during session.</objective>
    <prerequisites>RES-032</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Filter state in memory; sorting by retrieved_at desc.</requirement>
      <requirement>Logic unit tests (UI smoke test acceptable).</requirement>
    </requirements>

    <tasks>
      <step>Implement filter state and apply to DB query results.</step>
      <step>Add tests/test_filters.py.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Changing filters updates table; tests pass.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm filter values affect result sets in tests.</artifact_check>
    </validation>

    <deliverables>
      <file>app/tui/views/research.py</file>
      <file>tests/test_filters.py</file>
    </deliverables>
  </ticket>

  <ticket id="SEC-034">
    <title>Domain allow/deny policy editor</title>
    <objective>Manage domain allow/deny lists in project settings (no web calls yet).</objective>
    <prerequisites>PERM-011</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Add web_allow and web_deny lists to settings schema and writer.</requirement>
      <requirement>Small UI panel to add/remove domains; persist via settings_writer.</requirement>
    </requirements>

    <tasks>
      <step>Extend settings model + writer to support domain lists.</step>
      <step>Implement UI to manage lists.</step>
      <step>Show diff and example resulting .claude/settings.json snippet.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Saved settings include edited domain lists.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Open resulting JSON and verify domains present.</artifact_check>
    </validation>

    <deliverables>
      <file>app/permissions/policy.py (or extend writer)</file>
      <file>UI update (settings/agents view)</file>
    </deliverables>
  </ticket>

  <ticket id="PERM-051">
    <title>Hook hardening: gate.py and format_md.py</title>
    <objective>Implement PreToolUse blocking and PostToolUse markdown formatting.</objective>
    <prerequisites>PERM-011, DOC-014</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>gate.py reads JSON from stdin: {tool_name, target_path, args, url?}; deny on Bash, path escape, sensitive paths, or disallowed domain.</requirement>
      <requirement>Exit code 2 on deny; print reason to stdout/stderr.</requirement>
      <requirement>format_md.py formats Markdown content after Write/Edit using mdformat API; no shell calls.</requirement>
      <requirement>Unit tests calling helper functions for both scripts.</requirement>
    </requirements>

    <tasks>
      <step>Implement pure-Python helpers and import them in scripts.</step>
      <step>Write tests covering allowed/denied scenarios and formatting.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Malicious paths and disallowed domains are blocked.</criterion>
      <criterion>Markdown files are pretty-formatted deterministically.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm exit codes and messages from helper invocations in tests.</artifact_check>
    </validation>

    <deliverables>
      <file>.claude/hooks/gate.py</file>
      <file>.claude/hooks/format_md.py</file>
      <file>tests for hook helpers</file>
    </deliverables>
  </ticket>

  <ticket id="SYN-040">
    <title>Synthesis (architect + critic loop)</title>
    <objective>Generate element requirements with acceptance criteria; no web; diff gate.</objective>
    <prerequisites>PRM-012, AGT-021, DB-030, DOC-014</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Create app/llm/prompts/synthesis.md with headings: Decisions, Requirements, Open Questions, Risks &amp; Mitigations, Acceptance Criteria.</requirement>
      <requirement>Read kernel.md and findings for selected workstream; propose edits to elements/&lt;slug&gt;.md.</requirement>
      <requirement>Optional critic pass (read-only) to flag issues before apply.</requirement>
      <requirement>Diff preview; atomic apply on approval.</requirement>
    </requirements>

    <tasks>
      <step>Create synthesis.md prompt.</step>
      <step>Implement synthesis flow (gather inputs, propose, preview, apply).</step>
      <step>Integrate optional critic review (non-blocking).</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Deterministic section headings present.</criterion>
      <criterion>Apply only after approval; atomic write semantics honored.</criterion>
    </acceptance_criteria>

    <validation>
      <instruction>Document manual steps to select a workstream and verify resulting file content.</instruction>
    </validation>

    <deliverables>
      <file>app/llm/prompts/synthesis.md</file>
      <file>Updated synthesis TUI flow</file>
    </deliverables>
  </ticket>

  <ticket id="EXP-042">
    <title>Exporter bundle</title>
    <objective>Produce exports/requirements.md and exports/research.{jsonl,csv} atomically.</objective>
    <prerequisites>DB-030, DOC-017, SYN-040</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit, Glob, LS</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Concatenate Kernel + Outline + elements in stable order into requirements.md.</requirement>
      <requirement>Serialize findings to JSONL and CSV with headers.</requirement>
      <requirement>Atomic writes; idempotent re-runs.</requirement>
      <requirement>Unit tests in tests/test_exporter.py.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/export/exporter.py.</step>
      <step>Add tests verifying file contents and idempotency.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Re-running export yields identical outputs if inputs unchanged.</criterion>
      <criterion>CSV headers match schema fields.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Confirm export files exist and contain expected sections/rows.</artifact_check>
    </validation>

    <deliverables>
      <file>app/export/exporter.py</file>
      <file>tests/test_exporter.py</file>
    </deliverables>
  </ticket>

  <ticket id="RUN-052">
    <title>Headless runner (no web)</title>
    <objective>Add python -m app.cli to run new/import-research/export without TUI.</objective>
    <prerequisites>FS-004, EXP-042</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>Commands: new &lt;slug&gt;; import-research &lt;slug&gt; &lt;file&gt;; export &lt;slug&gt;.</requirement>
      <requirement>Reuse internal modules; no shelling out.</requirement>
      <requirement>Unit tests for argument parsing and function dispatch.</requirement>
    </requirements>

    <tasks>
      <step>Implement app/cli.py with argparse/Typer.</step>
      <step>Add tests/test_cli.py.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>CLI routes to the correct internal functions with expected side effects.</criterion>
    </acceptance_criteria>

    <validation>
      <instruction>Print example invocations for a human to run locally.</instruction>
    </validation>

    <deliverables>
      <file>app/cli.py</file>
      <file>tests/test_cli.py</file>
    </deliverables>
  </ticket>

  <ticket id="OBS-053">
    <title>Usage metrics panel</title>
    <objective>Track counts and elapsed time per stage; show in Home view.</objective>
    <prerequisites>UI-013</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>app/core/state.py stores counters and durations for stages.</requirement>
      <requirement>Render a small metrics panel; no persistence required.</requirement>
    </requirements>

    <tasks>
      <step>Implement state container and hooks to increment on stage start/stop.</step>
      <step>Add UI panel in home view.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Metrics increment during manual navigation.</criterion>
    </acceptance_criteria>

    <validation>
      <instruction>Document manual steps to exercise a couple of stages and observe counters.</instruction>
    </validation>

    <deliverables>
      <file>app/core/state.py</file>
      <file>app/tui/views/home.py (or metrics view)</file>
    </deliverables>
  </ticket>

  <ticket id="QA-064">
    <title>Deterministic E2E with Fake client</title>
    <objective>End-to-end test: scaffold → kernel → outline → synthesis → export using Fake streams.</objective>
    <prerequisites>All prior stage wiring</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit, Glob, LS</allowed>
      <denied>Bash, Web*</denied>
    </tool_policy>

    <requirements>
      <requirement>tests/test_e2e_fake.py uses pytest tmp_path workspace.</requirement>
      <requirement>Deterministic Fake outputs for Kernel/Outline/Synthesis.</requirement>
      <requirement>Assert presence and shape of generated files and exports.</requirement>
    </requirements>

    <tasks>
      <step>Compose an E2E flow invoking internal functions with FakeClaudeClient.</step>
      <step>Add assertions for expected markers/headings and export rows.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>E2E passes consistently across runs.</criterion>
    </acceptance_criteria>

    <validation>
      <instruction>Print "poetry run pytest -q tests/test_e2e_fake.py" for a human.</instruction>
    </validation>

    <deliverables>
      <file>tests/test_e2e_fake.py</file>
    </deliverables>
  </ticket>

  <!-- Optional: tightly scoped test execution via Bash with strict gating -->
  <ticket id="OPS-TEST" optional="true">
    <title>Enable limited Bash to run quality gates</title>
    <objective>Permit only poetry run (ruff|mypy|pytest) commands through gate.py.</objective>
    <prerequisites>PERM-051</prerequisites>

    <tool_policy>
      <allowed>Read, Write, Edit, Bash(limited)</allowed>
      <denied>Web*</denied>
      <bash_allow_regex>^poetry( run)? (ruff|mypy|pytest)( .*)?$</bash_allow_regex>
    </tool_policy>

    <requirements>
      <requirement>Update .claude/settings.json and gate.py to allow only the regex-defined commands; block everything else.</requirement>
      <requirement>Document usage in README.</requirement>
    </requirements>

    <tasks>
      <step>Modify gate.py to inspect command string and enforce regex.</step>
      <step>Amend settings to reflect limited Bash allowance.</step>
      <step>Update README quality section to note automated agent-run commands.</step>
      <step>Show diff.</step>
    </tasks>

    <acceptance_criteria>
      <criterion>Allowed commands pass; unrelated Bash invocations are blocked with exit code 2 and reason.</criterion>
    </acceptance_criteria>

    <validation>
      <artifact_check>Demonstrate (in tests or documented examples) acceptance vs. rejection cases.</artifact_check>
    </validation>

    <deliverables>
      <file>.claude/settings.json</file>
      <file>.claude/hooks/gate.py</file>
      <file>README.md</file>
    </deliverables>
  </ticket>

</tickets>
