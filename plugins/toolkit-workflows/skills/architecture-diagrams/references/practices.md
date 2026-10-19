# Architecture practices

Reviewed: 2026-10-18. C4 is a tool-independent modeling convention, not an ISO or OMG standard.

- Pick context, container, or component scope; use consistent abstraction in a view.
- Include names, responsibilities, and element types. Add technology where relevant to the level.
- Give relationships direction and intent; identify protocols where they matter.
- State scope in the title and explain notation in a legend.
- For before/after comparisons, retain stable names and identify the changed boundary or relationship.

These summarize the [C4 review checklist](https://c4model.com/diagrams/checklist).
[C4 diagram guidance](https://c4model.com/diagrams) recommends using only levels that add value;
context and container views suffice for many teams. A C4 container is a running application or data
store, not necessarily a Docker container: [container definition](https://c4model.com/abstractions/container).

## Choosing a representation

For a small view, use basic flowchart syntax with explicit types and responsibilities. For a model
with several related views, [Structurizr DSL](https://docs.structurizr.com/dsl) defines elements and
relationships once. Consult current docs for its installation, validation, and exports; it is
optional and has no bundled runtime. [Mermaid C4](https://mermaid.js.org/syntax/c4.html) is explicitly
experimental, so verify its limitations before selecting it for maintained documentation.

## Example and domain checks

Use [the container example](../assets/containers.mmd) as a proposal template. Its API and database
are separate containers; the customer is outside the system boundary. Replace names and claimed
technologies with evidence. Do not insert classes into this container view or claim that an HTTPS
arrow proves authentication. Explain what each arrow means and inspect whether system ownership
and external dependencies are clear.

Example legend: type labels identify C4 roles, the enclosing box marks the system boundary, the
cylinder denotes a data store, and arrows name interactions and protocols from caller to dependency.
