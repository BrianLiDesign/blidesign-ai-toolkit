---
name: orchestrate
description: Coordinate native subagents for substantial independent research, review, or implementation tasks, with bounded delegation, isolated edits, and verified integration. Keep small or tightly dependent tasks in the main agent.
---

# Orchestrate

Use the current host's native subagent tools. Invoking this workflow authorizes appropriate
delegation within the requested task, subject to host policy; it does not expand authorization to
publish, merge a remote PR, deploy, message others, or change personal configuration. Automatic
skill discovery stays enabled. This is an interactive workflow, not a persistent scheduler.

## Frame and assign

1. Read the task, applicable repository guidance, working-tree state, and available tools. Identify
   the requirements, existing edits, verification commands, and current base commit. Keep small or
   tightly dependent work in the main agent. For host setup or capability uncertainty, read only
   the relevant section of [host guidance](references/hosts.md).
2. Let the coordinator own assignments and status. Use the project's issue tracker for durable
   work when required; find existing issues before creating any. Use a session-local task list for
   short-lived assignments. Dispatch only tasks whose dependencies are satisfied.
3. Default to two concurrent workers, reduced by host limits and available capacity; explicit task
   instructions take precedence. Inherit the parent model without selecting another automatically.
   Workers report to the coordinator and do not delegate recursively. A worker needing another
   specialist returns that need to the coordinator.
4. Use the [assignment and handoff contract](references/handoffs.md). Supply objective, source
   pointers, base commit, allowed scope, dependencies, acceptance criteria, verification, and the
   worker's absolute working directory. Include all necessary context rather than assuming the
   host passes conversation history or skills to children.

## Choose the route

- **Research:** split independent questions; use research-and-recommend when available. Otherwise
  require primary sources, cited evidence, uncertainty, and a comparison against task constraints.
- **Review:** fix the same base and head for every reviewer. Use code-review when available and
  authorized to launch its reviewers; count those reviewers within this workflow's worker budget.
  Otherwise assign independent standards and requirements reviews, with file/line evidence and
  actionable findings. Reviewers leave source files unchanged.
- **Implementation:** use implement-spec when available for a spec with dependency-linked tickets.
  The coordinator follows its task-graph approach without nesting orchestrators or delegating
  scheduling to workers. Apply this workflow's concurrency, isolation, and retry limits. Otherwise
  assign ready tasks directly from the requirements and retain their acceptance criteria.

## Isolate implementation and integrate

Parallel research/review may share a checkout under a read-only assignment. That instruction is
not a security boundary; check actual host permissions when enforced read-only access is needed.

Concurrent implementation workers each need a separate branch and worktree based on the current
integration branch. Preserve unrelated edits in the original checkout; create the integration
worktree outside it rather than moving or stashing user work. Record the integration base SHA and
confirm each worker's initial HEAD matches it before edits. Host-created worktrees may start from
the default branch: inspect and correct the base before dispatch, without destructive resets.
All worker commands must target their assigned worktree. If safe isolation or native delegation
is unavailable, complete the work sequentially and disclose the limitation; never claim workers ran.

Only the coordinator integrates, one result at a time. Inspect the returned diff and acceptance
evidence, then merge or cherry-pick the worker's scoped commits into the integration worktree.
Resolve conflicts against the requirements and rerun affected checks. Start newly unblocked tasks
from the updated integration tip. Worktree isolation does not isolate external services, ports,
databases, or shared artifacts; use separate fixtures or serialize those operations.

Use project-check when available to verify the combined state, otherwise run the project's reviewed
checks and record equivalent evidence. Review the integrated diff independently; the coordinator
may perform the review when another worker is unavailable. A clean worker test result does not
establish that the combined result passes.

## Recover and finish

Retry a failed assignment at most once, only with an identified corrective action and within the
original scope. Stop dependent work until the failure is resolved. Preserve partial commits and
dirty worktrees; return blockers rather than marking missing work complete. Interrupt or stop
owned workers before integration or cleanup if their result is no longer usable.

Remove only owned worktrees after their workers have stopped and the work is integrated or explicitly
discarded. Check for uncommitted changes before removal; preserve them instead of force-removing.
Keep branches containing unintegrated commits. Close or release completed native worker sessions
when the host supports it, so session limits remain available.

Return completed tasks, integration commit/branch or checkout state, verification evidence,
remaining blockers, preserved work, and host limitations. Mark tracker work complete only when its
acceptance criteria pass; local implementation does not imply publication or remote PR merge.
For behavioral validation, use the [acceptance scenarios](references/acceptance.md) and distinguish
observed runs from documentation review or tabletop checks.
