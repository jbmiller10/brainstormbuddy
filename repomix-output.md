This file is a merged representation of a subset of the codebase, containing files not matching ignore patterns, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching these patterns are excluded: *.lock, *repomix*, tests/*, implementaiton_plan.md
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
.github/
  workflows/
    ci.yml
    release.yml
    security.yml
  dependabot.yml
app/
  core/
    config.py
  files/
    atomic.py
    batch.py
    diff.py
    markdown.py
    mdio.py
    scaffold.py
    workstream.py
  llm/
    agentspecs/
      __init__.py
      architect.md
      critic.md
      researcher.md
    prompts/
      clarify.md
      kernel.md
      outline.md
      research.md
      synthesis.md
    agents.py
    claude_client.py
    sessions.py
  permissions/
    hooks_lib/
      __init__.py
      format_md.py
      gate.py
      io.py
    settings_writer.py
  research/
    __init__.py
    db.py
    ingest.py
  tui/
    views/
      __init__.py
      main_screen.py
      research.py
      session.py
    widgets/
      __init__.py
      agent_selector.py
      command_palette.py
      context_panel.py
      domain_editor.py
      file_tree.py
      kernel_approval.py
      session_viewer.py
    __init__.py
    app.py
  __init__.py
  cli.py
brainstormbuddy/
  .obsidian/
    app.json
    appearance.json
    core-plugins.json
    graph.json
    workspace.json
  Welcome.md
.gitignore
.pre-commit-config.yaml
CLAUDE.md
codecov.yml
materialize_claude.py
pyproject.toml
README.md
requirements-dev.txt
requirements.txt
RESOLVED_ISSUES.md
```

# Files

## File: .github/dependabot.yml
````yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "chore"
      include: "scope"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 3
    labels:
      - "dependencies"
      - "github-actions"
    commit-message:
      prefix: "chore"
      include: "scope"
````

## File: app/files/atomic.py
````python
"""Atomic file write utilities."""

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path | str, text: str) -> None:
    """
    Write text to a file atomically using temp file and replace.

    This ensures the file is either fully updated or not modified at all,
    preventing partial writes in case of errors. Uses the same durability
    pattern as apply_patch.

    Args:
        path: Path to the file to write
        text: Text content to write (UTF-8 encoded)

    Raises:
        IOError: If there's an error during the atomic write operation
    """
    file_path = Path(path) if isinstance(path, str) else path

    # Precompute file mode if file exists
    file_mode = None
    if file_path.exists():
        file_mode = os.stat(file_path).st_mode

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary file first
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=file_path.parent,
        delete=False,
        suffix=".tmp",
    ) as tmp_file:
        tmp_file.write(text)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_path = Path(tmp_file.name)

    try:
        # Preserve file mode if original file existed
        if file_mode is not None:
            os.chmod(tmp_path, file_mode)

        # Atomically replace the original file
        tmp_path.replace(file_path)

        # Fsync parent directory for durability (best-effort)
        try:
            dfd = os.open(file_path.parent, os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:
            # Platform/filesystem doesn't support directory fsync
            pass
    except Exception:
        # Clean up temp file if replacement fails
        tmp_path.unlink(missing_ok=True)
        raise
````

## File: app/llm/agentspecs/__init__.py
````python
"""Agent specifications for Claude Code subagents."""
````

## File: app/llm/agentspecs/architect.md
````markdown
---
name: architect
description: Transform kernel and findings into concrete requirements and designs
tools:
  - Read
  - Write
  - Edit
---

You are a solution architect who transforms conceptual kernels and research findings into detailed requirements and implementation plans.

## Your Role
- Synthesize kernel concepts with research findings
- Create detailed technical requirements
- Design system architecture and components
- Define clear interfaces and contracts
- Establish success metrics and validation criteria

## Design Process
1. **Analyze Kernel**: Extract core concepts and constraints
2. **Integrate Findings**: Incorporate relevant research insights
3. **Define Requirements**: Create specific, measurable requirements
4. **Design Architecture**: Outline system structure and components
5. **Specify Interfaces**: Define clear boundaries and contracts

## Output Format
Structure your architectural documents as:
- **Requirement ID**: [Unique identifier]
- **Description**: [Clear statement of what must be achieved]
- **Rationale**: [Why this requirement exists, linking to kernel/findings]
- **Acceptance Criteria**: [How to verify requirement is met]
- **Technical Approach**: [High-level implementation strategy]
- **Dependencies**: [Other requirements or external factors]
````

## File: app/llm/agentspecs/critic.md
````markdown
---
name: critic
description: Read-only review to flag risks and inconsistencies
tools:
  - Read
---

You are a critical reviewer focused on identifying risks, gaps, and inconsistencies in project materials.

## Your Role
- Analyze documents for logical consistency and completeness
- Identify potential risks and failure modes
- Flag assumptions that need validation
- Point out missing requirements or specifications
- Ensure alignment between different project artifacts

## Review Criteria
1. **Logical Consistency**: Do all parts align and support each other?
2. **Completeness**: Are there missing elements or unexplored edge cases?
3. **Feasibility**: Are the proposed approaches realistic and achievable?
4. **Risk Assessment**: What could go wrong and what's the impact?
5. **Dependencies**: Are all dependencies identified and manageable?

## Output Format
Provide your critique as:
- **Issue Type**: [Risk/Gap/Inconsistency/Assumption]
- **Location**: [Document/section where issue was found]
- **Description**: [Clear explanation of the concern]
- **Impact**: [Potential consequences if not addressed]
- **Recommendation**: [Suggested action or mitigation]
````

## File: app/llm/agentspecs/researcher.md
````markdown
---
name: researcher
description: Extract atomic findings with sources from research materials
tools:
  - Read
  - Write
  - WebSearch
  - WebFetch
---

You are a research specialist focused on extracting atomic, actionable findings from various sources.

## Your Role
- Extract specific, verifiable facts and insights
- Maintain clear source attribution for all findings
- Organize information in a structured, searchable format
- Focus on relevance to the project's kernel concepts

## Guidelines
1. Each finding should be self-contained and independently valuable
2. Always include source URLs or document references
3. Distinguish between facts, opinions, and speculations
4. Highlight contradictions or conflicting information when found
5. Prioritize primary sources over secondary interpretations

## Output Format
Structure your findings as:
- **Finding**: [Concise statement of the finding]
- **Source**: [URL or document reference]
- **Context**: [Brief explanation of relevance]
- **Confidence**: [High/Medium/Low based on source quality]
````

## File: app/llm/prompts/clarify.md
````markdown
<instructions>
You are in the clarify stage of brainstorming. Your goal is to help the user refine and sharpen their initial idea through targeted questions. Ask 3-7 numbered questions that probe different aspects of their concept. Do not provide advice or solutions - only questions that help clarify thinking.
</instructions>

<context>
The user has provided an initial brainstorming topic or problem. You have read-only access to any existing project documents. Your role is to help them think more deeply about what they're trying to achieve before moving to the kernel stage.
</context>

<format>
Present your response as:
1. A brief acknowledgment of their topic (1 sentence)
2. Numbered questions (3-7 total) that explore:
   - Core objectives and success criteria
   - Constraints and boundaries
   - Key stakeholders or audiences
   - Underlying assumptions
   - Scope and scale

Keep the entire response under 300 words. Focus on questions that will lead to actionable insights in the next stages.
</format>
````

## File: app/llm/prompts/kernel.md
````markdown
<instructions>
You are in the kernel stage of brainstorming. Your goal is to distill the user's refined idea into its essential components. Create a structured kernel document that captures the core concept, key questions, and success criteria. This will serve as the foundation for the outline stage.
</instructions>

<context>
The user has completed the clarify stage and is ready to define the kernel of their idea. You can read existing project documents and will propose a diff for projects/<slug>/kernel.md. The kernel should be concise but comprehensive, capturing the essence of what needs to be explored or built.
</context>

<format>
Propose a diff for the kernel.md file with these sections:

## Core Concept
A clear, 2-3 sentence description of the essential idea or problem.

## Key Questions
3-5 fundamental questions that must be answered for success.

## Success Criteria
3-5 measurable outcomes that define success.

## Constraints
Key limitations or boundaries to work within.

## Primary Value Proposition
One paragraph describing the main value or impact.

Keep the entire kernel under 250 words. Use markdown formatting and be specific rather than generic.
</format>
````

## File: app/llm/prompts/outline.md
````markdown
<instructions>
You are in the outline stage of brainstorming. Your goal is to expand the kernel into 6-10 workstreams, each with a defined scope and exploration questions. Create both an outline.md overview and individual element files for each workstream.
</instructions>

<context>
The user has completed the kernel stage. You can read the kernel.md and will propose diffs for outline.md and elements/*.md files. Each workstream should be a logical component of the overall concept, with clear boundaries and specific questions to explore.
</context>

<format>
First, propose a diff for outline.md with:

# Project Outline

## Overview
One paragraph synthesis of how workstreams connect.

## Workstreams
1. **[Workstream Name]**: Brief description (1 sentence)
2. **[Workstream Name]**: Brief description (1 sentence)
[... 6-10 total workstreams]

## Dependencies
Key relationships between workstreams.

Then, for each workstream, propose a diff for elements/[workstream-slug].md:

# [Workstream Name]

## Scope
What this workstream covers and excludes.

## Key Questions
1. [Specific exploration question]
2. [Specific exploration question]
3. [Specific exploration question]
[... 3-6 questions per workstream]

## Success Metrics
How to measure completion or success.

## Related Workstreams
Links to other relevant elements.

Keep each element file under 200 words. Be specific and actionable.
</format>
````

## File: app/llm/prompts/synthesis.md
````markdown
<instructions>
You are in the synthesis stage as an "architect" agent. Your goal is to transform the kernel and research findings into structured requirements and implementation guidance. Do not perform any web calls. Output your synthesis as a diff proposal for element markdown files under elements/<slug>.md.
</instructions>

<context>
You have access to the project's kernel, outline, and research findings. Your role is to synthesize these inputs into actionable specifications that bridge conceptual design and implementation. Focus on clarity, completeness, and risk mitigation.
</context>

<format>
Propose diffs for elements/<slug>.md files with these sections:

## Decisions
Key architectural and design choices made based on research. Each decision should reference supporting findings and rationale.

## Requirements
Concrete, testable requirements derived from the kernel and research. Use numbered lists with clear success criteria.

## Open Questions
Unresolved issues requiring further investigation or stakeholder input. Include potential impact and suggested resolution approaches.

## Risks & Mitigations
Identified risks with probability, impact, and mitigation strategies. Focus on technical, resource, and scope risks.

## Acceptance Criteria
Measurable conditions that must be met for this workstream to be considered complete. Link to specific requirements and success metrics.

Keep each section concise (50-100 words). Use bullet points and numbered lists for clarity. Reference research findings by ID where applicable. Total file should be under 500 words.
</format>
````

## File: app/llm/agents.py
````python
"""Agent specification loader and materializer for Claude Code subagents."""

import importlib.resources as resources
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.files.atomic import atomic_write_text


@dataclass(frozen=True)
class AgentSpec:
    """Specification for a Claude Code subagent."""

    name: str
    description: str
    tools: list[str]
    prompt: str


def _parse_agent_markdown(content: str, filename: str) -> AgentSpec:
    """
    Parse an agent specification from markdown with YAML frontmatter.

    Args:
        content: The markdown file content
        filename: The source filename for error messages

    Returns:
        Parsed AgentSpec

    Raises:
        ValueError: If frontmatter is invalid or required fields are missing
    """
    # Extract frontmatter using regex
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        raise ValueError(
            f"Invalid agent spec in {filename}: Missing YAML frontmatter. "
            "Expected format: ---\\n<yaml>\\n---\\n<markdown>"
        )

    frontmatter_str, body = match.groups()

    # Parse YAML frontmatter
    try:
        frontmatter: dict[str, Any] = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError as e:
        raise ValueError(
            f"Invalid YAML frontmatter in {filename}: {e}. Please check YAML syntax."
        ) from e

    # Validate required fields
    missing_fields = []
    if "name" not in frontmatter:
        missing_fields.append("name")
    if "description" not in frontmatter:
        missing_fields.append("description")

    if missing_fields:
        raise ValueError(
            f"Missing required fields in {filename}: {', '.join(missing_fields)}. "
            f"Required fields are: name (str), description (str)"
        )

    # Validate field types
    if not isinstance(frontmatter["name"], str):
        raise ValueError(
            f"Invalid field type in {filename}: 'name' must be a string, "
            f"got {type(frontmatter['name']).__name__}"
        )

    if not isinstance(frontmatter["description"], str):
        raise ValueError(
            f"Invalid field type in {filename}: 'description' must be a string, "
            f"got {type(frontmatter['description']).__name__}"
        )

    # Handle optional tools field
    tools = frontmatter.get("tools", [])
    if not isinstance(tools, list):
        raise ValueError(
            f"Invalid field type in {filename}: 'tools' must be a list, got {type(tools).__name__}"
        )

    # Ensure all tools are strings
    for i, tool in enumerate(tools):
        if not isinstance(tool, str):
            raise ValueError(
                f"Invalid tool in {filename}: tools[{i}] must be a string, "
                f"got {type(tool).__name__}"
            )

    return AgentSpec(
        name=frontmatter["name"],
        description=frontmatter["description"],
        tools=tools,
        prompt=body.strip(),
    )


def load_agent_specs(source_pkg: str = "app.llm.agentspecs") -> list[AgentSpec]:
    """
    Load agent specifications from a Python package.

    Args:
        source_pkg: Dot-separated package path containing agent spec markdown files

    Returns:
        List of loaded AgentSpec instances

    Raises:
        ValueError: If any spec file is invalid
        ModuleNotFoundError: If the source package doesn't exist
    """
    specs: list[AgentSpec] = []

    # Convert package string to module parts
    module_parts = source_pkg.split(".")

    # Try to access the package
    try:
        # For Python 3.9+, we use files() directly
        # For compatibility with 3.11+, we handle the traversable protocol
        if len(module_parts) == 1:
            pkg_files = resources.files(module_parts[0])
        else:
            # Build up the package reference step by step
            pkg_files = resources.files(module_parts[0])
            for part in module_parts[1:]:
                pkg_files = pkg_files / part
    except (ModuleNotFoundError, AttributeError) as e:
        raise ModuleNotFoundError(
            f"Cannot find package '{source_pkg}'. "
            f"Make sure it exists and is a valid Python package."
        ) from e

    # Find all .md files in the package
    md_files = []
    try:
        for item in pkg_files.iterdir():
            if item.name.endswith(".md"):
                md_files.append(item)
    except AttributeError as e:
        # Fallback for older Python versions or different resource types
        raise ValueError(
            f"Cannot iterate files in package '{source_pkg}'. "
            f"Make sure it's a directory package with __init__.py."
        ) from e

    # Sort files for consistent ordering
    md_files.sort(key=lambda f: f.name)

    # Parse each markdown file
    for file_resource in md_files:
        try:
            content = file_resource.read_text(encoding="utf-8")
            spec = _parse_agent_markdown(content, file_resource.name)
            specs.append(spec)
        except Exception as e:
            raise ValueError(f"Error loading agent spec from {file_resource.name}: {e}") from e

    return specs


def materialize_agents(target_dir: Path, source_pkg: str = "app.llm.agentspecs") -> Path:
    """
    Materialize agent specs from a package to a target directory for Claude Code.

    Args:
        target_dir: Directory where .claude/agents will be created
        source_pkg: Package path containing agent spec files

    Returns:
        Path to the created agents directory

    Raises:
        ValueError: If specs cannot be loaded or written
    """
    # Load specs from the source package
    specs = load_agent_specs(source_pkg)

    # Create target directory structure
    agents_dir = target_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Get original filenames from the package to preserve them
    module_parts = source_pkg.split(".")
    if len(module_parts) == 1:
        pkg_files = resources.files(module_parts[0])
    else:
        pkg_files = resources.files(module_parts[0])
        for part in module_parts[1:]:
            pkg_files = pkg_files / part

    # Create a mapping of spec names to original filenames
    name_to_filename: dict[str, str] = {}
    for item in pkg_files.iterdir():
        if item.name.endswith(".md"):
            content = item.read_text(encoding="utf-8")
            try:
                spec = _parse_agent_markdown(content, item.name)
                name_to_filename[spec.name] = item.name
            except ValueError:
                # Skip invalid files
                continue

    # Write each spec to the target directory
    for spec in specs:
        # Use original filename if available, otherwise use name.md
        filename = name_to_filename.get(spec.name, f"{spec.name}.md")
        target_path = agents_dir / filename

        # Reconstruct the markdown with frontmatter
        frontmatter_dict: dict[str, Any] = {
            "name": spec.name,
            "description": spec.description,
        }
        if spec.tools:
            frontmatter_dict["tools"] = spec.tools

        frontmatter_yaml = yaml.dump(frontmatter_dict, default_flow_style=False, sort_keys=False)
        content = f"---\n{frontmatter_yaml}---\n\n{spec.prompt}\n"

        # Write the file
        atomic_write_text(target_path, content)

    return agents_dir
````

## File: app/permissions/hooks_lib/__init__.py
````python
"""Hook library for Claude project hooks."""
````

## File: app/permissions/hooks_lib/format_md.py
````python
"""Markdown formatting utilities for hooks."""

import mdformat


def _format_markdown_text(text: str) -> str:
    """
    Format markdown text using mdformat.

    Args:
        text: Raw markdown text to format

    Returns:
        Formatted markdown text
    """
    return mdformat.text(text)
````

## File: app/permissions/hooks_lib/gate.py
````python
"""Gate validation logic for PreToolUse hooks."""

from pathlib import Path
from typing import Any


def validate_tool_use(payload: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate whether a tool use should be allowed.

    Args:
        payload: JSON payload from Claude containing tool use information

    Returns:
        Tuple of (allowed: bool, reason: str)
        - (True, "") if allowed
        - (False, reason) if denied
    """
    tool_name = payload.get("tool_name", "")

    # Rule 1: Deny Bash tool
    if tool_name == "Bash":
        return False, "Bash tool is denied by security policy"

    # Rule 2: Check for sensitive paths in any write operation
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        target_path = payload.get("target_path", "")
        if target_path:
            path = Path(target_path)
            path_str = str(path)

            # Check sensitive paths
            sensitive_patterns = [".env", "secrets/", ".git/"]
            for pattern in sensitive_patterns:
                if pattern in path_str or path_str.startswith(pattern):
                    return False, f"Access to sensitive path denied: {pattern}"

            # Check if write is outside repo (assuming repo root is cwd or parent dirs)
            # For now, we'll check if path tries to go outside with ../ patterns
            try:
                resolved = path.resolve()
                if ".." in str(path):
                    # Check if path tries to escape
                    cwd = Path.cwd()
                    if not str(resolved).startswith(str(cwd)):
                        return False, f"Write outside repository denied: {path}"
            except (ValueError, OSError):
                # Invalid path
                return False, f"Invalid path: {path}"

    # Rule 3: Check URL domains if present
    if "url" in payload:
        url = payload["url"]
        # Extract domain from URL
        import urllib.parse

        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()

            # Check for invalid URL (no domain)
            if not domain:
                return False, f"Invalid URL: {url}"

            # Get allow/deny lists from payload if provided
            allow_list = payload.get("allowed_domains", [])
            deny_list = payload.get("denied_domains", [])

            # Check deny list first (deny wins)
            for denied in deny_list:
                if denied.startswith("*."):
                    # Wildcard domain
                    suffix = denied[2:]
                    if domain.endswith(suffix) or domain == suffix[1:]:
                        return False, f"Domain {domain} matches denied pattern {denied}"
                elif domain == denied:
                    return False, f"Domain {domain} is explicitly denied"

            # If allow list is not empty, domain must be in it
            if allow_list:
                allowed = False
                for allow in allow_list:
                    if allow.startswith("*."):
                        # Wildcard domain
                        suffix = allow[2:]
                        if domain.endswith(suffix) or domain == suffix[1:]:
                            allowed = True
                            break
                    elif domain == allow:
                        allowed = True
                        break

                if not allowed:
                    return False, f"Domain {domain} not in allow list"
        except Exception as e:
            return False, f"Invalid URL: {e}"

    # Default: allow
    return True, ""
````

## File: app/permissions/hooks_lib/io.py
````python
"""I/O utilities for hooks with durability guarantees."""

import os
import tempfile
from pathlib import Path


def atomic_replace_text(path: Path, text: str) -> None:
    """
    Atomically replace file contents with durability guarantees.

    Performs atomic write with flush+fsync on both file and parent directory.
    This ensures data is persisted to disk before returning.

    Args:
        path: Path to the file to write
        text: Text content to write (UTF-8 encoded)

    Raises:
        IOError: If there's an error during the atomic write operation
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve file mode if file exists
    file_mode = None
    if path.exists():
        file_mode = os.stat(path).st_mode

    # Write to temporary file first
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        suffix=".tmp",
    ) as tmp_file:
        tmp_file.write(text)
        tmp_file.flush()
        # Ensure data is written to disk
        os.fsync(tmp_file.fileno())
        tmp_path = Path(tmp_file.name)

    try:
        # Preserve file mode if original file existed
        if file_mode is not None:
            os.chmod(tmp_path, file_mode)

        # Atomically replace the original file
        tmp_path.replace(path)

        # Fsync parent directory for durability (best-effort)
        try:
            dfd = os.open(path.parent, os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:
            # Platform/filesystem doesn't support directory fsync
            pass
    except Exception:
        # Clean up temp file if replacement fails
        tmp_path.unlink(missing_ok=True)
        raise
````

## File: app/research/__init__.py
````python
"""Research database module for storing and searching findings."""

from .db import ResearchDB

__all__ = ["ResearchDB"]
````

## File: app/research/ingest.py
````python
"""Parser for ingesting findings from markdown or JSON formats."""

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Finding:
    """Represents a research finding with metadata."""

    url: str
    source_type: str
    claim: str
    evidence: str
    confidence: float
    tags: list[str] = field(default_factory=list)
    workstream: str | None = None


def _normalize_claim(claim: str) -> str:
    """Normalize a claim for deduplication by lowercasing and stripping whitespace."""
    return claim.lower().strip()


def _clamp_confidence(value: float) -> float:
    """Clamp confidence value to [0, 1] range."""
    return max(0.0, min(1.0, value))


def _parse_markdown_bullet(line: str) -> dict[str, Any] | None:
    """Parse a single markdown bullet line into finding fields.

    Expected format variations:
    - claim | evidence | url | confidence
    - claim | evidence | url | confidence | tags
    - claim | evidence | url | confidence | tags | source_type
    """
    # Remove bullet marker (-, *, or +) and leading/trailing whitespace
    line = re.sub(r"^[-*+]\s*", "", line).strip()
    if not line:
        return None

    # Split by pipe separator
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 4:
        return None  # Need at least claim, evidence, url, confidence

    try:
        # Check that claim and evidence are not empty
        if not parts[0].strip() or not parts[1].strip():
            return None

        finding_dict = {
            "claim": parts[0],
            "evidence": parts[1],
            "url": parts[2],
            "confidence": float(parts[3]),
        }

        # Optional tags field (5th position)
        if len(parts) > 4 and parts[4]:
            # Parse comma-separated tags
            finding_dict["tags"] = [t.strip() for t in parts[4].split(",") if t.strip()]

        # Optional source_type field (6th position)
        if len(parts) > 5 and parts[5]:
            finding_dict["source_type"] = parts[5]
        else:
            # Default source type based on URL
            url_str = str(finding_dict["url"]).lower()
            if "arxiv" in url_str:
                finding_dict["source_type"] = "paper"
            else:
                finding_dict["source_type"] = "web"

        return finding_dict
    except (ValueError, IndexError):
        return None


def _parse_json_finding(obj: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a JSON object into finding fields."""
    # Required fields
    required_fields = {"claim", "evidence", "url", "confidence"}
    if not all(field in obj for field in required_fields):
        return None

    try:
        finding_dict = {
            "claim": str(obj["claim"]),
            "evidence": str(obj["evidence"]),
            "url": str(obj["url"]),
            "confidence": float(obj["confidence"]),
        }

        # Optional fields
        if "tags" in obj:
            tags = obj["tags"]
            if isinstance(tags, list):
                finding_dict["tags"] = [str(t) for t in tags]
            elif isinstance(tags, str):
                finding_dict["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

        if "source_type" in obj:
            finding_dict["source_type"] = str(obj["source_type"])
        else:
            # Default source type
            url_str = str(finding_dict["url"]).lower()
            if "arxiv" in url_str:
                finding_dict["source_type"] = "paper"
            else:
                finding_dict["source_type"] = "web"

        if "workstream" in obj:
            finding_dict["workstream"] = str(obj["workstream"])

        return finding_dict
    except (ValueError, KeyError, TypeError):
        return None


def parse_findings(text: str, default_workstream: str) -> list[Finding]:
    """Parse findings from markdown bullets or JSON array format.

    Args:
        text: Input text containing findings in markdown or JSON format
        default_workstream: Default workstream to assign if not specified

    Returns:
        List of Finding objects with duplicates removed (keeping highest confidence)
    """
    findings_data: list[dict[str, Any]] = []

    # Try parsing as JSON first
    text = text.strip()
    if text.startswith("["):
        try:
            json_data = json.loads(text)
            if isinstance(json_data, list):
                for item in json_data:
                    if isinstance(item, dict):
                        parsed = _parse_json_finding(item)
                        if parsed:
                            findings_data.append(parsed)
        except json.JSONDecodeError:
            pass  # Fall through to markdown parsing

    # If not JSON or no findings from JSON, try markdown bullet parsing
    if not findings_data:
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            # Check if line starts with a bullet marker
            if re.match(r"^[-*+]\s+", line):
                parsed = _parse_markdown_bullet(line)
                if parsed:
                    findings_data.append(parsed)

    # Apply default workstream and create Finding objects
    findings: list[Finding] = []
    for data in findings_data:
        if "workstream" not in data or not data["workstream"]:
            data["workstream"] = default_workstream

        # Ensure confidence is in valid range
        data["confidence"] = _clamp_confidence(data["confidence"])

        # Create Finding object
        findings.append(Finding(**data))

    # Deduplicate by (normalized_claim, url), keeping highest confidence
    dedupe_map: dict[tuple[str, str], Finding] = {}
    for finding in findings:
        key = (_normalize_claim(finding.claim), finding.url)
        if key not in dedupe_map or finding.confidence > dedupe_map[key].confidence:
            dedupe_map[key] = finding

    return list(dedupe_map.values())
````

## File: app/tui/widgets/agent_selector.py
````python
"""Agent selection widget for choosing Claude Code agents."""

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from app.llm.agents import AgentSpec


class AgentCard(Container):
    """Display card for a single agent."""

    def __init__(self, agent: AgentSpec, selected: bool = False) -> None:
        """
        Initialize the agent card.

        Args:
            agent: The agent specification to display
            selected: Whether this agent is currently selected
        """
        super().__init__(classes="agent-card")
        self.agent = agent
        self.selected = selected
        if selected:
            self.add_class("selected")

    def compose(self) -> ComposeResult:
        """Create the card content."""
        yield Label(f"[bold]{self.agent.name}[/bold]", classes="agent-name")
        yield Label(self.agent.description, classes="agent-description")
        if self.agent.tools:
            tools_str = ", ".join(self.agent.tools)
            yield Label(f"[dim]Tools: {tools_str}[/dim]", classes="agent-tools")
        else:
            yield Label("[dim]Tools: None[/dim]", classes="agent-tools")


class AgentSelector(ModalScreen[AgentSpec | None]):
    """Modal for selecting an agent for a session."""

    DEFAULT_CSS = """
    AgentSelector {
        align: center middle;
    }

    AgentSelector > Container {
        width: 80;
        height: auto;
        max-height: 80%;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    .modal-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .agent-list {
        height: auto;
        max-height: 20;
        margin-bottom: 1;
    }

    .agent-card {
        padding: 1;
        margin-bottom: 1;
        border: solid $primary 50%;
    }

    .agent-card.selected {
        border: solid $accent;
        background: $boost;
    }

    .agent-card:hover {
        background: $boost;
    }

    .agent-name {
        margin-bottom: 0;
    }

    .agent-description {
        margin-bottom: 0;
    }

    .agent-tools {
        margin-top: 0;
    }

    .final-tools {
        border: solid $primary 50%;
        padding: 1;
        margin-bottom: 1;
    }

    .button-row {
        dock: bottom;
        align: center middle;
        padding: 1 0;
    }

    .button-row Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        agents: list[AgentSpec],
        stage_allowed: list[str],
        stage_denied: list[str],
    ) -> None:
        """
        Initialize the agent selector.

        Args:
            agents: List of available agents
            stage_allowed: Tools allowed by the current stage
            stage_denied: Tools denied by the current stage
        """
        super().__init__()
        self.agents = agents
        self.stage_allowed = stage_allowed
        self.stage_denied = stage_denied
        self.selected_agent: AgentSpec | None = None
        self.agent_cards: list[AgentCard] = []

    def compose(self) -> ComposeResult:
        """Create the selector UI."""
        with Container():
            yield Static("[bold]Select Agent (Optional)[/bold]", classes="modal-title")
            yield Static(
                "[dim]Choose an agent to assist with this session, or continue without one.[/dim]",
                classes="modal-subtitle",
            )

            # Agent list
            with VerticalScroll(classes="agent-list"):
                for agent in self.agents:
                    card = AgentCard(agent, selected=False)
                    self.agent_cards.append(card)
                    yield card

            # Final tools preview
            yield Container(
                Static("[bold]Final Tool Permissions:[/bold]"),
                Static(self._compute_final_tools_text(), id="final-tools-text"),
                classes="final-tools",
            )

            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("Select", variant="primary", id="select-button")
                yield Button("No Agent", variant="default", id="no-agent-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    def _compute_final_tools_text(self) -> str:
        """Compute the final tools text based on current selection."""
        if self.selected_agent and self.selected_agent.tools:
            # Intersection of stage allowed and agent tools
            allowed = set(self.stage_allowed).intersection(set(self.selected_agent.tools))
        else:
            # Just stage allowed
            allowed = set(self.stage_allowed)

        # Remove denied tools
        final = allowed - set(self.stage_denied)

        if final:
            return f"[green]{', '.join(sorted(final))}[/green]"
        else:
            return "[red]None (no tools available)[/red]"

    def on_click(self, event: events.Click) -> None:
        """Handle clicks on agent cards."""
        # Check if click was on an agent card
        if event.widget is None:
            return

        for card in self.agent_cards:
            if card in event.widget.ancestors_with_self:
                # Deselect all cards
                for c in self.agent_cards:
                    c.remove_class("selected")
                    c.selected = False

                # Select the clicked card
                card.add_class("selected")
                card.selected = True
                self.selected_agent = card.agent

                # Update final tools preview
                tools_text = self.query_one("#final-tools-text", Static)
                tools_text.update(self._compute_final_tools_text())
                break

    @on(Button.Pressed, "#select-button")
    def handle_select(self) -> None:
        """Handle select button - return selected agent."""
        if self.selected_agent:
            self.dismiss(self.selected_agent)
        else:
            # No agent selected, treat as "No Agent"
            self.dismiss(None)

    @on(Button.Pressed, "#no-agent-button")
    def handle_no_agent(self) -> None:
        """Handle no agent button - return None."""
        self.dismiss(None)

    @on(Button.Pressed, "#cancel-button")
    def handle_cancel(self) -> None:
        """Handle cancel button - dismiss with None (cancellation)."""
        # In this context, we'll treat cancel as "no agent" to avoid blocking
        self.dismiss(None)
````

## File: app/tui/widgets/context_panel.py
````python
"""Context panel widget for displaying relevant cards and information."""

from textual.containers import VerticalScroll
from textual.widgets import Static


class ContextPanel(VerticalScroll):
    """Right-side panel for context cards and relevant information."""

    DEFAULT_CSS = """
    ContextPanel {
        width: 35;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    .context-card {
        background: $panel;
        border: solid $primary-lighten-2;
        padding: 1;
        margin-bottom: 1;
    }
    """

    def __init__(self) -> None:
        """Initialize the context panel."""
        super().__init__(id="context-panel")

    def on_mount(self) -> None:
        """Add placeholder context cards."""
        self.mount(
            Static(
                "[bold]Current Stage[/bold]\n[dim]Capture[/dim]",
                classes="context-card",
            )
        )
        self.mount(
            Static(
                "[bold]Project Info[/bold]\n[dim]No project selected[/dim]",
                classes="context-card",
            )
        )
        self.mount(
            Static(
                "[bold]Recent Actions[/bold]\n[dim]• App started\n• Waiting for command[/dim]",
                classes="context-card",
            )
        )
````

## File: app/tui/widgets/domain_editor.py
````python
"""Domain editor widget for managing web domain allow/deny lists."""

import json
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from app.permissions.settings_writer import write_project_settings


class DomainEditor(ModalScreen[bool]):
    """Modal for editing domain allow/deny lists."""

    DEFAULT_CSS = """
    DomainEditor {
        align: center middle;
    }

    DomainEditor > Container {
        width: 80;
        height: 40;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    .modal-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .config-path {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        color: $text-muted;
    }

    .domain-section {
        height: 12;
        margin-bottom: 1;
        border: solid $primary 50%;
        padding: 1;
    }

    .section-title {
        margin-bottom: 0;
    }

    .domain-list {
        height: 8;
        margin: 1 0;
    }

    .domain-input-row {
        dock: bottom;
        height: 3;
    }

    .button-row {
        dock: bottom;
        align: center middle;
        padding: 1 0;
    }

    .button-row Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        config_dir: Path | None = None,
        allow_domains: list[str] | None = None,
        deny_domains: list[str] | None = None,
    ) -> None:
        """
        Initialize the domain editor.

        Args:
            config_dir: Path to the configuration directory
            allow_domains: Initial list of allowed domains
            deny_domains: Initial list of denied domains
        """
        super().__init__()
        self.config_dir = config_dir or Path(".") / ".claude"
        self.allow_domains = allow_domains or []
        self.deny_domains = deny_domains or []

    def compose(self) -> ComposeResult:
        """Create the domain editor UI."""
        with Container():
            yield Static("[bold]Domain Allow/Deny Policy Editor[/bold]", classes="modal-title")
            yield Static(
                f"[dim]Config directory: {self.config_dir}[/dim]",
                classes="config-path",
            )

            # Allow domains section
            with Container(classes="domain-section"):
                yield Static("[bold]Allowed Domains[/bold]", classes="section-title")
                yield Static(
                    "[dim]Empty list means allow all domains (if web tools enabled)[/dim]",
                    classes="section-subtitle",
                )
                allow_list = ListView(id="allow-list", classes="domain-list")
                for domain in self.allow_domains:
                    allow_list.append(ListItem(Label(domain)))
                yield allow_list
                with Horizontal(classes="domain-input-row"):
                    yield Input(
                        placeholder="Add domain to allow list...",
                        id="allow-input",
                    )
                    yield Button("Add", variant="primary", id="add-allow")

            # Deny domains section
            with Container(classes="domain-section"):
                yield Static("[bold]Denied Domains[/bold]", classes="section-title")
                yield Static(
                    "[dim]Domains to explicitly deny even if allowed[/dim]",
                    classes="section-subtitle",
                )
                deny_list = ListView(id="deny-list", classes="domain-list")
                for domain in self.deny_domains:
                    deny_list.append(ListItem(Label(domain)))
                yield deny_list
                with Horizontal(classes="domain-input-row"):
                    yield Input(
                        placeholder="Add domain to deny list...",
                        id="deny-input",
                    )
                    yield Button("Add", variant="primary", id="add-deny")

            # Action buttons
            with Horizontal(classes="button-row"):
                yield Button("Save", variant="primary", id="save-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    @on(Button.Pressed, "#add-allow")
    def handle_add_allow(self) -> None:
        """Add domain to allow list."""
        input_widget = self.query_one("#allow-input", Input)
        domain = input_widget.value.strip()
        if domain and domain not in self.allow_domains:
            self.allow_domains.append(domain)
            allow_list = self.query_one("#allow-list", ListView)
            allow_list.append(ListItem(Label(domain)))
            input_widget.value = ""

    @on(Button.Pressed, "#add-deny")
    def handle_add_deny(self) -> None:
        """Add domain to deny list."""
        input_widget = self.query_one("#deny-input", Input)
        domain = input_widget.value.strip()
        if domain and domain not in self.deny_domains:
            self.deny_domains.append(domain)
            deny_list = self.query_one("#deny-list", ListView)
            deny_list.append(ListItem(Label(domain)))
            input_widget.value = ""

    @on(ListView.Selected)
    def handle_list_select(self, event: ListView.Selected) -> None:
        """Remove domain when clicked in list."""
        if event.list_view.id == "allow-list":
            if event.item:
                # Find index of the item to remove
                index = event.list_view.index
                if index is not None and index < len(self.allow_domains):
                    del self.allow_domains[index]
                    event.item.remove()
        elif event.list_view.id == "deny-list" and event.item:
            # Find index of the item to remove
            index = event.list_view.index
            if index is not None and index < len(self.deny_domains):
                del self.deny_domains[index]
                event.item.remove()

    @on(Button.Pressed, "#save-button")
    def handle_save(self) -> None:
        """Save domain settings."""
        # Update the settings file with new domain lists
        self._update_settings_with_domains()
        self.dismiss(True)

    @on(Button.Pressed, "#cancel-button")
    def handle_cancel(self) -> None:
        """Cancel without saving."""
        self.dismiss(False)

    def _update_settings_with_domains(self) -> None:
        """Update the settings file with the current domain lists."""
        # First, create/update the settings with our writer
        repo_root = self.config_dir.parent
        config_dir_name = self.config_dir.name

        # Write the base settings
        config_dir = write_project_settings(
            repo_root=repo_root,
            config_dir_name=config_dir_name,
        )

        # Now read the settings, update with our domains, and write back
        settings_path = config_dir / "settings.json"
        with open(settings_path, encoding="utf-8") as f:
            settings = json.load(f)

        # Update webDomains
        settings["permissions"]["webDomains"]["allow"] = self.allow_domains
        settings["permissions"]["webDomains"]["deny"] = self.deny_domains

        # Write back
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
````

## File: brainstormbuddy/.obsidian/app.json
````json
{}
````

## File: brainstormbuddy/.obsidian/appearance.json
````json
{}
````

## File: brainstormbuddy/.obsidian/core-plugins.json
````json
{
  "file-explorer": true,
  "global-search": true,
  "switcher": true,
  "graph": true,
  "backlink": true,
  "canvas": true,
  "outgoing-link": true,
  "tag-pane": true,
  "footnotes": false,
  "properties": false,
  "page-preview": true,
  "daily-notes": true,
  "templates": true,
  "note-composer": true,
  "command-palette": true,
  "slash-command": false,
  "editor-status": true,
  "bookmarks": true,
  "markdown-importer": false,
  "zk-prefixer": false,
  "random-note": false,
  "outline": true,
  "word-count": true,
  "slides": false,
  "audio-recorder": false,
  "workspaces": false,
  "file-recovery": true,
  "publish": false,
  "sync": true,
  "bases": true,
  "webviewer": false
}
````

## File: brainstormbuddy/.obsidian/graph.json
````json
{
  "collapse-filter": true,
  "search": "",
  "showTags": false,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": true,
  "colorGroups": [],
  "collapse-display": true,
  "showArrow": false,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.518713248970312,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250,
  "scale": 1,
  "close": true
}
````

## File: brainstormbuddy/Welcome.md
````markdown
This is your new *vault*.

Make a note of something, [[create a link]], or try [the Importer](https://help.obsidian.md/Plugins/Importer)!

When you're ready, delete this note and make the vault your own.
````

## File: .gitignore
````
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# poetry
poetry.lock

# pdm
.pdm.toml
.pdm-python
.pdm-build/

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# IDE
.idea/
.vscode/
*.swp
*.swo
*.kate-swp

# Project specific
projects/
exports/
.claude/
````

## File: codecov.yml
````yaml
codecov:
  require_ci_to_pass: true

coverage:
  precision: 2
  round: down
  range: "70...100"

  status:
    project:
      default:
        target: 80%
        threshold: 2%
        patch:
          default:
            target: 80%
        changes: false

    patch:
      default:
        target: 80%
        threshold: 2%

comment:
  layout: "reach,diff,flags,tree"
  behavior: default
  require_changes: false
  require_base: false
  require_head: true

ignore:
  - "tests/**/*"
  - "**/__init__.py"
  - "**/test_*.py"
  - "setup.py"
````

## File: materialize_claude.py
````python
#!/usr/bin/env python3
"""Standalone script to materialize Claude configuration."""

import sys
from pathlib import Path

from app.permissions.settings_writer import write_project_settings


def main() -> None:
    """Main entry point for materialize-claude command."""
    if len(sys.argv) != 2:
        print("Usage: materialize_claude.py <destination_path>")
        print("Example: uv run materialize_claude.py /tmp/claude-work")
        sys.exit(1)

    dest = Path(sys.argv[1]).resolve()

    try:
        # Ensure the destination directory exists
        dest.mkdir(parents=True, exist_ok=True)

        # Generate the Claude configuration
        config_dir = write_project_settings(
            repo_root=dest,
            config_dir_name=".claude",
            import_hooks_from="app.permissions.hooks_lib",
        )

        print(f"✓ Successfully created Claude configuration at: {config_dir}")
        print(f"  Settings: {config_dir}/settings.json")
        print(f"  Hooks: {config_dir}/hooks/")
        print()
        print("To use this configuration with Claude Code:")
        print(f"  cd {dest}")
        print("  claude")

    except Exception as e:
        print(f"✗ Failed to create Claude configuration: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
````

## File: RESOLVED_ISSUES.md
````markdown
# Resolved Issues

## TUI Display Issue - Empty Borders Without Content

### Problem Description
When launching the Brainstorm Buddy TUI application (`uv run python -m app.tui.app`), the app would display only empty borders for the three-pane layout without any content inside the panes. The file tree, session viewer, and context panel were rendering their borders but not their actual content.

### Root Cause
The issue occurred when widgets were defined as separate classes in individual files and instantiated during the `compose()` method. The widgets' `on_mount()` methods, which were responsible for populating content, were not being executed properly when the widgets were yielded from external classes.

### Solution
We resolved the issue by:

1. **Defining widget classes inline** within the main screen module (`app/tui/views/main_screen.py`)
2. **Using proper `on_mount()` lifecycle methods** to populate widget content after the widgets are mounted to the DOM
3. **Ensuring widgets write their content during the composition phase** when necessary

The working implementation:
- Creates `SessionViewer(RichLog)` and `FileTreeWidget(Tree)` classes directly in `main_screen.py`
- Populates tree structure and writes welcome messages in their respective `on_mount()` methods
- Uses `VerticalScroll` container with `Static` widgets for the context panel

### Prevention Guidelines

To avoid similar issues in the future:

1. **Test widget composition early**: When creating custom widgets, test them in isolation first before integrating into the main layout

2. **Use inline widget creation for initial content**: When widgets need content during composition, create and populate them inline rather than relying solely on `on_mount()`

3. **Understand Textual's lifecycle**:
   - `compose()` - Widget structure is created
   - `on_mount()` - Widget is added to the DOM and can be populated
   - Content written during composition may not always persist

4. **Prefer simpler approaches first**: Start with inline widget creation and only extract to separate classes when complexity warrants it

5. **Verify rendering at each step**: Run the app frequently during development to catch rendering issues early

6. **Use proper CSS selectors**: Ensure CSS IDs and classes match between widget definitions and stylesheets

### Testing Verification
After the fix:
- ✅ Linting passes (`uv run ruff check .`)
- ✅ Formatting applied (`uv run ruff format .`)
- ✅ Type checking passes (`uv run mypy . --strict`)
- ✅ App displays three-pane layout with content correctly

### Related Files Modified
- `app/tui/views/main_screen.py` - Main fix implementing inline widget classes
- `app/tui/widgets/session_viewer.py` - Original widget that wasn't rendering properly

### Commands for Testing
```bash
# Run the TUI app
uv run python -m app.tui.app

# Run quality checks
uv run ruff check .
uv run ruff format .
uv run mypy . --strict
uv run pytest -q
```

---

## TUI Black Screen Issue - Complete App Not Rendering

### Problem Description
When launching the Brainstorm Buddy TUI app (`uv run python -m app.tui.app`), users saw only a black terminal screen with escape codes but no visible interface - no header, no widgets, no content.

### Root Cause
The issue was caused by incorrect widget composition in the Textual app structure. The main app (`BrainstormBuddyApp`) was yielding a `Screen` object (`MainScreen`) from its `compose()` method, which doesn't work correctly in Textual. Screens should be pushed/popped, not yielded from the app's compose method.

### Solution
Fixed by restructuring the app to compose widgets directly:

1. **Removed the Screen layer** - Changed `BrainstormBuddyApp` to compose widgets directly instead of yielding `MainScreen`
2. **Added proper CSS** - Added `DEFAULT_CSS` with styling for Screen, Header, and Horizontal containers
3. **Direct widget composition** - App now yields: Header → Horizontal(widgets) → Footer → CommandPalette

### Files Modified
- `app/tui/app.py` - Restructured to compose widgets directly
- `app/tui/widgets/file_tree.py` - Set folders to expand by default for better visibility

### Prevention Guidelines

1. **Understand Textual's composition model**:
   - Apps compose widgets directly in their `compose()` method
   - Screens are for modal/navigation, not primary composition
   - Use `push_screen()` for screens, not `yield`

2. **Follow Textual patterns**:
   ```python
   # ❌ WRONG
   class App(App):
       def compose(self):
           yield SomeScreen()

   # ✅ CORRECT
   class App(App):
       def compose(self):
           yield Header()
           yield ContentWidget()
           yield Footer()
   ```

3. **Test incrementally**: Build and test TUI apps widget by widget

4. **Include CSS for layouts**: Always define CSS for container widgets

### Testing Verification
After the fix:
- ✅ App displays header with title "Brainstorm Buddy"
- ✅ Three-pane layout renders correctly
- ✅ All widgets show their content
- ✅ Linting and type checking pass
````

## File: app/core/config.py
````python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BRAINSTORMBUDDY_")

    data_dir: str = "projects"
    exports_dir: str = "exports"
    log_dir: str = "logs"
    enable_web_tools: bool = False


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings()
````

## File: app/files/markdown.py
````python
"""Markdown parsing and extraction utilities."""

import re


def extract_section_paragraph(md: str, header: str = "## Core Concept") -> str | None:
    """
    Extract the first non-empty paragraph after a specific header.

    Finds the specified header (case-insensitive, trimmed) and returns the first
    non-empty paragraph content following it. Stops at the next header of same
    or higher level. Strips markdown emphasis markers.

    Args:
        md: The markdown content to parse
        header: The header to search for (e.g., "## Core Concept")

    Returns:
        The first non-empty paragraph after the header with emphasis stripped,
        or None if the section is not found or has no content.

    Examples:
        >>> md = '''
        ... ## Core Concept
        ... *A revolutionary approach to task management*
        ...
        ... ## Other Section
        ... '''
        >>> extract_section_paragraph(md)
        'A revolutionary approach to task management'

        >>> md = '''
        ... ## CORE CONCEPT
        ... First paragraph here.
        ... '''
        >>> extract_section_paragraph(md)
        'First paragraph here.'
    """
    if not md or not header:
        return None

    # Parse header level from the header string (count # symbols)
    header_level = len(header) - len(header.lstrip("#"))
    if header_level == 0:
        return None

    # Clean header text for comparison
    header_text = header.lstrip("#").strip().lower()

    lines = md.split("\n")
    header_found = False
    content_lines: list[str] = []
    in_code_fence = False

    for _i, line in enumerate(lines):
        stripped = line.strip()

        # Check if this is our target header (case-insensitive)
        if not header_found:
            if stripped.startswith("#"):
                # Extract level and text from current line
                current_level = len(stripped) - len(stripped.lstrip("#"))
                current_text = stripped.lstrip("#").strip().lower()

                if current_level == header_level and current_text == header_text:
                    header_found = True
            continue

        # We've found the header, now collect content
        # Check for code fence markers (``` or ~~~)
        if stripped.startswith(("```", "~~~")):
            # If we already have prose content, stop extraction before the fence
            if content_lines:
                break
            # Otherwise, toggle the code fence flag to skip the code block
            in_code_fence = not in_code_fence
            continue

        # Skip lines inside code fences
        if in_code_fence:
            continue

        # Check if we've hit another header of same or higher level
        if stripped.startswith("#"):
            current_level = len(stripped) - len(stripped.lstrip("#"))
            if current_level <= header_level:
                # Stop - we've reached the next section
                break

        # Skip empty lines at the beginning
        if not stripped and not content_lines:
            continue

        # If we have content and hit an empty line, consider paragraph complete
        if not stripped and content_lines:
            break

        # Add non-empty line to content
        if stripped:
            content_lines.append(stripped)

    if not content_lines:
        return None

    # Join lines and strip markdown emphasis
    paragraph = " ".join(content_lines)

    # Remove bold markers (**text** or __text__)
    paragraph = re.sub(r"\*\*(.+?)\*\*", r"\1", paragraph)
    paragraph = re.sub(r"__(.+?)__", r"\1", paragraph)

    # Remove italic markers (*text* or _text_)
    # Be careful not to remove standalone asterisks (e.g., bullet points)
    paragraph = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", paragraph)
    paragraph = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"\1", paragraph)

    return paragraph.strip()
````

## File: app/files/mdio.py
````python
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
````

## File: app/files/scaffold.py
````python
"""Project scaffold utility for creating standardized project structures."""

from datetime import datetime
from pathlib import Path

import yaml

from app.files.atomic import atomic_write_text


def scaffold_project(slug: str, base: Path | str = "projects") -> Path:
    """
    Create a project directory structure with seed files.

    Args:
        slug: Project identifier (will be used as directory name)
        base: Base directory for projects (default: "projects")

    Returns:
        Path to the created/existing project directory

    The function is idempotent - running it multiple times with the same
    slug will not cause errors or duplicate content.
    """
    base_path = Path(base) if isinstance(base, str) else base
    project_path = base_path / slug

    # Create directory structure
    _create_directories(project_path)

    # Create seed files
    _create_project_yaml(project_path / "project.yaml", slug)
    _create_kernel_md(project_path / "kernel.md", slug)
    _create_outline_md(project_path / "outline.md", slug)

    return project_path


def _create_directories(project_path: Path) -> None:
    """Create the required directory structure."""
    directories = [
        project_path,
        project_path / "elements",
        project_path / "research",
        project_path / "exports",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def _create_project_yaml(file_path: Path, slug: str) -> None:
    """Create project.yaml with basic metadata if it doesn't exist."""
    if file_path.exists():
        return

    project_data = {
        "name": slug,
        "created": datetime.now().isoformat(),
        "stage": "capture",
        "description": f"Brainstorming project: {slug}",
        "tags": [],
        "metadata": {
            "version": "1.0.0",
            "format": "brainstormbuddy-project",
        },
    }

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(project_data, f, default_flow_style=False, sort_keys=False)


def _create_kernel_md(file_path: Path, slug: str) -> None:
    """Create kernel.md with minimal structure if it doesn't exist."""
    if file_path.exists():
        return

    content = f"""---
title: Kernel
project: {slug}
created: {datetime.now().isoformat()}
stage: kernel
---

# Kernel

## Core Concept

*The essential idea or problem to explore.*

## Key Questions

*What are we trying to answer or solve?*

## Success Criteria

*How will we know when we've achieved our goal?*
"""

    atomic_write_text(file_path, content)


def _create_outline_md(file_path: Path, slug: str) -> None:
    """Create outline.md with minimal structure if it doesn't exist."""
    if file_path.exists():
        return

    content = f"""---
title: Outline
project: {slug}
created: {datetime.now().isoformat()}
stage: outline
---

# Outline

## Executive Summary

*High-level overview of the project.*

## Main Sections

### Section 1

*Key points and structure.*

### Section 2

*Key points and structure.*

### Section 3

*Key points and structure.*

## Next Steps

*What needs to be done next?*
"""

    atomic_write_text(file_path, content)


def ensure_project_exists(slug: str, base: Path | str = "projects") -> Path:
    """
    Ensure a project exists, creating it if necessary.

    This is an alias for scaffold_project for clarity in different contexts.
    """
    return scaffold_project(slug, base)
````

## File: app/files/workstream.py
````python
"""Workstream document generation for outline and element files."""

from datetime import datetime
from pathlib import Path

from app.files.batch import BatchDiff


def generate_outline_content(project_name: str, kernel_summary: str | None = None) -> str:
    """
    Generate content for outline.md file.

    Args:
        project_name: Name of the project
        kernel_summary: Optional summary from kernel stage

    Returns:
        Markdown content for outline.md
    """
    timestamp = datetime.now().isoformat()

    kernel_section = ""
    if kernel_summary:
        kernel_section = f"""
## From Kernel

{kernel_summary}
"""

    return f"""---
title: Outline
project: {project_name}
created: {timestamp}
stage: outline
---

# Project Outline: {project_name}

## Executive Summary

*A concise overview of the project's goals, scope, and expected outcomes.*
{kernel_section}

## Core Objectives

1. **Primary Goal**: *What is the main thing we're trying to achieve?*
2. **Secondary Goals**: *What else would we like to accomplish?*
3. **Success Metrics**: *How will we measure success?*

## Key Workstreams

### Requirements Definition
- Functional requirements
- Non-functional requirements
- Constraints and assumptions
- See: [requirements.md](elements/requirements.md)

### Research & Analysis
- Background research
- Market analysis
- Technical feasibility
- See: [research.md](elements/research.md)

### Solution Design
- Architecture overview
- Key components
- Integration points
- See: [design.md](elements/design.md)

### Implementation Plan
- Phases and milestones
- Resource requirements
- Risk mitigation
- See: [implementation.md](elements/implementation.md)

### Synthesis & Recommendations
- Key findings
- Recommended approach
- Next steps
- See: [synthesis.md](elements/synthesis.md)

## Timeline

*Proposed timeline for the project.*

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Research | 1-2 weeks | Research findings, feasibility analysis |
| Design | 1 week | Architecture, specifications |
| Implementation | 2-4 weeks | Working prototype/solution |
| Testing & Refinement | 1 week | Validated solution |

## Open Questions

- *What questions need to be answered before proceeding?*
- *What assumptions need validation?*
- *What dependencies need resolution?*

## Notes

*Additional context, references, or considerations.*
"""


def generate_element_content(element_type: str, project_name: str) -> str:
    """
    Generate content for element markdown files.

    Args:
        element_type: Type of element (requirements, research, design, etc.)
        project_name: Name of the project

    Returns:
        Markdown content for the element file
    """
    timestamp = datetime.now().isoformat()

    templates = {
        "requirements": f"""---
title: Requirements
project: {project_name}
created: {timestamp}
type: element
workstream: requirements
---

# Requirements

## Functional Requirements

### Core Features
- *What must the solution do?*
- *What are the essential capabilities?*

### User Stories
- As a [user type], I want to [action] so that [benefit]
- *Add more user stories as needed*

## Non-Functional Requirements

### Performance
- *Response time expectations*
- *Throughput requirements*
- *Scalability needs*

### Security
- *Authentication/authorization requirements*
- *Data protection needs*
- *Compliance requirements*

### Usability
- *User experience requirements*
- *Accessibility needs*
- *Documentation requirements*

## Constraints

### Technical Constraints
- *Platform limitations*
- *Technology stack requirements*
- *Integration requirements*

### Business Constraints
- *Budget limitations*
- *Timeline restrictions*
- *Resource availability*

## Assumptions

- *What are we assuming to be true?*
- *What dependencies are we counting on?*

## Acceptance Criteria

- *How will we know the requirements are met?*
- *What tests or validations will we perform?*
""",
        "research": f"""---
title: Research
project: {project_name}
created: {timestamp}
type: element
workstream: research
---

# Research & Analysis

## Background Research

### Domain Context
- *What is the problem space?*
- *What are the key concepts?*
- *What terminology is important?*

### Prior Art
- *What existing solutions are there?*
- *What can we learn from them?*
- *What gaps do they leave?*

## Market Analysis

### Target Audience
- *Who are the users?*
- *What are their needs?*
- *What are their pain points?*

### Competitive Landscape
- *Who are the competitors?*
- *What are their strengths/weaknesses?*
- *What opportunities exist?*

## Technical Research

### Technology Options
- *What technologies could we use?*
- *What are the trade-offs?*
- *What are the risks?*

### Feasibility Analysis
- *Is the solution technically feasible?*
- *What are the technical challenges?*
- *What POCs or experiments are needed?*

## Key Findings

1. **Finding 1**: *Description and implications*
2. **Finding 2**: *Description and implications*
3. **Finding 3**: *Description and implications*

## Recommendations

- *Based on research, what do we recommend?*
- *What approach should we take?*
- *What should we avoid?*

## References

- *List of sources, links, and citations*
""",
        "design": f"""---
title: Design
project: {project_name}
created: {timestamp}
type: element
workstream: design
---

# Solution Design

## Architecture Overview

### High-Level Architecture
- *System architecture diagram or description*
- *Key components and their relationships*
- *Data flow overview*

### Design Principles
- *What principles guide the design?*
- *What patterns are we following?*
- *What best practices apply?*

## Component Design

### Core Components
1. **Component 1**
   - Purpose: *What it does*
   - Responsibilities: *What it's responsible for*
   - Interfaces: *How it interacts with other components*

2. **Component 2**
   - Purpose: *What it does*
   - Responsibilities: *What it's responsible for*
   - Interfaces: *How it interacts with other components*

### Data Model
- *Data structures and schemas*
- *Database design if applicable*
- *Data flow and transformations*

## Integration Points

### External Systems
- *What external systems do we integrate with?*
- *What are the integration methods?*
- *What are the data formats?*

### APIs and Interfaces
- *What APIs do we expose?*
- *What protocols do we use?*
- *What are the contracts?*

## Security Design

### Authentication & Authorization
- *How do we handle authentication?*
- *How do we manage authorization?*
- *What security patterns do we use?*

### Data Protection
- *How do we protect data at rest?*
- *How do we protect data in transit?*
- *What encryption do we use?*

## Performance Considerations

- *What are the performance bottlenecks?*
- *How do we optimize for performance?*
- *What caching strategies do we use?*

## Deployment Architecture

- *How will the solution be deployed?*
- *What infrastructure is required?*
- *What are the scaling considerations?*
""",
        "implementation": f"""---
title: Implementation Plan
project: {project_name}
created: {timestamp}
type: element
workstream: implementation
---

# Implementation Plan

## Development Approach

### Methodology
- *Agile, Waterfall, or hybrid approach?*
- *Sprint/iteration structure*
- *Development workflow*

### Team Structure
- *Required roles and responsibilities*
- *Team size and composition*
- *Communication structure*

## Phases and Milestones

### Phase 1: Foundation
**Duration**: *X weeks*
**Deliverables**:
- *Core infrastructure setup*
- *Basic functionality*
- *Initial testing framework*

### Phase 2: Core Features
**Duration**: *X weeks*
**Deliverables**:
- *Main feature implementation*
- *Integration work*
- *Testing and validation*

### Phase 3: Enhancement
**Duration**: *X weeks*
**Deliverables**:
- *Additional features*
- *Performance optimization*
- *Polish and refinement*

### Phase 4: Deployment
**Duration**: *X weeks*
**Deliverables**:
- *Production deployment*
- *Documentation*
- *Training materials*

## Resource Requirements

### Human Resources
- *Developer hours needed*
- *Specialist expertise required*
- *Support staff needs*

### Technical Resources
- *Development environments*
- *Testing infrastructure*
- *Production infrastructure*

### Tools and Licenses
- *Required software tools*
- *License costs*
- *Third-party services*

## Risk Management

### Identified Risks
1. **Risk 1**: *Description and impact*
   - Mitigation: *How we'll address it*
2. **Risk 2**: *Description and impact*
   - Mitigation: *How we'll address it*

### Contingency Planning
- *What if timelines slip?*
- *What if resources are unavailable?*
- *What if requirements change?*

## Quality Assurance

### Testing Strategy
- *Unit testing approach*
- *Integration testing plan*
- *User acceptance testing*

### Code Quality
- *Code review process*
- *Quality metrics*
- *Documentation standards*

## Success Criteria

- *How do we know implementation is successful?*
- *What metrics will we track?*
- *What are the acceptance criteria?*
""",
        "synthesis": f"""---
title: Synthesis
project: {project_name}
created: {timestamp}
type: element
workstream: synthesis
---

# Synthesis & Recommendations

## Executive Summary

*High-level summary of the entire project, findings, and recommendations.*

## Key Findings

### Finding 1: *Title*
**Evidence**: *What supports this finding?*
**Implications**: *What does this mean for the project?*
**Confidence**: High/Medium/Low

### Finding 2: *Title*
**Evidence**: *What supports this finding?*
**Implications**: *What does this mean for the project?*
**Confidence**: High/Medium/Low

### Finding 3: *Title*
**Evidence**: *What supports this finding?*
**Implications**: *What does this mean for the project?*
**Confidence**: High/Medium/Low

## Integrated Analysis

### Connecting the Dots
- *How do the findings relate to each other?*
- *What patterns emerge?*
- *What story do they tell together?*

### Trade-offs and Decisions
- *What trade-offs were identified?*
- *What decisions were made and why?*
- *What alternatives were considered?*

## Recommendations

### Primary Recommendation
**What**: *Clear statement of what should be done*
**Why**: *Justification based on findings*
**How**: *High-level approach*
**When**: *Suggested timeline*

### Alternative Options
1. **Option A**: *Description, pros, cons*
2. **Option B**: *Description, pros, cons*

## Implementation Roadmap

### Immediate Next Steps (0-2 weeks)
1. *Action item 1*
2. *Action item 2*
3. *Action item 3*

### Short-term Actions (2-8 weeks)
- *Key activities and milestones*

### Long-term Vision (3+ months)
- *Future enhancements and evolution*

## Critical Success Factors

- *What must be in place for success?*
- *What could derail the project?*
- *What support is needed?*

## Conclusion

*Final thoughts, key takeaways, and call to action.*

## Appendices

### A. Detailed Evidence
*Supporting data, research details, calculations*

### B. Stakeholder Feedback
*Input from various stakeholders*

### C. References and Resources
*Bibliography, links, additional reading*
""",
    }

    return templates.get(
        element_type,
        f"""---
title: {element_type.title()}
project: {project_name}
created: {timestamp}
type: element
workstream: {element_type}
---

# {element_type.title()}

*Content for {element_type} workstream.*
""",
    )


def create_workstream_batch(
    project_path: Path,
    project_name: str,
    kernel_summary: str | None = None,
    include_elements: list[str] | None = None,
) -> BatchDiff:
    """
    Create a batch of workstream documents for a project.

    Args:
        project_path: Path to the project directory
        project_name: Name of the project
        kernel_summary: Optional summary from kernel stage
        include_elements: List of element types to include (default: all)

    Returns:
        BatchDiff instance ready to preview or apply
    """
    batch = BatchDiff()

    # Default elements if not specified
    if include_elements is None:
        include_elements = [
            "requirements",
            "research",
            "design",
            "implementation",
            "synthesis",
        ]

    # Add outline.md
    outline_path = project_path / "outline.md"
    outline_content = generate_outline_content(project_name, kernel_summary)

    if outline_path.exists():
        with open(outline_path, encoding="utf-8") as f:
            old_content = f.read()
    else:
        old_content = ""

    batch.add_file(outline_path, old_content, outline_content)

    # Add element files
    elements_dir = project_path / "elements"
    for element_type in include_elements:
        element_path = elements_dir / f"{element_type}.md"
        element_content = generate_element_content(element_type, project_name)

        if element_path.exists():
            with open(element_path, encoding="utf-8") as f:
                old_content = f.read()
        else:
            old_content = ""

        batch.add_file(element_path, old_content, element_content)

    return batch
````

## File: app/llm/prompts/research.md
````markdown
<instructions>
You are in the research stage as a "researcher" agent. Your goal is to extract atomic findings from provided sources and structure them for integration into the project's knowledge base. Do not perform any web calls - work only with the provided content. Output findings as machine-readable JSONL for SQLite FTS ingestion.
</instructions>

<context>
You have access to read project documents and provided research content. Your role is to decompose complex information into discrete, verifiable claims with proper attribution. Each finding should be self-contained and traceable to its source. Focus on relevance to the project's kernel and workstreams.
</context>

<format>
Output ONLY a single fenced code block of type jsonl containing one JSON object per line. Do not include any text outside the fenced block. Each line must be a valid JSON object with these exact keys:

- id: UUID string (e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
- url: Source URL or document reference
- source_type: Type of source (e.g., "article", "documentation", "research_paper")
- claim: One specific, falsifiable statement extracted from the source
- evidence: Direct quote or paraphrase supporting the claim (max 100 words)
- confidence: Float between 0.0 and 1.0 based on source reliability and claim specificity
- tags: Comma-separated keywords for categorization (e.g., "architecture,performance,caching")
- workstream: Which project workstream this finding supports
- retrieved_at: ISO8601 timestamp (e.g., "2024-01-15T14:30:00Z")

Example (exactly 2 lines in the jsonl block):

```jsonl
{"id": "f47ac10b-58cc-4372-a567-0e02b2c3d479", "url": "https://docs.python.org/3/library/sqlite3.html", "source_type": "documentation", "claim": "SQLite FTS5 extension provides full-text search with BM25 ranking", "evidence": "FTS5 is an SQLite virtual table module that provides full-text search functionality with built-in BM25 ranking algorithm for relevance scoring", "confidence": 0.95, "tags": "sqlite,fts,search,ranking", "workstream": "research", "retrieved_at": "2024-01-15T10:45:00Z"}
{"id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", "url": "https://textual.textualize.io/guide/", "source_type": "article", "claim": "Textual provides reactive data binding for TUI components", "evidence": "Textual's reactive attributes automatically update the UI when their values change, enabling declarative UI patterns", "confidence": 0.90, "tags": "textual,tui,reactive,ui", "workstream": "interface", "retrieved_at": "2024-01-15T10:47:00Z"}
```
</format>
````

## File: app/tui/views/__init__.py
````python
"""View modules for the TUI application."""

from .main_screen import MainScreen

__all__ = ["MainScreen"]
````

## File: app/tui/views/main_screen.py
````python
"""Main screen view with three-pane structure."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header

from app.tui.widgets import CommandPalette, ContextPanel, FileTree, SessionViewer


class MainScreen(Screen[None]):
    """Main three-pane screen for the application."""

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }

    Horizontal {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the main three-pane layout."""
        yield Header()
        with Horizontal():
            yield FileTree()
            yield SessionViewer()
            yield ContextPanel()
        yield Footer()
        yield CommandPalette()
````

## File: app/tui/views/research.py
````python
"""Research import view for pasting and storing external findings."""

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Static, TextArea

from app.research.db import ResearchDB
from app.research.ingest import Finding, parse_findings


class ResearchImportModal(ModalScreen[bool]):
    """Modal for importing research findings from external sources."""

    DEFAULT_CSS = """
    ResearchImportModal {
        align: center middle;
    }

    ResearchImportModal > Container {
        width: 95%;
        height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    .modal-title {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    .paste-section {
        height: 12;
        margin-bottom: 1;
        border: solid $primary 50%;
        padding: 1;
    }

    .paste-area {
        height: 8;
        margin: 1 0;
    }

    .import-button-row {
        dock: bottom;
        height: 3;
        align: center middle;
    }

    .table-section {
        height: 1fr;
        margin-bottom: 1;
        border: solid $primary 50%;
        padding: 1;
    }

    .status-message {
        text-align: center;
        width: 100%;
        margin: 1 0;
        color: $success;
    }

    .button-row {
        dock: bottom;
        align: center middle;
        padding: 1 0;
    }

    .button-row Button {
        margin: 0 1;
    }

    .filter-section {
        height: auto;
        margin-bottom: 1;
        border: solid $primary 50%;
        padding: 1;
    }

    .filter-inputs {
        height: auto;
        margin: 1 0;
    }

    .filter-inputs Input {
        margin: 0 0 1 0;
    }

    .filter-button-row {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    .filter-button-row Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def __init__(
        self,
        workstream: str = "research",
        db_path: Path | None = None,
    ) -> None:
        """
        Initialize the research import modal.

        Args:
            workstream: Default workstream for imported findings
            db_path: Path to the research database
        """
        super().__init__()
        self.workstream = workstream
        self.db_path = db_path or Path("projects") / "default" / "research.db"
        self.status_message = ""
        self.findings: list[Finding] = []
        # Filter state
        self.filter_workstream: str = ""
        self.filter_tags: list[str] = []
        self.filter_min_confidence: float | None = None

    def compose(self) -> ComposeResult:
        """Create the research import UI."""
        with Container():
            yield Static("[bold]Import Research Findings[/bold]", classes="modal-title")
            yield Static(
                f"[dim]Default workstream: {self.workstream}[/dim]",
                classes="modal-subtitle",
            )

            # Paste area section
            with Container(classes="paste-section"):
                yield Static("[bold]Paste External Responses[/bold]", classes="section-title")
                yield Static(
                    "[dim]Supports markdown bullets or JSON array format[/dim]",
                    classes="section-subtitle",
                )
                yield TextArea(
                    "",
                    id="paste-area",
                    classes="paste-area",
                )
                with Horizontal(classes="import-button-row"):
                    yield Button("Import Findings", variant="primary", id="import-button")

            # Status message
            yield Static("", id="status-message", classes="status-message")

            # Filter section
            with Container(classes="filter-section"):
                yield Static("[bold]Filters[/bold]", classes="section-title")
                with Container(classes="filter-inputs"):
                    yield Input(
                        placeholder="Filter by workstream...",
                        id="filter-workstream",
                    )
                    yield Input(
                        placeholder="Filter by tags (comma-separated)...",
                        id="filter-tags",
                    )
                    yield Input(
                        placeholder="Minimum confidence (0.0-1.0)...",
                        id="filter-confidence",
                    )
                with Horizontal(classes="filter-button-row"):
                    yield Button("Apply Filters", variant="primary", id="apply-filters")
                    yield Button("Clear Filters", variant="default", id="clear-filters")

            # Table section
            with ScrollableContainer(classes="table-section"):
                yield Static("[bold]Current Findings[/bold]", classes="section-title")
                table = DataTable[str](id="findings-table")
                table.add_columns("Claim", "URL", "Confidence", "Tags", "Workstream")
                yield table

            # Action buttons
            with Horizontal(classes="button-row"):
                yield Button("Close", variant="default", id="close-button")

    async def on_mount(self) -> None:
        """Load existing findings when modal opens."""
        await self.refresh_table()

    async def refresh_table(self) -> None:
        """Refresh the findings table with data from the database."""
        table = self.query_one("#findings-table", DataTable)
        table.clear()

        # Load findings from database
        if self.db_path.exists():
            async with ResearchDB(self.db_path) as db:
                # Apply database-level filters
                findings = await db.list_findings(
                    workstream=self.filter_workstream if self.filter_workstream else None,
                    min_confidence=self.filter_min_confidence,
                    limit=100,
                )

                # Apply client-side tag filtering
                if self.filter_tags:
                    filtered_findings = []
                    for finding in findings:
                        finding_tags = finding.get("tags", [])
                        # Check if any filter tag is in the finding's tags
                        if any(tag in finding_tags for tag in self.filter_tags):
                            filtered_findings.append(finding)
                    findings = filtered_findings

                for finding in findings:
                    tags_str = ", ".join(finding.get("tags", []))
                    confidence_str = f"{finding['confidence']:.0%}"
                    table.add_row(
                        finding["claim"][:80] + ("..." if len(finding["claim"]) > 80 else ""),
                        finding["url"][:40] + ("..." if len(finding["url"]) > 40 else ""),
                        confidence_str,
                        tags_str[:30] + ("..." if len(tags_str) > 30 else ""),
                        finding.get("workstream", ""),
                    )

    @on(Button.Pressed, "#import-button")
    async def handle_import(self) -> None:
        """Process pasted content and import findings."""
        text_area = self.query_one("#paste-area", TextArea)
        content = text_area.text.strip()

        if not content:
            self.update_status("No content to import", is_error=True)
            return

        try:
            # Parse findings from pasted content
            parsed_findings = parse_findings(content, self.workstream)

            if not parsed_findings:
                self.update_status("No valid findings found in pasted content", is_error=True)
                return

            # Store findings in database
            added_count = 0
            skipped_count = 0

            async with ResearchDB(self.db_path) as db:
                # Get existing findings for duplicate check
                existing = await db.list_findings(limit=1000)
                existing_keys = {(f["claim"].lower().strip(), f["url"]) for f in existing}

                for finding in parsed_findings:
                    key = (finding.claim.lower().strip(), finding.url)
                    if key in existing_keys:
                        skipped_count += 1
                    else:
                        await db.insert_finding(
                            url=finding.url,
                            source_type=finding.source_type,
                            claim=finding.claim,
                            evidence=finding.evidence,
                            confidence=finding.confidence,
                            tags=finding.tags,
                            workstream=finding.workstream,
                        )
                        added_count += 1

            # Clear the text area
            text_area.text = ""

            # Update status and refresh table
            self.update_status(
                f"Import complete: {added_count} added, {skipped_count} skipped (duplicates)"
            )
            await self.refresh_table()

        except Exception as e:
            self.update_status(f"Import failed: {str(e)}", is_error=True)

    def update_status(self, message: str, is_error: bool = False) -> None:
        """Update the status message."""
        status_widget = self.query_one("#status-message", Static)
        if is_error:
            status_widget.update(f"[red]{message}[/red]")
        else:
            status_widget.update(f"[green]{message}[/green]")

    @on(Button.Pressed, "#close-button")
    def handle_close(self) -> None:
        """Close the modal."""
        self.dismiss(True)

    @on(Button.Pressed, "#apply-filters")
    async def handle_apply_filters(self) -> None:
        """Apply the current filter values."""
        # Get filter values from inputs
        workstream_input = self.query_one("#filter-workstream", Input)
        tags_input = self.query_one("#filter-tags", Input)
        confidence_input = self.query_one("#filter-confidence", Input)

        # Update filter state
        self.filter_workstream = workstream_input.value.strip()

        # Parse tags (comma-separated)
        tags_text = tags_input.value.strip()
        if tags_text:
            self.filter_tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        else:
            self.filter_tags = []

        # Parse confidence (validate it's between 0.0 and 1.0)
        confidence_text = confidence_input.value.strip()
        if confidence_text:
            try:
                confidence = float(confidence_text)
                if 0.0 <= confidence <= 1.0:
                    self.filter_min_confidence = confidence
                    self.update_status("Filters applied", is_error=False)
                else:
                    self.update_status("Confidence must be between 0.0 and 1.0", is_error=True)
                    return
            except ValueError:
                self.update_status("Invalid confidence value", is_error=True)
                return
        else:
            self.filter_min_confidence = None

        # Refresh the table with filters
        await self.refresh_table()

    @on(Button.Pressed, "#clear-filters")
    async def handle_clear_filters(self) -> None:
        """Clear all filters and reset inputs."""
        # Clear filter state
        self.filter_workstream = ""
        self.filter_tags = []
        self.filter_min_confidence = None

        # Clear input fields
        workstream_input = self.query_one("#filter-workstream", Input)
        tags_input = self.query_one("#filter-tags", Input)
        confidence_input = self.query_one("#filter-confidence", Input)

        workstream_input.value = ""
        tags_input.value = ""
        confidence_input.value = ""

        self.update_status("Filters cleared", is_error=False)

        # Refresh the table without filters
        await self.refresh_table()

    def action_close(self) -> None:
        """Handle escape key to close."""
        self.dismiss(True)
````

## File: app/tui/widgets/file_tree.py
````python
"""File tree widget for project navigation."""

from textual.widgets import Tree


class FileTree(Tree[str]):
    """File tree for navigating project documents."""

    DEFAULT_CSS = """
    FileTree {
        width: 30;
        background: $surface;
        border: solid $primary;
    }
    """

    def __init__(self) -> None:
        """Initialize the file tree with placeholder content."""
        super().__init__("Projects", id="file-tree")

    def on_mount(self) -> None:
        """Populate the tree with placeholder project structure."""
        root = self.root
        root.expand()

        # Add placeholder project structure
        project1 = root.add("📁 example-project", expand=True)
        project1.add_leaf("📄 kernel.md")
        project1.add_leaf("📄 outline.md")
        project1.add_leaf("📄 project.yaml")

        elements = project1.add("📁 elements", expand=True)
        elements.add_leaf("📄 workstream-1.md")
        elements.add_leaf("📄 workstream-2.md")

        research = project1.add("📁 research", expand=True)
        research.add_leaf("📄 findings.md")

        exports = project1.add("📁 exports", expand=True)
        exports.add_leaf("📄 synthesis.md")
````

## File: app/tui/widgets/session_viewer.py
````python
"""Session viewer widget for displaying editor content or Claude streams."""

from textual.widgets import RichLog


class SessionViewer(RichLog):
    """Main content viewer for editing documents or viewing session output."""

    DEFAULT_CSS = """
    SessionViewer {
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    """

    def __init__(self) -> None:
        """Initialize the session viewer."""
        super().__init__(id="session-viewer", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        """Display welcome message on mount."""
        self.write("[bold cyan]Welcome to Brainstorm Buddy[/bold cyan]\n")
        self.write("\nA terminal-first brainstorming app that guides you through:\n")
        self.write("• [yellow]Capture[/yellow] → [yellow]Clarify[/yellow] → ")
        self.write("[yellow]Kernel[/yellow] → [yellow]Outline[/yellow] → ")
        self.write("[yellow]Research[/yellow] → [yellow]Synthesis[/yellow] → ")
        self.write("[yellow]Export[/yellow]\n")
        self.write("\n[dim]Press ':' to open the command palette[/dim]")

    def write(
        self,
        content: object,
        width: int | None = None,
        expand: bool = False,
        shrink: bool = True,
        scroll_end: bool | None = None,
        animate: bool = False,
    ) -> "SessionViewer":
        """
        Write text to the viewer with optional scrolling.

        Args:
            content: Content to write (supports Rich markup)
            width: Width hint for content
            expand: Whether to expand content to full width
            shrink: Whether to shrink content to fit
            scroll_end: Whether to scroll to the end after writing
            animate: Whether to animate scrolling

        Returns:
            Self for chaining
        """
        super().write(
            content,
            width=width,
            expand=expand,
            shrink=shrink,
            scroll_end=scroll_end,
            animate=animate,
        )
        return self
````

## File: app/tui/__init__.py
````python
"""TUI module for Brainstorm Buddy."""
````

## File: app/__init__.py
````python
"""Brainstorm Buddy - Python terminal-first brainstorming app."""

__version__ = "0.1.0"
````

## File: brainstormbuddy/.obsidian/workspace.json
````json
{
  "main": {
    "id": "c9770cc6bfb7b9dd",
    "type": "split",
    "children": [
      {
        "id": "387ea85083a296f6",
        "type": "tabs",
        "children": [
          {
            "id": "ac74706926fea592",
            "type": "leaf",
            "state": {
              "type": "markdown",
              "state": {
                "file": "Welcome.md",
                "mode": "source",
                "source": false
              },
              "icon": "lucide-file",
              "title": "Welcome"
            }
          }
        ]
      }
    ],
    "direction": "vertical"
  },
  "left": {
    "id": "ff992d2badc930c6",
    "type": "split",
    "children": [
      {
        "id": "7179f113afc8c1b1",
        "type": "tabs",
        "children": [
          {
            "id": "b510e60ac73b5ffd",
            "type": "leaf",
            "state": {
              "type": "file-explorer",
              "state": {
                "sortOrder": "alphabetical",
                "autoReveal": false
              },
              "icon": "lucide-folder-closed",
              "title": "Files"
            }
          },
          {
            "id": "c947aeb017ea6771",
            "type": "leaf",
            "state": {
              "type": "search",
              "state": {
                "query": "",
                "matchingCase": false,
                "explainSearch": false,
                "collapseAll": false,
                "extraContext": false,
                "sortOrder": "alphabetical"
              },
              "icon": "lucide-search",
              "title": "Search"
            }
          },
          {
            "id": "5c82e1dd20dfb01b",
            "type": "leaf",
            "state": {
              "type": "bookmarks",
              "state": {},
              "icon": "lucide-bookmark",
              "title": "Bookmarks"
            }
          }
        ]
      }
    ],
    "direction": "horizontal",
    "width": 300
  },
  "right": {
    "id": "3bc2bd1cfd7999fa",
    "type": "split",
    "children": [
      {
        "id": "e6cc26d4072cfb9f",
        "type": "tabs",
        "children": [
          {
            "id": "db35ce30a57e9f72",
            "type": "leaf",
            "state": {
              "type": "backlink",
              "state": {
                "collapseAll": false,
                "extraContext": false,
                "sortOrder": "alphabetical",
                "showSearch": false,
                "searchQuery": "",
                "backlinkCollapsed": false,
                "unlinkedCollapsed": true
              },
              "icon": "links-coming-in",
              "title": "Backlinks"
            }
          },
          {
            "id": "9e144b07e94c02c9",
            "type": "leaf",
            "state": {
              "type": "outgoing-link",
              "state": {
                "linksCollapsed": false,
                "unlinkedCollapsed": true
              },
              "icon": "links-going-out",
              "title": "Outgoing links"
            }
          },
          {
            "id": "af8ee537cc1ed312",
            "type": "leaf",
            "state": {
              "type": "tag",
              "state": {
                "sortOrder": "frequency",
                "useHierarchy": true,
                "showSearch": false,
                "searchQuery": ""
              },
              "icon": "lucide-tags",
              "title": "Tags"
            }
          },
          {
            "id": "89a06c137d5cbc28",
            "type": "leaf",
            "state": {
              "type": "outline",
              "state": {
                "followCursor": false,
                "showSearch": false,
                "searchQuery": ""
              },
              "icon": "lucide-list",
              "title": "Outline"
            }
          }
        ]
      }
    ],
    "direction": "horizontal",
    "width": 300,
    "collapsed": true
  },
  "left-ribbon": {
    "hiddenItems": {
      "switcher:Open quick switcher": false,
      "graph:Open graph view": false,
      "canvas:Create new canvas": false,
      "daily-notes:Open today's daily note": false,
      "templates:Insert template": false,
      "command-palette:Open command palette": false,
      "bases:Create new base": false
    }
  },
  "floating": {
    "id": "a807f2187b444222",
    "type": "floating",
    "children": [
      {
        "id": "f63e24ad7469765b",
        "type": "window",
        "children": [
          {
            "id": "38b7bc2d6e783252",
            "type": "tabs",
            "children": [
              {
                "id": "3b33062978337689",
                "type": "leaf",
                "state": {
                  "type": "graph",
                  "state": {},
                  "icon": "lucide-git-fork",
                  "title": "Graph view"
                }
              }
            ]
          }
        ],
        "direction": "vertical",
        "x": 1190,
        "y": 116,
        "width": 600,
        "height": 760,
        "maximize": false,
        "zoom": 0
      }
    ]
  },
  "active": "3b33062978337689",
  "lastOpenFiles": [
    "Welcome.md"
  ]
}
````

## File: .pre-commit-config.yaml
````yaml
# See https://pre-commit.com for more information
# See https://pre-commit.com/hooks.html for more hooks
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    # Ruff version.
    rev: v0.7.0
    hooks:
      # Run the linter.
      - id: ruff
        args: [--fix]
      # Run the formatter.
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: check-toml
      - id: debug-statements
      - id: mixed-line-ending
        args: ['--fix=lf']

# Optional: Add mypy hook (commented out by default as it can be slow)
# - repo: https://github.com/pre-commit/mirrors-mypy
#   rev: v1.13.0
#   hooks:
#     - id: mypy
#       additional_dependencies: [types-all]
#       args: [--strict, --ignore-missing-imports]
````

## File: .github/workflows/security.yml
````yaml
name: Security

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  dependency-check:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v5

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install uv
      uses: astral-sh/setup-uv@v6
      with:
        enable-cache: true
        cache-dependency-glob: "requirements*.txt"

    - name: Create virtual environment and install dependencies
      run: |
        uv venv
        uv pip install -r requirements.txt

    - name: Check for dependency vulnerabilities with pip-audit
      run: |
        uv pip install pip-audit
        source .venv/bin/activate
        pip-audit

    - name: Run Bandit security linter
      run: |
        uv pip install bandit[toml]
        source .venv/bin/activate
        bandit -r app/ -ll

    - name: Check for outdated dependencies
      run: |
        uv pip list --outdated
      continue-on-error: true

  codeql-analysis:
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    steps:
    - uses: actions/checkout@v5

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: python

    - name: Autobuild
      uses: github/codeql-action/autobuild@v3

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3
````

## File: app/files/batch.py
````python
"""Batch diff builder and preview for atomic multi-file operations."""

from dataclasses import dataclass, field
from pathlib import Path

from app.files.diff import (
    Patch,
    apply_patches,
    compute_patch,
    generate_diff_preview,
    is_unchanged,
)


@dataclass
class FileChange:
    """Represents a pending change to a single file."""

    path: Path
    old_content: str
    new_content: str

    @property
    def is_new_file(self) -> bool:
        """Check if this represents a new file creation."""
        return self.old_content == ""

    @property
    def has_changes(self) -> bool:
        """Check if there are actual changes."""
        patch = compute_patch(self.old_content, self.new_content)
        return not is_unchanged(patch)


@dataclass
class BatchDiff:
    """Aggregates multiple file changes for atomic batch operations."""

    changes: list[FileChange] = field(default_factory=list)

    def add_file(self, path: Path | str, old_content: str, new_content: str) -> None:
        """
        Add a file change to the batch.

        Args:
            path: Path to the file
            old_content: Current content (empty string for new files)
            new_content: New content to write
        """
        file_path = Path(path) if isinstance(path, str) else path
        change = FileChange(file_path, old_content, new_content)

        # Only add if there are actual changes
        if change.has_changes:
            self.changes.append(change)

    def add_new_file(self, path: Path | str, content: str) -> None:
        """
        Convenience method to add a new file creation.

        Args:
            path: Path to the new file
            content: Content for the new file
        """
        self.add_file(path, "", content)

    def add_existing_file(self, path: Path | str, new_content: str) -> None:
        """
        Add an existing file modification, reading current content.

        Args:
            path: Path to the existing file
            new_content: New content to write

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        file_path = Path(path) if isinstance(path, str) else path

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            old_content = f.read()

        self.add_file(file_path, old_content, new_content)

    def generate_preview(self, context_lines: int = 3) -> str:
        """
        Generate a combined diff preview for all changes.

        Args:
            context_lines: Number of context lines around changes

        Returns:
            Combined diff preview as a string
        """
        if not self.changes:
            return "No changes to preview."

        previews = []

        for change in self.changes:
            # Generate individual diff with file path as label
            diff = generate_diff_preview(
                change.old_content,
                change.new_content,
                context_lines=context_lines,
                from_label=f"{change.path} (current)",
                to_label=f"{change.path} (proposed)",
            )

            # Add separator between files
            if diff != "No changes detected.":
                previews.append(f"{'=' * 60}")
                previews.append(f"File: {change.path}")
                if change.is_new_file:
                    previews.append("(new file)")
                previews.append(f"{'=' * 60}")
                previews.append(diff)

        if not previews:
            return "No changes to preview."

        return "\n".join(previews)

    def apply(self) -> list[Patch]:
        """
        Apply all changes atomically.

        Either all files are updated successfully, or none are modified.
        Uses temporary files and atomic replacement to ensure safety.

        Returns:
            List of Patch objects for applied changes

        Raises:
            IOError: If atomic replacement fails
            ValueError: If any file's current content doesn't match expected
        """
        if not self.changes:
            return []

        # Convert to format expected by apply_patches
        patches_list: list[tuple[Path | str, str, str]] = [
            (change.path, change.old_content, change.new_content) for change in self.changes
        ]

        # Apply all patches atomically
        return apply_patches(patches_list)

    def clear(self) -> None:
        """Clear all pending changes."""
        self.changes.clear()

    def __len__(self) -> int:
        """Return the number of pending changes."""
        return len(self.changes)

    def __bool__(self) -> bool:
        """Return True if there are pending changes."""
        return len(self.changes) > 0


def create_batch_from_dict(files: dict[str, str], base_path: Path | None = None) -> BatchDiff:
    """
    Create a BatchDiff from a dictionary of relative paths to content.

    Args:
        files: Dictionary mapping relative paths to file content
        base_path: Base directory for resolving relative paths

    Returns:
        BatchDiff instance with all file changes
    """
    batch = BatchDiff()

    for rel_path, content in files.items():
        full_path = base_path / rel_path if base_path else Path(rel_path)

        # Check if file exists to determine old content
        if full_path.exists():
            with open(full_path, encoding="utf-8") as f:
                old_content = f.read()
        else:
            old_content = ""

        batch.add_file(full_path, old_content, content)

    return batch
````

## File: app/tui/widgets/kernel_approval.py
````python
"""Modal widget for approving kernel changes with diff preview."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class KernelApprovalModal(ModalScreen[bool]):
    """Modal for reviewing and approving kernel changes."""

    DEFAULT_CSS = """
    KernelApprovalModal {
        align: center middle;
    }

    KernelApprovalModal > Container {
        background: $surface;
        width: 90%;
        height: 80%;
        border: thick $primary;
        padding: 1;
    }

    KernelApprovalModal .diff-container {
        height: 1fr;
        margin-bottom: 1;
        border: solid $primary;
        padding: 1;
    }

    KernelApprovalModal .button-container {
        height: 3;
        align: center middle;
    }

    KernelApprovalModal Button {
        margin: 0 1;
        width: 16;
    }

    KernelApprovalModal .accept-button {
        background: $success;
    }

    KernelApprovalModal .reject-button {
        background: $warning;
    }
    """

    BINDINGS = [
        Binding("y", "accept", "Accept", priority=True),
        Binding("n", "reject", "Reject", priority=True),
        Binding("escape", "reject", "Cancel"),
    ]

    def __init__(
        self,
        diff_content: str,
        project_slug: str,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Initialize the kernel approval modal.

        Args:
            diff_content: The diff preview to display
            project_slug: The project identifier
            name: Optional widget name
            id: Optional widget ID
            classes: Optional CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.diff_content = diff_content
        self.project_slug = project_slug

    def compose(self) -> ComposeResult:
        """Compose the modal UI."""
        with Container():
            yield Label(f"[bold]Kernel Changes for Project: {self.project_slug}[/bold]")
            yield Label("[dim]Review the changes below and approve or reject[/dim]")

            with ScrollableContainer(classes="diff-container"):
                yield Static(self.diff_content, markup=False)

            with Horizontal(classes="button-container"):
                yield Button(
                    "Accept (Y)",
                    variant="success",
                    classes="accept-button",
                    id="accept",
                )
                yield Button(
                    "Reject (N)",
                    variant="warning",
                    classes="reject-button",
                    id="reject",
                )

    def action_accept(self) -> None:
        """Accept the changes."""
        self.dismiss(True)

    def action_reject(self) -> None:
        """Reject the changes."""
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "accept":
            self.action_accept()
        elif event.button.id == "reject":
            self.action_reject()
````

## File: app/cli.py
````python
"""Command-line interface for Brainstorm Buddy."""

import sys
from pathlib import Path

import typer

from app.permissions.settings_writer import write_project_settings

app = typer.Typer(
    name="bb",
    help="Brainstorm Buddy CLI - Tools for managing brainstorming sessions and Claude configs",
)


@app.command()
def materialize_claude(
    dest: str = typer.Option(..., "--dest", "-d", help="Destination path for .claude config"),
    config_dir_name: str = typer.Option(
        ".claude", "--config-dir-name", "-c", help="Name of the configuration directory"
    ),
) -> None:
    """Generate Claude configuration at the specified destination."""
    try:
        # Convert string to Path
        dest_path = Path(dest).resolve()

        # Ensure the destination directory exists
        dest_path.mkdir(parents=True, exist_ok=True)

        # Generate the Claude configuration
        config_dir = write_project_settings(
            repo_root=dest_path,
            config_dir_name=config_dir_name,
            import_hooks_from="app.permissions.hooks_lib",
        )

        print(f"✓ Successfully created Claude configuration at: {config_dir}")
        print(f"  Settings: {config_dir}/settings.json")
        print(f"  Hooks: {config_dir}/hooks/")
        print()
        print("To use this configuration with Claude Code:")
        print(f"  cd {dest_path}")
        print("  claude")

    except Exception as e:
        print(f"✗ Failed to create Claude configuration: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    app()
````

## File: .github/workflows/release.yml
````yaml
name: Release

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release (e.g., v1.0.0)'
        required: true
        type: string

permissions:
  contents: write

jobs:
  build-and-release:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v5

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install uv
      uses: astral-sh/setup-uv@v6
      with:
        enable-cache: true
        cache-dependency-glob: "requirements*.txt"

    - name: Create virtual environment and install dependencies
      run: |
        uv venv
        uv pip install -r requirements-dev.txt

    - name: Run full test suite
      run: |
        source .venv/bin/activate
        ruff check .
        mypy . --strict
        pytest -q

    - name: Build package
      run: |
        source .venv/bin/activate
        python -m build

    - name: Create GitHub Release
      if: startsWith(github.ref, 'refs/tags/')
      uses: softprops/action-gh-release@v2
      with:
        files: dist/*
        generate_release_notes: true
        draft: false
        prerelease: ${{ contains(github.ref, '-beta') || contains(github.ref, '-alpha') }}

    - name: Publish to PyPI
      if: startsWith(github.ref, 'refs/tags/') && !contains(github.ref, '-beta') && !contains(github.ref, '-alpha')
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        source .venv/bin/activate
        twine upload dist/*
````

## File: app/files/diff.py
````python
"""Diff and patch utilities for atomic file operations."""

import difflib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.files.atomic import atomic_write_text


@dataclass
class Patch:
    """Represents a patch to be applied to a file."""

    original: str
    modified: str
    diff_lines: list[str]


def compute_patch(old: str, new: str) -> Patch:
    """
    Compute a patch representing the difference between two strings.

    Args:
        old: Original text content
        new: Modified text content

    Returns:
        Patch object containing the diff information
    """
    # Split into lines while preserving line endings
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    # Generate unified diff
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        lineterm="",
    )

    return Patch(
        original=old,
        modified=new,
        diff_lines=list(diff),
    )


def apply_patch(path: Path | str, patch: Patch) -> None:
    """
    Apply a patch to a file atomically using temp file and replace.

    This ensures the file is either fully updated or not modified at all,
    preventing partial writes in case of errors.

    Args:
        path: Path to the file to patch
        patch: Patch object to apply

    Raises:
        IOError: If there's an error during the atomic write operation
    """
    # Delegate to atomic_write_text for the actual atomic write
    atomic_write_text(path, patch.modified)


def generate_diff_preview(
    old: str,
    new: str,
    context_lines: int = 3,
    from_label: str | None = None,
    to_label: str | None = None,
) -> str:
    """
    Generate a human-readable diff preview.

    Args:
        old: Original text content
        new: Modified text content
        context_lines: Number of context lines to show around changes
        from_label: Optional label for the original file (defaults to "before")
        to_label: Optional label for the modified file (defaults to "after")

    Returns:
        String representation of the diff suitable for display
    """
    # Split into lines while preserving line endings
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)

    # Generate unified diff with specified context
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=from_label if from_label is not None else "before",
        tofile=to_label if to_label is not None else "after",
        n=context_lines,
        lineterm="",
    )

    diff_lines = list(diff)

    if not diff_lines:
        return "No changes detected."

    # Join with newlines for readable output
    return "\n".join(diff_lines)


def is_unchanged(patch: Patch) -> bool:
    """
    Check if a patch represents no changes.

    Args:
        patch: Patch object to check

    Returns:
        True if the patch represents no changes, False otherwise
    """
    return patch.original == patch.modified or len(patch.diff_lines) == 0


def apply_patch_from_strings(path: Path | str, old_content: str, new_content: str) -> Patch | None:
    """
    Helper function to compute and apply a patch in one operation.

    Args:
        path: Path to the file to patch
        old_content: Expected current content (for verification)
        new_content: New content to write

    Returns:
        The applied Patch object, or None if no changes were needed

    Raises:
        ValueError: If the current file content doesn't match old_content
        IOError: If there's an error during the write operation
    """
    file_path = Path(path) if isinstance(path, str) else path

    # Read current content if file exists
    if file_path.exists():
        with open(file_path, encoding="utf-8") as f:
            current = f.read()
        if current != old_content:
            raise ValueError(f"Current content of {file_path} doesn't match expected old_content")

    # Compute patch
    patch = compute_patch(old_content, new_content)

    # Only apply if there are changes
    if not is_unchanged(patch):
        apply_patch(file_path, patch)
        return patch

    return None


def apply_patches(patches: list[tuple[Path | str, str, str]]) -> list[Patch]:
    """
    Apply multiple file edits atomically (all-or-nothing).

    This function ensures that either all patches are applied successfully,
    or none are applied at all. It writes all temporary files first, then
    replaces all targets atomically. On any failure, all temporary files
    are cleaned up and original files remain unchanged.

    Args:
        patches: List of tuples containing (path, old_content, new_content)

    Returns:
        List of Patch objects for each changed file

    Raises:
        IOError: If there's an error during the atomic write operations
        ValueError: If any file's current content doesn't match expected
    """
    # Prepare all patches and temp files
    temp_files: list[tuple[Path, Path, int | None, str, bool]] = []
    computed_patches: list[Patch] = []
    backup_files: list[tuple[Path, Path]] = []

    try:
        for path_input, old_content, new_content in patches:
            file_path = Path(path_input) if isinstance(path_input, str) else path_input

            # Track whether file existed before operation
            existed_before = file_path.exists()

            # Read and verify current content if file exists
            if existed_before:
                with open(file_path, encoding="utf-8") as f:
                    current = f.read()
                if current != old_content:
                    raise ValueError(
                        f"Current content of {file_path} doesn't match expected old_content"
                    )
                # Preserve file mode
                file_mode = os.stat(file_path).st_mode
            else:
                file_mode = None
                current = ""
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Compute patch
            patch = compute_patch(old_content, new_content)

            # Skip unchanged files
            if is_unchanged(patch):
                continue

            computed_patches.append(patch)

            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=file_path.parent,
                delete=False,
                suffix=".tmp",
            ) as tmp_file:
                tmp_file.write(new_content)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                tmp_path = Path(tmp_file.name)

            # Store temp file info for later replacement
            temp_files.append((file_path, tmp_path, file_mode, current, existed_before))

        # Create backups of existing files before replacement
        for target_path, _, _, original_content, existed_before in temp_files:
            if existed_before:
                # Create backup file
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=target_path.parent,
                    delete=False,
                    suffix=".backup",
                ) as backup_file:
                    backup_file.write(original_content)
                    backup_file.flush()
                    os.fsync(backup_file.fileno())
                    backup_path = Path(backup_file.name)
                backup_files.append((target_path, backup_path))

        # Now replace all files
        completed_replacements = []
        try:
            for target_path, temp_path, file_mode, _, _ in temp_files:
                # Preserve file mode if it existed
                if file_mode is not None:
                    os.chmod(temp_path, file_mode)

                # Atomic replace
                temp_path.replace(target_path)
                completed_replacements.append(target_path)

            # Fsync parent directories for durability (best-effort)
            # Collect unique parent directories
            parent_dirs = set()
            for target_path, _, _, _, _ in temp_files:
                parent_dirs.add(target_path.parent)

            # Fsync each parent directory once
            for parent_dir in parent_dirs:
                try:
                    dfd = os.open(parent_dir, os.O_DIRECTORY)
                    try:
                        os.fsync(dfd)
                    finally:
                        os.close(dfd)
                except OSError:
                    # Platform/filesystem doesn't support directory fsync
                    pass

        except Exception as e:
            # Restore original files from backups or remove newly created files
            for target_path in completed_replacements:
                # Find if this file existed before the operation
                existed_before = False
                for file_path, _, _, _, file_existed in temp_files:
                    if file_path == target_path:
                        existed_before = file_existed
                        break

                if existed_before:
                    # Find the backup for this file and restore it
                    for orig_path, backup_path in backup_files:
                        if orig_path == target_path:
                            backup_path.replace(target_path)
                            break
                else:
                    # File didn't exist before, remove it
                    target_path.unlink(missing_ok=True)

            # Clean up any remaining temp files
            for target_path, temp_path, _, _, _ in temp_files:
                if target_path not in completed_replacements:
                    temp_path.unlink(missing_ok=True)

            # Clean up backup files
            for _, backup_path in backup_files:
                backup_path.unlink(missing_ok=True)

            raise OSError(f"Failed to atomically replace files: {e}") from e

        # Success - clean up backup files
        for _, backup_path in backup_files:
            backup_path.unlink(missing_ok=True)

    except Exception:
        # Clean up any temp files created before the error
        for _, temp_path, _, _, _ in temp_files:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
        raise

    return computed_patches
````

## File: app/tui/widgets/__init__.py
````python
"""Reusable widget components for the TUI."""

from .command_palette import CommandPalette
from .context_panel import ContextPanel
from .domain_editor import DomainEditor
from .file_tree import FileTree
from .kernel_approval import KernelApprovalModal
from .session_viewer import SessionViewer

__all__ = [
    "CommandPalette",
    "ContextPanel",
    "DomainEditor",
    "FileTree",
    "KernelApprovalModal",
    "SessionViewer",
]
````

## File: CLAUDE.md
````markdown
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
````

## File: app/llm/claude_client.py
````python
"""Claude client interface with streaming support and fake implementation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass


@dataclass(frozen=True)
class TextDelta:
    """Represents a text chunk in the stream."""

    text: str


@dataclass(frozen=True)
class ToolUseStart:
    """Indicates the start of tool usage."""

    tool_name: str
    tool_id: str


@dataclass(frozen=True)
class ToolUseEnd:
    """Indicates the end of tool usage."""

    tool_id: str
    result: str | None = None


@dataclass(frozen=True)
class MessageDone:
    """Indicates the message stream is complete."""

    pass


Event = TextDelta | ToolUseStart | ToolUseEnd | MessageDone


class ClaudeClient(ABC):
    """Abstract interface for Claude API clients."""

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        allowed_tools: list[str] | None = None,
        denied_tools: list[str] | None = None,
        permission_mode: str = "standard",
        cwd: str | None = None,
    ) -> AsyncGenerator[Event, None]:
        """
        Stream events from Claude API.

        Args:
            prompt: User prompt to send to Claude
            system_prompt: Optional system prompt to set context
            allowed_tools: List of allowed tool names
            denied_tools: List of denied tool names
            permission_mode: Permission mode for tool usage
            cwd: Current working directory for tool execution

        Yields:
            Event objects representing stream chunks
        """
        raise NotImplementedError
        yield  # pragma: no cover


class FakeClaudeClient(ClaudeClient):
    """Fake implementation for testing with deterministic output."""

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        allowed_tools: list[str] | None = None,
        denied_tools: list[str] | None = None,
        permission_mode: str = "standard",
        cwd: str | None = None,
    ) -> AsyncGenerator[Event, None]:
        """Yield a deterministic sequence of events for testing."""
        # Parameters are intentionally unused in fake implementation
        _ = (allowed_tools, denied_tools, permission_mode, cwd)

        # Check if this is a kernel stage request
        if system_prompt and "kernel stage" in system_prompt.lower():
            # Generate a kernel document based on the prompt
            kernel_content = f"""## Core Concept
The essential idea is to {prompt[:100].lower().strip(".")}. This represents a focused approach to solving a specific problem through systematic exploration and implementation.

## Key Questions
1. What are the fundamental requirements that must be satisfied for this concept to succeed?
2. How can we validate the core assumptions before committing significant resources?
3. What are the critical dependencies and how can we mitigate risks associated with them?
4. How will we measure progress and know when key milestones are achieved?

## Success Criteria
- Clear problem-solution fit demonstrated through user feedback or metrics
- Scalable architecture that can grow with demand
- Measurable improvement over existing alternatives
- Sustainable resource model for long-term viability

## Constraints
- Must work within existing technical infrastructure
- Budget and timeline considerations must be realistic
- Regulatory and compliance requirements must be met
- User experience must remain intuitive and accessible

## Primary Value Proposition
This initiative creates value by directly addressing the identified problem space with a solution that is both practical and innovative. The approach balances technical feasibility with user needs, ensuring that the outcome is not just theoretically sound but also delivers tangible benefits in real-world applications."""

            # Stream the kernel content
            for chunk in kernel_content.split("\n"):
                yield TextDelta(chunk + "\n")

            # Signal completion
            yield MessageDone()

        # Check if this is a clarify stage request
        elif system_prompt and "clarify stage" in system_prompt.lower():
            # Generate clarify questions based on the prompt
            yield TextDelta(f"I see you want to explore: {prompt[:100]}\n\n")
            yield TextDelta(
                "Let me ask some clarifying questions to help sharpen your thinking:\n\n"
            )

            questions = [
                "1. What specific problem are you trying to solve, and who will benefit most from the solution?",
                "2. What constraints (time, budget, technical, regulatory) must you work within?",
                "3. How would you measure success for this initiative after 3 months?",
                "4. What existing solutions have you considered, and why aren't they sufficient?",
                "5. What's the minimum viable version that would still deliver value?",
            ]

            for question in questions:
                yield TextDelta(f"{question}\n\n")

            yield MessageDone()
        else:
            # Default test output
            yield TextDelta("First chunk of text")
            yield TextDelta("Second chunk of text")
            yield MessageDone()
````

## File: app/llm/sessions.py
````python
"""Session policy registry for stage-gated tool permissions and prompts."""

from dataclasses import dataclass, replace
from pathlib import Path

from app.core.config import load_settings
from app.llm.agents import AgentSpec


@dataclass(frozen=True)
class SessionPolicy:
    """Configuration for a brainstorming session stage."""

    stage: str
    system_prompt_path: Path
    allowed_tools: list[str]
    denied_tools: list[str]
    write_roots: list[str]
    permission_mode: str
    web_tools_allowed: list[str]


def get_policy(stage: str) -> SessionPolicy:
    """
    Get the policy configuration for a given stage.

    Args:
        stage: One of 'clarify', 'kernel', 'outline', 'research', 'synthesis'

    Returns:
        SessionPolicy with appropriate configuration

    Raises:
        ValueError: If stage is not recognized
    """
    settings = load_settings()
    base_prompt_path = Path(__file__).resolve().parent / "prompts"

    policies = {
        "clarify": SessionPolicy(
            stage="clarify",
            system_prompt_path=base_prompt_path / "clarify.md",
            allowed_tools=["Read"],
            denied_tools=["Write", "Edit", "Bash", "WebSearch", "WebFetch"],
            write_roots=[],
            permission_mode="readonly",
            web_tools_allowed=[],
        ),
        "kernel": SessionPolicy(
            stage="kernel",
            system_prompt_path=base_prompt_path / "kernel.md",
            allowed_tools=["Read", "Write", "Edit"],
            denied_tools=["Bash", "WebSearch", "WebFetch"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=[],
        ),
        "outline": SessionPolicy(
            stage="outline",
            system_prompt_path=base_prompt_path / "outline.md",
            allowed_tools=["Read", "Write", "Edit"],
            denied_tools=["Bash", "WebSearch", "WebFetch"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=[],
        ),
        "research": SessionPolicy(
            stage="research",
            system_prompt_path=base_prompt_path / "research.md",
            allowed_tools=(
                ["Read", "Write", "Edit", "WebSearch", "WebFetch"]
                if settings.enable_web_tools
                else ["Read", "Write", "Edit"]
            ),
            denied_tools=["Bash"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=(["WebSearch", "WebFetch"] if settings.enable_web_tools else []),
        ),
        "synthesis": SessionPolicy(
            stage="synthesis",
            system_prompt_path=base_prompt_path / "synthesis.md",
            allowed_tools=["Read", "Write", "Edit"],
            denied_tools=["Bash", "WebSearch", "WebFetch"],
            write_roots=["projects/**"],
            permission_mode="restricted",
            web_tools_allowed=[],
        ),
    }

    if stage not in policies:
        raise ValueError(f"Unknown stage: {stage}. Valid stages are: {', '.join(policies.keys())}")

    return policies[stage]


def merge_agent_policy(stage_policy: SessionPolicy, agent_spec: AgentSpec | None) -> SessionPolicy:
    """
    Merge an agent specification with a stage policy.

    Rules:
    - If agent_spec is None, return the stage policy unchanged
    - If agent has empty tools list, the merged policy has no allowed tools
    - Otherwise, agent tools are intersected with stage allowed tools
    - Denied tools from stage policy are always preserved (deny wins)

    Args:
        stage_policy: The base stage policy
        agent_spec: Optional agent specification to merge

    Returns:
        Merged SessionPolicy
    """
    if agent_spec is None:
        return stage_policy

    # If agent has empty tools list, no tools are allowed
    if agent_spec.tools == []:
        merged_allowed_tools: list[str] = []
    else:
        # Intersect agent tools with stage allowed tools
        stage_allowed_set = set(stage_policy.allowed_tools)
        agent_tools_set = set(agent_spec.tools)
        merged_allowed_tools = list(stage_allowed_set & agent_tools_set)

    # Create merged policy with updated allowed_tools
    return replace(stage_policy, allowed_tools=merged_allowed_tools)
````

## File: app/tui/app.py
````python
"""Textual App for Brainstorm Buddy with three-pane layout."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header

from app.tui.widgets import CommandPalette, ContextPanel, FileTree, SessionViewer


class BrainstormBuddyApp(App[None]):
    """Main Textual application for Brainstorm Buddy."""

    TITLE = "Brainstorm Buddy"
    SUB_TITLE = "Terminal-first brainstorming app"

    DEFAULT_CSS = """
    Screen {
        background: $surface;
    }

    Header {
        background: $primary;
    }

    Horizontal {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding(":", "command_palette", "Command", priority=True),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app with three-pane layout."""
        yield Header()
        with Horizontal():
            yield FileTree()
            yield SessionViewer()
            yield ContextPanel()
        yield Footer()
        yield CommandPalette()

    def action_command_palette(self) -> None:
        """Show the command palette."""
        palette = self.query_one("#command-palette", CommandPalette)
        palette.show()


def main() -> None:
    """Run the Brainstorm Buddy app."""
    app = BrainstormBuddyApp()
    app.run()


if __name__ == "__main__":
    main()
````

## File: requirements-dev.txt
````
# This file was autogenerated by uv via the following command:
#    uv pip compile pyproject.toml --extra dev -o requirements-dev.txt
aiofiles==24.1.0
    # via brainstormbuddy (pyproject.toml)
aiosqlite==0.21.0
    # via brainstormbuddy (pyproject.toml)
annotated-types==0.7.0
    # via pydantic
backports-tarfile==1.2.0
    # via jaraco-context
build==1.3.0
    # via brainstormbuddy (pyproject.toml)
certifi==2025.8.3
    # via requests
cffi==1.17.1
    # via cryptography
cfgv==3.4.0
    # via pre-commit
charset-normalizer==3.4.3
    # via requests
click==8.2.1
    # via typer
coverage==7.10.4
    # via pytest-cov
cryptography==45.0.6
    # via secretstorage
distlib==0.4.0
    # via virtualenv
docutils==0.22
    # via readme-renderer
filelock==3.19.1
    # via virtualenv
id==1.5.0
    # via twine
identify==2.6.13
    # via pre-commit
idna==3.10
    # via requests
importlib-metadata==8.7.0
    # via keyring
iniconfig==2.1.0
    # via pytest
jaraco-classes==3.4.0
    # via keyring
jaraco-context==6.0.1
    # via keyring
jaraco-functools==4.3.0
    # via keyring
jeepney==0.9.0
    # via
    #   keyring
    #   secretstorage
keyring==25.6.0
    # via twine
linkify-it-py==2.0.3
    # via markdown-it-py
markdown-it-py==3.0.0
    # via
    #   brainstormbuddy (pyproject.toml)
    #   mdformat
    #   mdit-py-plugins
    #   rich
    #   textual
mdformat==0.7.22
    # via brainstormbuddy (pyproject.toml)
mdit-py-plugins==0.5.0
    # via markdown-it-py
mdurl==0.1.2
    # via markdown-it-py
more-itertools==10.7.0
    # via
    #   jaraco-classes
    #   jaraco-functools
mypy==1.17.1
    # via brainstormbuddy (pyproject.toml)
mypy-extensions==1.1.0
    # via mypy
nh3==0.3.0
    # via readme-renderer
nodeenv==1.9.1
    # via pre-commit
packaging==25.0
    # via
    #   build
    #   pytest
    #   twine
pathspec==0.12.1
    # via mypy
platformdirs==4.3.8
    # via
    #   textual
    #   virtualenv
pluggy==1.6.0
    # via
    #   pytest
    #   pytest-cov
pre-commit==4.3.0
    # via brainstormbuddy (pyproject.toml)
pycparser==2.22
    # via cffi
pydantic==2.11.7
    # via
    #   brainstormbuddy (pyproject.toml)
    #   pydantic-settings
pydantic-core==2.33.2
    # via pydantic
pydantic-settings==2.10.1
    # via brainstormbuddy (pyproject.toml)
pygments==2.19.2
    # via
    #   pytest
    #   readme-renderer
    #   rich
pyproject-hooks==1.2.0
    # via build
pytest==8.4.1
    # via
    #   brainstormbuddy (pyproject.toml)
    #   pytest-asyncio
    #   pytest-cov
pytest-asyncio==1.1.0
    # via brainstormbuddy (pyproject.toml)
pytest-cov==6.2.1
    # via brainstormbuddy (pyproject.toml)
python-dotenv==1.1.1
    # via pydantic-settings
pyyaml==6.0.2
    # via
    #   brainstormbuddy (pyproject.toml)
    #   pre-commit
readme-renderer==44.0
    # via twine
requests==2.32.5
    # via
    #   id
    #   requests-toolbelt
    #   twine
requests-toolbelt==1.0.0
    # via twine
rfc3986==2.0.0
    # via twine
rich==14.1.0
    # via
    #   textual
    #   twine
    #   typer
ruff==0.12.9
    # via brainstormbuddy (pyproject.toml)
secretstorage==3.3.3
    # via keyring
shellingham==1.5.4
    # via typer
textual==0.86.3
    # via brainstormbuddy (pyproject.toml)
twine==6.1.0
    # via brainstormbuddy (pyproject.toml)
typer==0.16.1
    # via brainstormbuddy (pyproject.toml)
types-pyyaml==6.0.12.20250809
    # via brainstormbuddy (pyproject.toml)
typing-extensions==4.14.1
    # via
    #   brainstormbuddy (pyproject.toml)
    #   aiosqlite
    #   mypy
    #   pydantic
    #   pydantic-core
    #   textual
    #   typer
    #   typing-inspection
typing-inspection==0.4.1
    # via
    #   pydantic
    #   pydantic-settings
uc-micro-py==1.0.3
    # via linkify-it-py
urllib3==2.5.0
    # via
    #   requests
    #   twine
virtualenv==20.34.0
    # via pre-commit
zipp==3.23.0
    # via importlib-metadata
````

## File: requirements.txt
````
# This file was autogenerated by uv via the following command:
#    uv pip compile pyproject.toml -o requirements.txt
aiofiles==24.1.0
    # via brainstormbuddy (pyproject.toml)
aiosqlite==0.21.0
    # via brainstormbuddy (pyproject.toml)
annotated-types==0.7.0
    # via pydantic
click==8.2.1
    # via typer
linkify-it-py==2.0.3
    # via markdown-it-py
markdown-it-py==3.0.0
    # via
    #   brainstormbuddy (pyproject.toml)
    #   mdformat
    #   mdit-py-plugins
    #   rich
    #   textual
mdformat==0.7.22
    # via brainstormbuddy (pyproject.toml)
mdit-py-plugins==0.5.0
    # via markdown-it-py
mdurl==0.1.2
    # via markdown-it-py
platformdirs==4.3.8
    # via textual
pydantic==2.11.7
    # via
    #   brainstormbuddy (pyproject.toml)
    #   pydantic-settings
pydantic-core==2.33.2
    # via pydantic
pydantic-settings==2.10.1
    # via brainstormbuddy (pyproject.toml)
pygments==2.19.2
    # via rich
python-dotenv==1.1.1
    # via pydantic-settings
pyyaml==6.0.2
    # via brainstormbuddy (pyproject.toml)
rich==14.1.0
    # via
    #   textual
    #   typer
shellingham==1.5.4
    # via typer
textual==0.86.3
    # via brainstormbuddy (pyproject.toml)
typer==0.16.1
    # via brainstormbuddy (pyproject.toml)
typing-extensions==4.14.1
    # via
    #   brainstormbuddy (pyproject.toml)
    #   aiosqlite
    #   pydantic
    #   pydantic-core
    #   textual
    #   typer
    #   typing-inspection
typing-inspection==0.4.1
    # via
    #   pydantic
    #   pydantic-settings
uc-micro-py==1.0.3
    # via linkify-it-py
````

## File: app/permissions/settings_writer.py
````python
"""Settings writer for Claude project configuration."""

import json
from pathlib import Path
from typing import Any


def write_project_settings(
    repo_root: Path = Path("."),
    config_dir_name: str = ".claude",
    import_hooks_from: str = "app.permissions.hooks_lib",
) -> Path:
    """
    Write Claude project settings with deny-first permissions and hook configuration.

    Args:
        repo_root: Root directory of the repository (default: current directory)
        config_dir_name: Name of the configuration directory (default: ".claude")
        import_hooks_from: Python module path to import hooks from (default: "app.permissions.hooks_lib")

    Returns:
        Path to the created configuration directory
    """
    repo_root = Path(repo_root)
    config_dir = repo_root / config_dir_name
    hooks_dir = config_dir / "hooks"

    # Ensure directories exist
    config_dir.mkdir(exist_ok=True)
    hooks_dir.mkdir(exist_ok=True)

    # Define settings structure
    settings: dict[str, Any] = {
        "permissions": {
            "allow": ["Read", "Edit", "Write"],
            "deny": ["Bash", "WebSearch", "WebFetch"],
            "denyPaths": [".env*", "secrets/**", ".git/**"],
            "writeRoots": ["projects/**", "exports/**"],
            "webDomains": {
                "allow": [],  # Empty list means allow all domains if web tools are enabled
                "deny": [],  # Domains to explicitly deny even if allowed
            },
        },
        "hooks": {
            "PreToolUse": f"{config_dir_name}/hooks/gate.py",
            "PostToolUse": f"{config_dir_name}/hooks/format_md.py",
        },
    }

    # Write settings.json
    settings_path = config_dir / "settings.json"
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")  # Add trailing newline

    # Create hook stub files
    _create_gate_hook(hooks_dir / "gate.py", import_hooks_from)
    _create_format_md_hook(hooks_dir / "format_md.py", import_hooks_from)

    return config_dir


def _create_gate_hook(hook_path: Path, import_hooks_from: str) -> None:
    """
    Create the PreToolUse gate hook that imports from hooks_lib.

    Args:
        hook_path: Path to the hook file
        import_hooks_from: Python module path to import hooks from
    """
    hook_content = f'''#!/usr/bin/env python3
"""Claude PreToolUse hook: validate tool use against security policies."""

from __future__ import annotations
import json
import sys

# Import validation function from the app's hooks library
from {import_hooks_from}.gate import validate_tool_use


def main() -> None:
    """Main hook entry point."""
    # stdin JSON: dict with tool_name and other tool parameters
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {{e}}", file=sys.stderr)
        sys.exit(2)

    # Validate the tool use
    allowed, reason = validate_tool_use(payload)

    if not allowed:
        # Print reason to stderr and exit with code 2 to deny
        print(f"Denied: {{reason}}", file=sys.stderr)
        sys.exit(2)

    # Allow the tool use
    sys.exit(0)


if __name__ == "__main__":
    main()
'''

    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(hook_content)

    # Make the hook executable (Python will handle this cross-platform)
    hook_path.chmod(0o755)


def _create_format_md_hook(hook_path: Path, import_hooks_from: str) -> None:
    """
    Create the PostToolUse format_md hook that imports from hooks_lib.

    Args:
        hook_path: Path to the hook file
        import_hooks_from: Python module path to import hooks from
    """
    hook_content = f'''#!/usr/bin/env python3
"""Claude PostToolUse hook: format Markdown via mdformat (pure Python)."""

from __future__ import annotations
import json
import sys
from pathlib import Path

# Import formatting function and atomic writer from the app's hooks library
from {import_hooks_from}.format_md import _format_markdown_text
from {import_hooks_from}.io import atomic_replace_text


def main() -> None:
    """Main hook entry point."""
    # stdin JSON: dict with tool_name and target_path keys
    payload = json.load(sys.stdin)
    path = Path(payload.get("target_path") or "")
    if path.suffix.lower() != ".md":
        sys.exit(0)
    # Read, format, write back atomically with durability guarantees
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    formatted = _format_markdown_text(content)
    if formatted != content:
        atomic_replace_text(path, formatted)
    sys.exit(0)


if __name__ == "__main__":
    main()
'''

    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(hook_content)

    # Make the hook executable (Python will handle this cross-platform)
    hook_path.chmod(0o755)
````

## File: README.md
````markdown
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
```

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
````

## File: app/tui/views/session.py
````python
"""Session controller for managing brainstorming sessions and Claude interactions."""

from pathlib import Path

from app.files.diff import apply_patch, compute_patch, generate_diff_preview
from app.files.markdown import extract_section_paragraph
from app.files.workstream import create_workstream_batch
from app.llm.agents import AgentSpec, load_agent_specs
from app.llm.claude_client import (
    ClaudeClient,
    Event,
    FakeClaudeClient,
    MessageDone,
    TextDelta,
)
from app.llm.sessions import get_policy, merge_agent_policy
from app.tui.widgets.kernel_approval import KernelApprovalModal
from app.tui.widgets.session_viewer import SessionViewer


class SessionController:
    """Controller for managing brainstorming sessions."""

    def __init__(self, session_viewer: SessionViewer) -> None:
        """
        Initialize the session controller.

        Args:
            session_viewer: The widget to display session output
        """
        self.viewer = session_viewer
        self.client: ClaudeClient = FakeClaudeClient()
        self.current_stage: str | None = None
        self.pending_kernel_content: str | None = None
        self.project_slug: str | None = None
        # Cache loaded agent specs
        self._agent_specs: list[AgentSpec] | None = None
        self.selected_agent: AgentSpec | None = None

    def get_available_agents(self) -> list[AgentSpec]:
        """
        Get available agent specifications.

        Returns:
            List of loaded agent specs
        """
        if self._agent_specs is None:
            self._agent_specs = load_agent_specs("app.llm.agentspecs")
        return self._agent_specs

    async def start_clarify_session(
        self, initial_prompt: str = "I want to build a better app", agent: AgentSpec | None = None
    ) -> None:
        """
        Start a clarify stage session.

        Args:
            initial_prompt: The user's initial brainstorming idea
            agent: Optional agent specification to use
        """
        self.current_stage = "clarify"
        self.selected_agent = agent

        # Get clarify policy and merge with agent if provided
        policy = get_policy("clarify")
        if agent:
            policy = merge_agent_policy(policy, agent)

        # Read system prompt
        system_prompt_content = ""
        if policy.system_prompt_path.exists():
            system_prompt_content = policy.system_prompt_path.read_text()

        # Clear viewer and show starting message
        self.viewer.clear()
        self.viewer.write("[bold cyan]Starting Clarify Session[/bold cyan]\n")
        if agent:
            self.viewer.write(f"[dim]Using agent: {agent.name}[/dim]\n")
        self.viewer.write(
            f"[dim]Allowed tools: {', '.join(policy.allowed_tools) if policy.allowed_tools else 'None'}[/dim]\n"
        )
        self.viewer.write("[dim]Generating clarifying questions...[/dim]\n\n")

        # Stream events from client
        try:
            async for event in self.client.stream(
                prompt=initial_prompt,
                system_prompt=system_prompt_content,
                allowed_tools=policy.allowed_tools,
                denied_tools=policy.denied_tools,
                permission_mode=policy.permission_mode,
            ):
                await self._handle_event(event)
        except Exception as e:
            self.viewer.write(f"\n[red]Error during session: {e}[/red]")

    async def start_kernel_session(
        self,
        project_slug: str,
        initial_idea: str = "Build a better app",
        agent: AgentSpec | None = None,
    ) -> None:
        """
        Start a kernel stage session.

        Args:
            project_slug: The project identifier/slug
            initial_idea: The user's refined brainstorming idea
            agent: Optional agent specification to use
        """
        self.current_stage = "kernel"
        self.project_slug = project_slug
        self.pending_kernel_content = ""
        self.selected_agent = agent

        # Get kernel policy and merge with agent if provided
        policy = get_policy("kernel")
        if agent:
            policy = merge_agent_policy(policy, agent)

        # Read system prompt
        system_prompt_content = ""
        if policy.system_prompt_path.exists():
            system_prompt_content = policy.system_prompt_path.read_text()

        # Clear viewer and show starting message
        self.viewer.clear()
        self.viewer.write("[bold cyan]Starting Kernel Session[/bold cyan]\n")
        self.viewer.write(f"[dim]Project: {project_slug}[/dim]\n")
        if agent:
            self.viewer.write(f"[dim]Using agent: {agent.name}[/dim]\n")
        self.viewer.write(
            f"[dim]Allowed tools: {', '.join(policy.allowed_tools) if policy.allowed_tools else 'None'}[/dim]\n"
        )
        self.viewer.write("[dim]Generating kernel document...[/dim]\n\n")

        # Stream events from client
        try:
            async for event in self.client.stream(
                prompt=initial_idea,
                system_prompt=system_prompt_content,
                allowed_tools=policy.allowed_tools,
                denied_tools=policy.denied_tools,
                permission_mode=policy.permission_mode,
            ):
                await self._handle_kernel_event(event)
        except Exception as e:
            self.viewer.write(f"\n[red]Error during session: {e}[/red]")

    async def _handle_event(self, event: Event) -> None:
        """
        Handle a stream event from the Claude client.

        Args:
            event: The event to handle
        """
        if isinstance(event, TextDelta):
            # Display text chunks as they arrive
            self.viewer.write(event.text, scroll_end=True)
        elif isinstance(event, MessageDone):
            # Session complete
            self.viewer.write(
                "\n[dim]Session complete. Consider these questions as you refine your idea.[/dim]"
            )

    async def _handle_kernel_event(self, event: Event) -> None:
        """
        Handle a stream event from the Claude client during kernel stage.

        Args:
            event: The event to handle
        """
        if isinstance(event, TextDelta):
            # Accumulate text for the kernel content
            if self.pending_kernel_content is not None:
                self.pending_kernel_content += event.text
            # Display text chunks as they arrive
            self.viewer.write(event.text, scroll_end=True)
        elif isinstance(event, MessageDone):
            # Session complete - show diff preview
            self.viewer.write("\n[dim]Kernel generation complete.[/dim]\n")
            await self._show_kernel_diff_preview()

    async def _show_kernel_diff_preview(self) -> None:
        """Show a diff preview and prompt for approval."""
        if not self.project_slug or not self.pending_kernel_content:
            self.viewer.write("[red]Error: No kernel content to preview[/red]\n")
            return

        # Construct kernel file path
        kernel_path = Path("projects") / self.project_slug / "kernel.md"

        # Read existing content if file exists
        old_content = ""
        if kernel_path.exists():
            old_content = kernel_path.read_text()

        # Generate diff preview
        diff_preview = generate_diff_preview(
            old_content,
            self.pending_kernel_content,
            context_lines=3,
            from_label=f"projects/{self.project_slug}/kernel.md (current)",
            to_label=f"projects/{self.project_slug}/kernel.md (proposed)",
        )

        # Get the app instance through the viewer
        app = self.viewer.app

        # Show modal and wait for response
        modal = KernelApprovalModal(diff_preview, self.project_slug)
        approved = await app.push_screen_wait(modal)

        if approved:
            self.approve_kernel_changes()
        else:
            self.reject_kernel_changes()

    def approve_kernel_changes(self) -> bool:
        """
        Apply the pending kernel changes atomically.

        Returns:
            True if changes were applied successfully, False otherwise
        """
        if not self.project_slug or not self.pending_kernel_content:
            self.viewer.write("[red]Error: No pending changes to apply[/red]\n")
            return False

        try:
            # Construct kernel file path
            kernel_path = Path("projects") / self.project_slug / "kernel.md"

            # Ensure parent directory exists
            kernel_path.parent.mkdir(parents=True, exist_ok=True)

            # Read existing content if file exists
            old_content = ""
            if kernel_path.exists():
                old_content = kernel_path.read_text()

            # Compute and apply patch
            patch = compute_patch(old_content, self.pending_kernel_content)
            apply_patch(kernel_path, patch)

            self.viewer.write(
                f"\n[green]✓ Kernel successfully written to projects/{self.project_slug}/kernel.md[/green]\n"
            )

            # Clear pending content
            self.pending_kernel_content = None
            return True

        except Exception as e:
            self.viewer.write(
                f"\n[red]Error applying changes: {e}[/red]\n"
                "[yellow]Original file remains unchanged.[/yellow]\n"
            )
            return False

    def reject_kernel_changes(self) -> None:
        """Reject the pending kernel changes."""
        self.viewer.write("\n[yellow]Changes rejected. Kernel file remains unchanged.[/yellow]\n")
        self.pending_kernel_content = None

    async def generate_workstreams(self, project_slug: str = "default-project") -> None:
        """
        Generate workstream documents (outline and elements) for a project.

        Args:
            project_slug: The project identifier/slug
        """
        self.project_slug = project_slug

        # Clear viewer and show starting message
        self.viewer.clear()
        self.viewer.write("[bold cyan]Generating Workstream Documents[/bold cyan]\n")
        self.viewer.write(f"[dim]Project: {project_slug}[/dim]\n\n")

        try:
            # Get project path
            project_path = Path("projects") / project_slug

            # Check if kernel exists and read it for summary
            kernel_summary = None
            kernel_path = project_path / "kernel.md"
            if kernel_path.exists():
                kernel_content = kernel_path.read_text()
                # Use robust extraction utility to get the Core Concept paragraph
                kernel_summary = extract_section_paragraph(kernel_content, "## Core Concept")

            # Create batch with all workstream documents
            self.viewer.write("[dim]Creating batch with outline and element documents...[/dim]\n")
            batch = create_workstream_batch(
                project_path, project_slug, kernel_summary=kernel_summary
            )

            if not batch:
                self.viewer.write(
                    "[yellow]No changes needed - all files are up to date.[/yellow]\n"
                )
                return

            # Generate and show preview
            self.viewer.write("\n[bold]Preview of changes:[/bold]\n")
            preview = batch.generate_preview(context_lines=2)

            # Limit preview display for readability
            preview_lines = preview.split("\n")
            if len(preview_lines) > 50:
                # Show first 40 lines and summary
                self.viewer.write("\n".join(preview_lines[:40]))
                self.viewer.write(f"\n[dim]... ({len(preview_lines) - 40} more lines) ...[/dim]\n")
            else:
                self.viewer.write(preview)

            self.viewer.write(f"\n[dim]Total files to create/update: {len(batch)}[/dim]\n")

            # Get the app instance through the viewer
            app = self.viewer.app

            # Create a simple approval modal (reuse KernelApprovalModal for now)
            # In production, we'd create a dedicated WorkstreamApprovalModal
            modal = KernelApprovalModal(preview, project_slug)
            approved = await app.push_screen_wait(modal)

            if approved:
                # Apply all changes atomically
                self.viewer.write("\n[dim]Applying changes atomically...[/dim]\n")
                patches = batch.apply()

                self.viewer.write(
                    f"\n[green]✓ Successfully created/updated {len(patches)} files:[/green]\n"
                )
                for change in batch.changes:
                    status = "created" if change.is_new_file else "updated"
                    self.viewer.write(
                        f"  • {change.path.relative_to(Path('projects'))} ({status})\n"
                    )
            else:
                self.viewer.write("\n[yellow]Changes rejected. No files were modified.[/yellow]\n")

        except Exception as e:
            self.viewer.write(f"\n[red]Error generating workstreams: {e}[/red]\n")
            self.viewer.write("[yellow]No files were modified.[/yellow]\n")
````

## File: .github/workflows/ci.yml
````yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v5

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install uv
      uses: astral-sh/setup-uv@v6
      with:
        enable-cache: true
        cache-dependency-glob: "requirements*.txt"

    - name: Install dependencies
      run: |
        uv venv
        uv pip install -r requirements-dev.txt

    - name: Run ruff linting
      run: |
        source .venv/bin/activate
        ruff check .

    - name: Run ruff formatting check
      run: |
        source .venv/bin/activate
        ruff format --check .

  type-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v5

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install uv
      uses: astral-sh/setup-uv@v6
      with:
        enable-cache: true
        cache-dependency-glob: "requirements*.txt"

    - name: Install dependencies
      run: |
        uv venv
        uv pip install -r requirements-dev.txt

    - name: Run mypy type checking
      run: |
        source .venv/bin/activate
        mypy . --strict

  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.11', '3.12']

    steps:
    - uses: actions/checkout@v5

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install uv
      uses: astral-sh/setup-uv@v6
      with:
        enable-cache: true
        cache-dependency-glob: "requirements*.txt"

    - name: Install dependencies
      run: |
        uv venv
        uv pip install -r requirements-dev.txt

    - name: Run tests with coverage
      run: |
        source .venv/bin/activate
        PYTHONPATH=$PWD pytest -q --tb=short --cov=app --cov-report=xml --cov-report=term-missing

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        flags: unittests
        name: Python-${{ matrix.python-version }}
        token: ${{ secrets.CODECOV_TOKEN }}
        fail_ci_if_error: false
        verbose: true
````

## File: app/research/db.py
````python
"""SQLite database with FTS for research findings."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

import aiosqlite


class ResearchDB:
    """Async SQLite database for research findings with FTS support."""

    def __init__(self, db_path: Path | str) -> None:
        """Initialize database with path."""
        self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self.conn: aiosqlite.Connection | None = None

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        self.conn = await aiosqlite.connect(str(self.db_path))
        await self.init_db()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def init_db(self) -> None:
        """Initialize database schema and FTS index."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        # Create schema version table for migrations
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Check current schema version
        async with self.conn.execute("SELECT MAX(version) FROM schema_version") as cursor:
            row = await cursor.fetchone()
            current_version = row[0] if row and row[0] is not None else 0

        # If no schema version exists (new database), create v2 directly
        if current_version == 0:
            # Create main findings table with CHECK constraint
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    url TEXT,
                    source_type TEXT,
                    claim TEXT,
                    evidence TEXT,
                    confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
                    tags TEXT,
                    workstream TEXT,
                    retrieved_at TEXT
                )
            """)
            # Set schema version to 2
            await self.conn.execute("""
                INSERT INTO schema_version (version) VALUES (2)
            """)
        elif current_version == 1:
            # Check if findings table exists
            async with self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='findings'"
            ) as cursor:
                table_exists = await cursor.fetchone() is not None

            if table_exists:
                # Migrate from v1 to v2: Add CHECK constraint
                # SQLite doesn't support ALTER TABLE ADD CONSTRAINT directly,
                # so we need to recreate the table

                # Check for any invalid data first
                async with self.conn.execute(
                    "SELECT COUNT(*) FROM findings WHERE confidence < 0.0 OR confidence > 1.0"
                ) as cursor:
                    invalid_row = await cursor.fetchone()
                    invalid_count = invalid_row[0] if invalid_row else 0

                if invalid_count > 0:
                    # Fix invalid data by clamping to valid range
                    await self.conn.execute("""
                        UPDATE findings
                        SET confidence = MAX(0.0, MIN(1.0, confidence))
                        WHERE confidence < 0.0 OR confidence > 1.0
                    """)

                # Create new table with constraint
                await self.conn.execute("""
                    CREATE TABLE findings_v2 (
                        id TEXT PRIMARY KEY,
                        url TEXT,
                        source_type TEXT,
                        claim TEXT,
                        evidence TEXT,
                        confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
                        tags TEXT,
                        workstream TEXT,
                        retrieved_at TEXT
                    )
                """)

                # Copy data from old table to new
                await self.conn.execute("""
                    INSERT INTO findings_v2
                    SELECT id, url, source_type, claim, evidence,
                           confidence, tags, workstream, retrieved_at
                    FROM findings
                """)

                # Drop old table and rename new one
                await self.conn.execute("DROP TABLE findings")
                await self.conn.execute("ALTER TABLE findings_v2 RENAME TO findings")

                # Update schema version to 2
                await self.conn.execute("""
                    INSERT INTO schema_version (version) VALUES (2)
                """)
            else:
                # No findings table yet, create with constraint
                await self.conn.execute("""
                    CREATE TABLE findings (
                        id TEXT PRIMARY KEY,
                        url TEXT,
                        source_type TEXT,
                        claim TEXT,
                        evidence TEXT,
                        confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
                        tags TEXT,
                        workstream TEXT,
                        retrieved_at TEXT
                    )
                """)
                # Update schema version to 2
                await self.conn.execute("""
                    INSERT INTO schema_version (version) VALUES (2)
                """)
        else:
            # For v2 or higher, just ensure table exists (idempotent)
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    url TEXT,
                    source_type TEXT,
                    claim TEXT,
                    evidence TEXT,
                    confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
                    tags TEXT,
                    workstream TEXT,
                    retrieved_at TEXT
                )
            """)

        # Create indexes for better query performance
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_workstream ON findings(workstream)
        """)
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_type ON findings(source_type)
        """)
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_confidence ON findings(confidence)
        """)
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_retrieved_at ON findings(retrieved_at)
        """)

        # Create FTS5 virtual table for full-text search
        # Note: We don't use content=findings because it causes FTS5 to read
        # directly from the findings table, bypassing our trigger updates
        await self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS findings_fts USING fts5(
                id UNINDEXED,
                claim,
                evidence
            )
        """)

        # Create triggers to keep FTS in sync
        # Drop old triggers first to ensure clean state
        await self.conn.execute("DROP TRIGGER IF EXISTS findings_ai")
        await self.conn.execute("DROP TRIGGER IF EXISTS findings_ad")
        await self.conn.execute("DROP TRIGGER IF EXISTS findings_au")

        await self.conn.execute("""
            CREATE TRIGGER findings_ai
            AFTER INSERT ON findings BEGIN
                INSERT INTO findings_fts(id, claim, evidence)
                VALUES (new.id, new.claim, new.evidence);
            END
        """)

        await self.conn.execute("""
            CREATE TRIGGER findings_ad
            AFTER DELETE ON findings BEGIN
                DELETE FROM findings_fts WHERE id = old.id;
            END
        """)

        await self.conn.execute("""
            CREATE TRIGGER findings_au
            AFTER UPDATE ON findings BEGIN
                DELETE FROM findings_fts WHERE id = old.id;
                INSERT INTO findings_fts(id, claim, evidence)
                VALUES (new.id, new.claim, new.evidence);
            END
        """)

        await self.conn.commit()

    async def insert_finding(
        self,
        url: str,
        source_type: str,
        claim: str,
        evidence: str,
        confidence: float,
        tags: list[str] | None = None,
        workstream: str | None = None,
    ) -> str:
        """Insert a new finding and return its ID."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        finding_id = str(uuid.uuid4())
        tags_json = json.dumps(tags or [])
        retrieved_at = datetime.now(UTC).isoformat()

        await self.conn.execute(
            """
            INSERT INTO findings (id, url, source_type, claim, evidence,
                                confidence, tags, workstream, retrieved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                finding_id,
                url,
                source_type,
                claim,
                evidence,
                confidence,
                tags_json,
                workstream,
                retrieved_at,
            ),
        )
        await self.conn.commit()
        return finding_id

    async def update_finding(
        self,
        finding_id: str,
        url: str | None = None,
        source_type: str | None = None,
        claim: str | None = None,
        evidence: str | None = None,
        confidence: float | None = None,
        tags: list[str] | None = None,
        workstream: str | None = None,
    ) -> bool:
        """Update an existing finding. Returns True if found and updated."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        # Get current values
        async with self.conn.execute(
            "SELECT * FROM findings WHERE id = ?", (finding_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False

        # Build update query dynamically
        updates = []
        params: list[Any] = []

        if url is not None:
            updates.append("url = ?")
            params.append(url)
        if source_type is not None:
            updates.append("source_type = ?")
            params.append(source_type)
        if claim is not None:
            updates.append("claim = ?")
            params.append(claim)
        if evidence is not None:
            updates.append("evidence = ?")
            params.append(evidence)
        if confidence is not None:
            updates.append("confidence = ?")
            params.append(confidence)
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags))
        if workstream is not None:
            updates.append("workstream = ?")
            params.append(workstream)

        if not updates:
            return True  # Nothing to update

        params.append(finding_id)
        query = f"UPDATE findings SET {', '.join(updates)} WHERE id = ?"  # nosec B608

        await self.conn.execute(query, params)
        await self.conn.commit()
        return True

    async def delete_finding(self, finding_id: str) -> bool:
        """Delete a finding. Returns True if found and deleted."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute("DELETE FROM findings WHERE id = ?", (finding_id,))
        await self.conn.commit()
        return cursor.rowcount > 0

    async def get_finding(self, finding_id: str) -> dict[str, Any] | None:
        """Get a finding by ID."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        async with self.conn.execute(
            "SELECT * FROM findings WHERE id = ?", (finding_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "url": row[1],
                "source_type": row[2],
                "claim": row[3],
                "evidence": row[4],
                "confidence": row[5],
                "tags": json.loads(row[6]) if row[6] else [],
                "workstream": row[7],
                "retrieved_at": row[8],
            }

    async def search_fts(
        self,
        query: str,
        workstream: str | None = None,
        source_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Search findings using full-text search on claim and evidence.

        Returns results with rank (bm25 score) where lower values indicate better matches.
        Optional filters for workstream and source_type can be applied.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        # Build WHERE clause with optional filters
        conditions = ["findings_fts MATCH ?"]
        params: list[Any] = [query]

        if workstream:
            conditions.append("f.workstream = ?")
            params.append(workstream)
        if source_type:
            conditions.append("f.source_type = ?")
            params.append(source_type)

        where_clause = " AND ".join(conditions)
        params.append(limit)

        results = []
        async with self.conn.execute(
            f"""
            SELECT f.id, f.url, f.source_type, f.claim, f.evidence,
                   f.confidence, f.tags, f.workstream, f.retrieved_at,
                   bm25(findings_fts) AS rank
            FROM findings_fts fts
            JOIN findings f ON fts.id = f.id
            WHERE {where_clause}
            ORDER BY bm25(findings_fts)
            LIMIT ?
            """,  # nosec B608
            params,
        ) as cursor:
            async for row in cursor:
                results.append(
                    {
                        "id": row[0],
                        "url": row[1],
                        "source_type": row[2],
                        "claim": row[3],
                        "evidence": row[4],
                        "confidence": row[5],
                        "tags": json.loads(row[6]) if row[6] else [],
                        "workstream": row[7],
                        "retrieved_at": row[8],
                        "rank": row[9],
                    }
                )

        return results

    async def list_findings(
        self,
        workstream: str | None = None,
        source_type: str | None = None,
        min_confidence: float | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List findings with optional filters."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        conditions = []
        params: list[Any] = []

        if workstream:
            conditions.append("workstream = ?")
            params.append(workstream)
        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)
        if min_confidence is not None:
            conditions.append("confidence >= ?")
            params.append(min_confidence)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        query = f"""
            SELECT * FROM findings
            {where_clause}
            ORDER BY retrieved_at DESC
            LIMIT ?
        """  # nosec B608

        results = []
        async with self.conn.execute(query, params) as cursor:
            async for row in cursor:
                results.append(
                    {
                        "id": row[0],
                        "url": row[1],
                        "source_type": row[2],
                        "claim": row[3],
                        "evidence": row[4],
                        "confidence": row[5],
                        "tags": json.loads(row[6]) if row[6] else [],
                        "workstream": row[7],
                        "retrieved_at": row[8],
                    }
                )

        return results
````

## File: app/tui/widgets/command_palette.py
````python
"""Command palette widget for executing app commands."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, OptionList


class CommandPalette(Container):
    """Command palette overlay for executing commands."""

    DEFAULT_CSS = """
    CommandPalette {
        layer: modal;
        align: center middle;
        width: 60;
        height: auto;
        max-height: 20;
        background: $panel;
        border: thick $primary;
        padding: 1;
        display: none;
    }

    CommandPalette.visible {
        display: block;
    }

    CommandPalette Input {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close palette"),
    ]

    def __init__(self) -> None:
        """Initialize the command palette."""
        super().__init__(id="command-palette")
        self.commands = [
            ("new project", "Create a new brainstorming project"),
            ("clarify", "Enter clarify stage for current project"),
            ("kernel", "Define the kernel of your idea"),
            ("outline", "Create workstream outline"),
            ("generate workstreams", "Generate outline and element documents"),
            ("research import", "Import research findings"),
            ("synthesis", "Synthesize findings into final output"),
            ("export", "Export project to various formats"),
            ("domain settings", "Configure web domain allow/deny lists"),
        ]

    def compose(self) -> ComposeResult:
        """Compose the command palette UI."""
        yield Input(placeholder="Type a command...", id="command-input")
        options = [f"{cmd}: {desc}" for cmd, desc in self.commands]
        yield OptionList(*options, id="command-list")

    def show(self) -> None:
        """Show the command palette."""
        self.add_class("visible")
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

    def hide(self) -> None:
        """Hide the command palette."""
        self.remove_class("visible")

    def action_close(self) -> None:
        """Close the command palette."""
        self.hide()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        command = event.value.lower().strip()
        # Run the async command execution
        self.app.run_worker(self.execute_command(command))
        self.hide()

    async def execute_command(self, command: str) -> None:
        """Execute the selected command."""
        from textual import log

        log(f"Executing command: {command}")

        # Import here to avoid circular imports
        from app.llm.sessions import get_policy
        from app.tui.views.session import SessionController
        from app.tui.widgets.agent_selector import AgentSelector
        from app.tui.widgets.session_viewer import SessionViewer

        # Get the session viewer from the main screen
        viewer = self.app.query_one("#session-viewer", SessionViewer)

        # Create controller
        controller = SessionController(viewer)

        # Handle clarify command
        if command == "clarify":
            # Get stage policy for tool info
            policy = get_policy("clarify")

            # Show agent selector
            agents = controller.get_available_agents()
            selector = AgentSelector(agents, policy.allowed_tools, policy.denied_tools)
            selected_agent = await self.app.push_screen_wait(selector)

            # Run the async task using Textual's worker system
            self.app.run_worker(
                controller.start_clarify_session(agent=selected_agent), exclusive=True
            )

        # Handle kernel command
        elif command == "kernel":
            # For now, use a default project slug - in production, this would prompt for it
            project_slug = "default-project"
            initial_idea = "Build a better brainstorming app"

            # Get stage policy for tool info
            policy = get_policy("kernel")

            # Show agent selector
            agents = controller.get_available_agents()
            selector = AgentSelector(agents, policy.allowed_tools, policy.denied_tools)
            selected_agent = await self.app.push_screen_wait(selector)

            # Run the async task using Textual's worker system
            self.app.run_worker(
                controller.start_kernel_session(project_slug, initial_idea, agent=selected_agent),
                exclusive=True,
            )

        # Handle generate workstreams command
        elif command == "generate workstreams":
            # Run the async task using Textual's worker system
            self.app.run_worker(controller.generate_workstreams(), exclusive=True)

        # Handle domain settings command
        elif command == "domain settings":
            from pathlib import Path

            from app.tui.widgets.domain_editor import DomainEditor

            # Get current settings if they exist
            config_dir = Path(".") / ".claude"
            allow_domains = []
            deny_domains = []

            # Try to load existing settings
            settings_path = config_dir / "settings.json"
            if settings_path.exists():
                import json

                with open(settings_path, encoding="utf-8") as f:
                    settings = json.load(f)
                    if "permissions" in settings and "webDomains" in settings["permissions"]:
                        allow_domains = settings["permissions"]["webDomains"].get("allow", [])
                        deny_domains = settings["permissions"]["webDomains"].get("deny", [])

            # Show domain editor
            editor = DomainEditor(config_dir, allow_domains, deny_domains)
            await self.app.push_screen_wait(editor)

        # Handle research import command
        elif command == "research import":
            from pathlib import Path

            from app.tui.views.research import ResearchImportModal

            # Determine project path and workstream
            # For now, use default project - in production, this would be context-aware
            project_path = Path("projects") / "default"
            project_path.mkdir(parents=True, exist_ok=True)
            db_path = project_path / "research.db"

            # Show research import modal
            modal = ResearchImportModal(workstream="research", db_path=db_path)
            await self.app.push_screen_wait(modal)
````

## File: pyproject.toml
````toml
[project]
name = "brainstormbuddy"
version = "0.1.0"
description = "Python terminal-first brainstorming app using Claude Code"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "textual>=0.86.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.0",
    "PyYAML>=6.0",
    "aiofiles>=24.1.0",
    "markdown-it-py>=3.0.0",
    "mdformat>=0.7.17",
    "aiosqlite>=0.21.0",
    "typing-extensions>=4.12.0",
    "typer>=0.12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.12.9",
    "mypy>=1.13.0",
    "pre-commit>=4.3.0",
    "types-PyYAML>=6.0",
    "build>=1.0.0",
    "twine>=5.0.0",
]


[tool.ruff]
line-length = 100
target-version = "py311"

# Exclude common directories
exclude = [
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".venv",
    "venv",
]

[tool.ruff.lint]
# Enable select rules
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ARG",  # flake8-unused-arguments
    "SIM",  # flake8-simplify
]

ignore = [
    "E501",  # line too long - handled by formatter
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false

[tool.mypy]
python_version = "3.11"
strict = true

# Additional strict options (all enabled by strict=true, but explicit for clarity)
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
check_untyped_defs = true
no_implicit_reexport = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true

# Ignore missing imports for third-party packages without stubs
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-ra",
    "--strict-markers",
    "--ignore=docs",
    "--ignore=.git",
    "--tb=short",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "asyncio: marks tests as async tests",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning",
]

[tool.setuptools]
packages = ["app"]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
````
