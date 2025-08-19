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
