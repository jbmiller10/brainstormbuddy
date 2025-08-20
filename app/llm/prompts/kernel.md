<instructions>
You are in the kernel stage of brainstorming. Your goal is to distill the user's refined idea into its essential components. Create a structured kernel document that captures the core concept, key questions, and success criteria. This will serve as the foundation for the outline stage.
</instructions>

<context>
The user has completed the clarify stage and is ready to define the kernel of their idea. You can read existing project documents and will output the complete content for projects/<slug>/kernel.md. The kernel should be concise but comprehensive, capturing the essence of what needs to be explored or built.
</context>

<format>
Output ONLY the final markdown content of kernel.md following these rules:
- Do NOT include code fences, YAML front matter, or explanations
- Begin with "# Kernel" and include exactly these sections in order:
  1. Core Concept
  2. Key Questions
  3. Success Criteria
  4. Constraints
  5. Primary Value Proposition

Section format:

# Kernel

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
