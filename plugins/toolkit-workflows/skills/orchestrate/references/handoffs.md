# Assignment and handoff contract

Use this compact structure in native tool arguments or messages. It is a communication contract,
not a new API or an installed task database. The coordinator owns dependency and status updates.

## Assignment

```text
Task: stable task or issue identifier
Objective: concrete result
Sources: spec/issue/files and relevant skill paths
Base: integration branch and exact starting commit
Working directory: absolute assigned checkout/worktree (local message only)
Allowed scope: files or question owned by this worker; read-only or implementation
Dependencies: completed prerequisites and their evidence
Acceptance: observable requirements
Verification: reviewed commands and expected results
Limits: no recursive delegation; inherit parent model; stay within task authorization
Return: findings or scoped commits, changed files, checks, blockers, uncertainty
```

For example, assign one worker an API contract review and another a repository standards review
of the same fixed diff. They inspect independently and return findings; neither edits that diff.
For implementation, assign separate modules to separate worktrees, each starting at the recorded
integration tip. A dependent documentation update starts only after the relevant code is integrated.

## Handoff

```text
Task and status: complete / partial / blocked
Result: findings with sources, or branch and commit IDs
Changed files: scoped list, or none
Verification: command, working directory, tested commit/dirty state, exit/result
Acceptance: requirements satisfied and gaps
Blockers and uncertainty: explicit, including unavailable checks
Preserved work: worktree/branch/artifact pointers
```

Store local absolute paths, transcripts, runtime files, and machine evidence outside the repository.
Durable repository notes and issue updates use portable paths and redacted summaries. Never include
credentials or assume an agent's success message substitutes for inspected artifacts.
