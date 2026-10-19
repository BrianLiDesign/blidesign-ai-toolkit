# Engineering visuals design

Status: implemented locally following confirmation of shared understanding.

Tracked in [issue 8](https://github.com/BrianLiDesign/blidesign-ai-toolkit/issues/8).

## Agreed scope

- Cover architecture, API sequences, data models, state machines, dependencies, and before/after
  designs in the first release.
- Defer interactive explanations, simulations, and UI wireframes.
- Select tools with maintained upstreams, clear licensing, documented formats, editable source,
  local rendering, and repeatable validation.
- Use Mermaid by default, with Graphviz and draw.io available for specific needs. Use C4 conventions
  for architecture. Add other renderers when a concrete requirement justifies them.
- Respond to explicit visual requests and proactively use diagrams when they materially clarify
  complex flows, architectural decisions, or proposed changes. Keep straightforward tasks concise.

## Delivery

Render quick explanations inline when the host supports them. For maintained documentation, follow
the project's existing conventions; otherwise save editable source under `docs/diagrams/`, with
exports when needed.

## Dependencies

Keep skill installation lightweight. Install pinned rendering dependencies locally when needed;
Graphviz and draw.io remain optional. If rendering is unavailable, provide editable source and
report that the result remains unverified.

## Validation

Before calling a diagram validated:

1. Check its relationships against the relevant code or specifications.
2. Render it successfully.
3. Inspect the result for clipped labels, unreadable text, and confusing arrows.

Distinguish existing behavior, proposed behavior, and assumptions.

## Packaging

Add an `engineering-visuals` router skill to the existing `toolkit-workflows` plugin. The router
selects and invokes the relevant specialist skill before visual implementation; it does not carry
all authoring instructions itself. Direct requests to a specialist skill remain supported.

Agreed specialist boundaries:

| Specialist skill | Responsibility |
| --- | --- |
| `engineering-diagrams` | Flow, sequence, state, and entity-relationship diagrams, using Mermaid by default. |
| `architecture-diagrams` | C4 architecture views, system boundaries, responsibilities, and existing/proposed designs. |
| `dependency-graphs` | Evidence-backed dependency graphs, using Graphviz when appropriate. |
| `editable-diagrams` | Diagrams requiring manual layout and ongoing editing in draw.io. |

Route architecture and dependency requests by their engineering purpose first. Route requests with
an explicit requirement for manual layout or draw.io deliverables to `editable-diagrams`, retaining
the relevant architecture or dependency standards. Each output has one lead specialist; reference
shared guidance rather than duplicating it across skills.

## Specialist standards and research

Each specialist skill must have standards and researched practices in place before use:

- Research authoritative primary sources during implementation and record source links, review
  dates, and relevant tool versions or compatibility limits.
- Distinguish formal standards, established conventions, and toolkit recommendations.
- Define supported requests, notation and abstraction rules, source-of-truth requirements,
  editable deliverables, and rendering and visual inspection criteria.
- Include usable examples and checks for common failures specific to its visual type.
- Refresh version-sensitive documentation when a request depends on changed syntax or behavior.
- Apply shared requirements for provenance, accessibility, local rendering, and validation through
  a single referenced source, with specialist additions where necessary.

Connect relevant engineering flows to the router through the existing toolkit overlay mechanism.
Interactive explanations, simulations, and UI wireframes remain outside the first release.

## Implementation boundary

Implement the confirmed scope in toolkit-workflows and reproducible owned overlays. Rendering
dependencies remain optional external tools; installation of the skill does not install them.
Local verification does not establish publication or installation in the user's agent hosts.

## Local verification

Verified on Windows against the working tree based on `dc6fb3b`:

- Repository verifier and 56 unit tests passed; one POSIX-only test was skipped.
- All five new skill entrypoints passed the skill-creator validator.
- PowerShell and Git Bash bootstrap dry runs passed for minimal, development, and full profiles.
- Development skill-sync dry run selected 50 skills; a real sync into an isolated temporary directory
  retained all specialist references and assets.
- Mermaid CLI 12.0.0 with Mermaid 12.2.0 and installed Chrome rendered flow, sequence, state, ER, and
  architecture examples. PNG examples were visually inspected; SVG and PDF exports also succeeded.
- Rendering tests covered missing tools, timeouts and child cleanup, literal paths, shell-wrapper
  rejection, invalid output, and preservation of sources and previous exports on failure.
- The draw.io example passed XML identity, geometry, and connector checks. Native Graphviz rendering
  and draw.io export/edit/reopen were unavailable because those optional applications are absent.
- The optional Mermaid runtime audit reported two low-severity findings, no moderate/high/critical
  findings; details and the advisory are recorded in the rendering reference. Runtime dependencies
  and their locks remain outside the repository.

The full Codex plugin validator, local CodeQL, and local Gitleaks were unavailable. Repository
verification checked manifest consistency and provenance; hosted security and cross-OS CI have not
run for these local changes. Existing upstream commit pins and license files are preserved.

## Primary references

- [GitHub Mermaid support](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
- [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)
- [Graphviz documentation](https://graphviz.org/documentation/)
- [draw.io](https://www.drawio.com/)
- [C4 diagrams](https://c4model.com/diagrams)
- [Structurizr DSL](https://docs.structurizr.com/dsl)

Mermaid's C4 syntax is documented as experimental. Treat C4 as the architecture convention rather
than assuming Mermaid's C4 renderer is suitable for every maintained architecture model:
[Mermaid C4 documentation](https://mermaid.js.org/syntax/c4.html).
