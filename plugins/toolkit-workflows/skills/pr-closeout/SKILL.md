---
name: pr-closeout
description: Finish an authorized GitHub PR through review remediation, CI, metadata, merge, and post-merge verification. Use for PR closeout; keep assessment-only requests read-only.
---

# PR closeout

Resolve the repository and PR from the configured remote or user-provided URL. Read repository
guidance and inspect the PR's current head, base, linked issues, reviews, unresolved threads,
checks, labels, milestone, project fields, and merge policy. Fetch before comparing local state.

Match actions to the user's request. A review request authorizes inspection; a remediation request
authorizes fixes and validation. Merge only when the user has authorized it. Existing authorization
persists through the workflow. Branch protection and required independent reviews remain binding;
do not bypass them or change protection to finish a merge.

Address every actionable review comment, including comments outside unresolved threads. Keep a
short disposition for each: fixed, already addressed with evidence, or blocked with a reason.
Resolve threads only after verifying the fix and within the requested scope. Use the repository's
regression gates and add targeted coverage for changed behavior. Stage only owned task changes.

Before pushing, inspect the final diff for unrelated files and secrets. Commit and push the fixes,
then wait for checks against the exact pushed head. Reconcile labels, linked issues, milestone,
and project state using repository conventions and accessible evidence. Report inaccessible fields
as unverified instead of guessing their values. Keep closing references accurate.

When authorized and merge requirements pass, use the repository's intended merge method. Confirm
the remote merged state, resulting commit, linked issue state, and relevant post-merge checks.
Update a local checkout only by a safe fast-forward after checking for local changes and divergence.

Report the PR link, commit, checks, review dispositions, and any incomplete metadata or access step.
A merged PR and green CI establish source integration. Claim live deployment acceptance only from
separately observed deployment behavior. Use release-acceptance if available and that work is in scope.
