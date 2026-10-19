# Shared visual standards

Reviewed: 2026-10-18. These are toolkit requirements unless identified as external guidance.

## Evidence and delivery

Identify audience, question, scope, and whether the visual represents existing or proposed behavior.
Read relevant code or specifications. Retain a short evidence note mapping important relationships
to file paths, symbols, contracts, or specification sections; record the commit and dirty state for
repository-derived diagrams. Label assumptions and unresolved relationships rather than inventing
them. Proposed designs reference their requirements instead of claiming to describe running code.

For quick explanations, use inline diagrams if supported. For maintained documentation, follow
project conventions or use `docs/diagrams/`. Preserve editable `.mmd`, `.dot`, `.drawio`, or `.dsl`
source alongside needed exports. Keep temporary renders outside source control. In before/after
comparisons, preserve identifiers, abstraction, and legend; name the change explicitly.

Separate three results: **source checked**, **rendered**, and **visually inspected**. Call a visual
validated only when its domain checks, rendering, and visual inspection all pass. A nonempty image
or successful command alone does not establish correctness. If tooling is unavailable, deliver
editable source with the missing check stated. Do not claim validation of unrendered inline source.

## Readability and accessibility

Give the visual a title and scope, label relationship direction, and explain non-obvious notation.
Keep text readable at the intended display size; inspect cropped labels, overlapping edges, and
contrast. Split dense views by question or abstraction rather than shrinking everything.
Provide a concise text equivalent describing the important relationships. Use labels or line
styles alongside color. Mermaid supports `accTitle` and `accDescr`; an image embed also needs
appropriate alternative text in its destination.

W3C's [complex-image guidance](https://www.w3.org/WAI/tutorials/images/complex/) supports a short
alternative plus a fuller text explanation when needed. This checklist is not a claim of complete
WCAG conformance. [Mermaid accessibility](https://mermaid.js.org/config/accessibility.html) documents
its title and description syntax.

## Tooling and compatibility

Use reviewed local executables and configuration. Rendering is not a sandbox: inspect imported
links, includes, scripts, images, fonts, and other external resources before execution. Keep private
source local. Avoid remote assets for reproducible/offline output. Install exact renderer versions
in a project-approved tool directory, retain its dependency lock, and record versions and relevant
configuration. Skill installation itself installs no rendering runtime or account integration.

Use [rendering instructions](rendering.md) for the bundled helper and dependency setup. Refresh
version-sensitive official documentation through find-docs/Context7 when available; otherwise use
the maintainer's documentation and identify uncertainty. A target host may run an older renderer:
GitHub documents checking its Mermaid version with an `info` diagram. Local success does not prove
GitHub compatibility. See [GitHub diagram support](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams).

Tool syntax is not a formal modeling standard. C4 is an established architecture convention;
Mermaid's notation, DOT, and draw.io XML are tool formats. For formal UML conformance, consult the
applicable OMG specification and use a suitable UML workflow rather than labeling Mermaid as
standards-compliant UML. [OMG UML](https://www.omg.org/spec/UML/).

## Completion evidence

Report source and export locations, lead specialist, renderer/version, domain-check outcome,
render command/result, visual-inspection outcome, and any remaining assumption or unavailable
check. A brief chat note is sufficient for temporary explanations; maintained visuals should keep
the evidence with their documentation. Do not label documentation research as runtime testing.
