---
name: engineering-visuals
description: Route engineering visual requests to specialist skills for behavior diagrams, C4 architecture, dependency graphs, or editable draw.io diagrams. Use proactively when a visual materially clarifies development work.
---

# Engineering visuals

Select a specialist before implementing each visual. Keep straightforward explanations concise;
use a visual when it answers a structural or behavioral question better than prose alone.

| Request | Lead specialist |
| --- | --- |
| Flow, API sequence, state machine, or data model | [engineering-diagrams](../engineering-diagrams/SKILL.md) |
| System context, containers, components, or before/after architecture | [architecture-diagrams](../architecture-diagrams/SKILL.md) |
| Imports, packages, build dependencies, or module coupling | [dependency-graphs](../dependency-graphs/SKILL.md) |
| Explicit draw.io deliverable or layout intended for manual editing | [editable-diagrams](../editable-diagrams/SKILL.md) |

Read and follow the selected specialist, including its standards reference, rather than stopping
at this routing table. For architecture or dependencies in draw.io, lead with editable-diagrams
and read the appropriate domain specialist's standards. For a mixed request, route each distinct
visual separately; each has one lead specialist.

The specialist owns notation and correctness; the renderer is an implementation choice. A request
for a Mermaid architecture diagram still belongs to architecture-diagrams. Respect explicit format
choices and existing project conventions. Simulations, UI wireframes, and general graphic design
are outside this workflow; use an available relevant skill or explain that boundary.

All specialists share [delivery and evidence rules](references/standards.md). Their relative links
require the toolkit-workflows skill set to be installed together, as profile skill sync does.
