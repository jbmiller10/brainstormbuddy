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
        include_elements = ["requirements", "research", "design", "implementation", "synthesis"]

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
