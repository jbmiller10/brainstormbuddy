<instructions>
You are synthesizing a complete conversation transcript from the onboarding phase into a structured kernel document. The transcript contains the user's initial braindump, summaries, clarifying questions, and the user's detailed answers. Your task is to distill all of this into the essential kernel that will guide the project forward.
</instructions>

<context>
The conversation transcript includes:
1. The user's original braindump
2. Summary and any refinements
3. Clarifying questions you asked
4. The user's answers and additional context
5. Any other discussion about the project

Analyze the entire conversation to extract the core essence of what the user wants to achieve.
</context>

<format>
Output ONLY the final markdown content following these rules:
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
A clear, 2-3 sentence description of the essential idea or problem based on the full conversation.

## Key Questions
3-5 fundamental questions that emerged from the conversation that must be answered for success.

## Success Criteria
3-5 measurable outcomes that define success, derived from the user's goals and answers.

## Constraints
Key limitations or boundaries identified during the conversation.

## Primary Value Proposition
One paragraph describing the main value or impact, synthesized from the entire discussion.

Keep the entire kernel under 250 words. Be specific and concrete based on what was discussed.
</format>
