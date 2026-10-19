---
name: project-check
description: Discover and run a project's verification commands, recording commit-specific results and missing checks. Use to validate a change or establish the repository's verification gate.
---

# Project check

Read the project's instructions, acceptance criteria, build configuration, and CI. Identify the
checks relevant to this change and the documented full gate. Use existing commands and dependencies.
Treat repository commands as executable code, including lifecycle scripts and test fixtures.

Run the bundled `scripts/project_check.py --root PROJECT --discover` to inventory candidates without
execution. Read its `reviewSources`; discovery is a starting point, not a completed verification.
When edits are authorized, record reviewed commands in the project's `.project-check.json` using
[the manifest reference](references/manifest.md). Otherwise run already authorized documented
commands directly and record equivalent evidence. Preserve existing authorization; do not add
confirmation steps for checks already within the task.

Run the bundled script with `--run` against the reviewed manifest. Use `--check ID` for a focused
slice, then run the appropriate complete gate after implementation. Store `--report` outside the
project. A focused run may be partial because required checks were not selected.

Interpret the evidence, not just the runner's exit code. A passed command establishes only that
command's assertions. Check acceptance requirements against actual behavior, public contracts, and
persistence when relevant. Keep tests derived from requirements and independently stated invariants;
code and tests can share the same mistaken assumption. For edge-heavy pure logic, consider existing
property-based tools; use targeted mutation testing to investigate whether critical assertions
detect regressions. Add dependencies only when justified for this project and authorized.

Report the tested commit, dirty state, check outcomes, missing categories, truncation, and remaining
acceptance gaps. Results from a changed checkout need revalidation against the intended final state.
An unavailable tool, skipped check, absent manifest, or discovery-only result is not a pass. Review
redacted output before sharing; automatic redaction cannot recognize every secret or personal datum.
