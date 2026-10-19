---
name: editable-diagrams
description: Create or revise editable draw.io diagrams when manual layout or a .drawio deliverable is required, preserving object identities and validating both the source and exported view.
---

# Editable diagrams

Read [shared standards](../engineering-visuals/references/standards.md) and
[editing practices](references/practices.md) before authoring. For architecture, also apply
[architecture standards](../architecture-diagrams/references/practices.md); for dependency views,
apply [dependency standards](../dependency-graphs/references/practices.md). For flow, sequence,
state, or ER semantics, consult [engineering diagram practices](../engineering-diagrams/references/practices.md).

Inspect existing pages, layers, object IDs, and connectors before modifying a diagram. Preserve
unrelated content and stable identities. For new diagrams, start from the uncompressed example
and use native editable shapes and connectors. An imported flattened image does not satisfy a
request for editable diagram elements.

Keep `.drawio` as the authoritative deliverable. Verify XML structure and connector endpoints, then
open in a compatible editor or export with the local desktop app and inspect the image. For edits,
verify that pages and labels still round-trip in draw.io. Report source checks and visual checks
separately when the editor or exporter is unavailable. Complete the shared evidence checks.
