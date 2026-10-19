---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: false
---

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Call the Skill tool with "tdd" where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, call the Skill tool with "code-review" to review the work.

Commit your work to the current branch.

<!-- blidesign-toolkit-overlay:start -->
## Toolkit engineering visuals

When an engineering visual materially clarifies the work, use engineering-visuals when available.
Read and follow its selected specialist before implementing each diagram; use its domain standards,
primary-source references, editable deliverables, and rendering/inspection checks. Preserve the
agreed task scope and distinguish existing behavior from proposed designs.
<!-- blidesign-toolkit-overlay:end -->
