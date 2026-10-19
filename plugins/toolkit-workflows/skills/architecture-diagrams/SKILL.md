---
name: architecture-diagrams
description: Explain or propose software architecture using C4 context, container, and component views, including system boundaries and before/after designs. Applies regardless of the chosen renderer.
---

# Architecture diagrams

Read [shared standards](../engineering-visuals/references/standards.md) and
[architecture practices](references/practices.md) before authoring.

Choose the audience and C4 level first. Start with context or containers; introduce a component view
only when it answers a concrete question. Inspect code, deployment definitions, and contracts for
existing architecture; identify the requirement and assumptions for proposals. Keep each view at a
consistent abstraction and apply the C4 review checklist.

Use a labeled Mermaid flowchart for a small standalone architecture view. Use Structurizr DSL when
a maintained model needs multiple consistent views, following current official DSL documentation
and the project's tool setup. Treat Mermaid C4 syntax as experimental. A Mermaid flowchart following
C4 conventions is not the experimental C4 syntax or a formal UML model.

For explicit draw.io/manual editing, let editable-diagrams lead implementation and supply these
architecture standards. For Mermaid output, use the shared rendering helper; for Structurizr,
validate and export with the project's pinned tool and record that evidence separately. Inspect
the final view and complete shared evidence checks.
