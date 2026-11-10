# Orchestration acceptance scenarios

Use a disposable local Git repository outside the toolkit checkout. Record the host/version or
session identity, skill source/version, base and result commits, assignments, native worker IDs,
checks, and preserved artifacts in a user-local evidence directory. Do not publish test issues.

| Scenario | Observable acceptance |
| --- | --- |
| Parallel research/review | Two native workers answer independent questions against a fixed base; no source changes; coordinator checks and combines both results. |
| Parallel implementation | Two workers edit separate files in distinct worktrees/branches based on the integration SHA; coordinator inspects diffs, integrates serially, and runs combined checks. |
| Dependency ordering | A dependent task starts only after its prerequisite is integrated, using the new integration tip. |
| Existing edits | An unrelated dirty file in the original checkout retains identical bytes through integration and cleanup. |
| Missing capabilities | With native delegation or safe isolation unavailable, the workflow reports sequential execution and produces no invented worker IDs. |
| Worker failure | A deliberately unavailable input yields a blocked/partial handoff; no dependent work starts and no incomplete task is reported as complete. |
| Corrective retry | Coordinator supplies a concrete correction, retries once, and preserves work and reports a blocker if that attempt also fails. |
| Cleanup | Stopped, clean, integrated owned worktrees may be removed; dirty or unintegrated work survives. |
| Combined verification | A check requiring both contributions passes on the integration tip; worker-only passes are insufficient. |

Use real native workers for the first two scenarios. For fallback and retry policy, a constrained
evaluation or tabletop walkthrough is useful but must be labeled as such, not a live host failure.
Inspect observable state before and after; avoid grading solely by matching instruction wording.

Report each host as live verified, documentation checked, unavailable, or failed, with the actual
scenario coverage. File sync and syntactically valid custom-agent examples do not establish that a
host discovered or executed the skill. Claude Code and Cursor live runs may be deferred explicitly.
