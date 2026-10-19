---
name: security-check
description: Assess security implications of a software change using project scanners, dependency and secret checks, and changed trust boundaries. Use for requested security checks or changes affecting authentication, permissions, untrusted input, or sensitive data.
---

# Security check

Resolve the project, change range, supported languages, deployment context, and existing security
configuration. Inspect changed trust boundaries: authentication and authorization, untrusted input,
process invocation, filesystem access, data exposure, dependency changes, and workflow permissions.
Use the repository's existing tools first. Do not turn a routine change into an unrelated full audit.

Choose evidence appropriate to the change:

- Static analysis: use configured CodeQL or the project's equivalent. A completed scan is not a
  clean verdict; inspect findings and their affected commit. Model known exploit preconditions.
- Dependencies: inspect lockfile changes and the package manager's audit or dependency-review results.
  A scanner with no supported dependency inventory has a coverage gap, not proof of safety.
- Secrets: use configured secret scanning with redacted output. Keep values out of reports; record
  location and finding ID. If a real credential was exposed, report the need for rotation and
  controlled history remediation rather than merely deleting the current line.
- Runtime behavior: use focused negative tests for changed permissions, validation, and failure paths.
  Keep probes within authorized targets and use owned fixtures.

Use `project-check` to capture local scanner commands under category `security` when available.
For hosted scans, record the exact head SHA, scanner/job URL, completion state, finding dispositions,
and unsupported or inaccessible checks. Use normal PR events with minimal workflow permissions;
untrusted PR code must not execute with privileged secrets through `pull_request_target`.

Classify actionable findings by impact and reproducible evidence. Fix within scope, add an effective
regression test where appropriate, then rerun the affected check. Explain false positives with
specific evidence; retain existing thresholds instead of disabling rules to obtain a green check.
Report passed, failed, blocked, and untested coverage separately. Scanner success alone does not
establish that the application is secure.

When adding CI, use [the CI reference](references/ci.md). Install or configure account-bound tools
only within the user's request; preserve existing authorization and repository policy.
