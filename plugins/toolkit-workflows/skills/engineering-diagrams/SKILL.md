---
name: engineering-diagrams
description: Create or revise software flowcharts, API sequence diagrams, state machines, and entity-relationship diagrams using Mermaid by default, with notation-specific checks and editable source.
---

# Engineering diagrams

Read [shared standards](../engineering-visuals/references/standards.md) and the relevant notation in
[diagram practices](references/practices.md) before authoring. For architecture or dependency
analysis, use that specialist even when the requested output is Mermaid.

Choose the representation from the question: flowchart for decisions and branching, sequence for
ordered interactions, state diagram for lifecycle transitions, ER for entities and cardinality.
Use repository terminology and trace important edges to evidence. Include meaningful failure paths
when they affect the explanation. Save maintained Mermaid source as `.mmd` without Markdown fences.

Render with the shared helper using the local Mermaid CLI and inspect the result at its intended
size. Match the destination's supported syntax; prefer established diagram types over experimental
features. Complete the shared evidence checks before describing the result as validated.
