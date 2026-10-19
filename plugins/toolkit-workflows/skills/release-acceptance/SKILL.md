---
name: release-acceptance
description: Verify a deployed release against public behavior and persistence requirements, recording inspectable evidence and cleaning up owned test data.
---

# Release acceptance

Identify the release commit, deployment URL, environment, acceptance requirements, and existing
authorization for test writes. Use provider APIs or CLI status to confirm which commit the URL
serves. A deployment marked ready is a starting point, not behavioral evidence.

Translate requirements into observable checks. Check response contracts, identity, defaults,
validation failures, and user-visible behavior as applicable. A successful status code alone does
not establish success. For persistence requirements, write a uniquely identifiable owned fixture,
read it back through the supported public interface, and compare the required fields. Use only
authorized environments and operations; prepare read-only checks while any required write approval
is pending. Stop writes if the target environment or ownership is uncertain.

For UI requirements, capture the relevant viewport and interaction states. Record actual behavior,
including console or network failures when they bear on the requirement. Preserve evidence without
credentials, real user data, or authenticated session material.

Track created fixture identifiers immediately, including partial successes. Clean up only those
fixtures with the supported delete/revert operation and verify removal. Attempt cleanup after a
failed check too; report any residual fixture and recovery step if cleanup fails.

Report each requirement as passed, failed, blocked, or untested with its evidence. Distinguish
controlled tests, owned local services, and live deployments. Record commit, environment, time,
reproduction command or action, expected result, observed result, and cleanup outcome. Attribute
human contributions only when evidenced. Keep unavailable deployment logs or access steps explicit.

For releases involving schema or data changes, check migration compatibility with the deployed and
rollback versions. Verify backup/restore or rollback readiness through existing procedures; do not
trigger production rollback merely to prove it exists. Exercise failure and recovery on owned test
environments when within scope. Record any irreversible migration and the agreed recovery route.

Inspect available deployment logs, error reports, latency, and resource signals for the tested
release, using the application's existing telemetry. Compare relevant behavior with its baseline
and state the observation window. A quiet error dashboard without representative traffic is weak
evidence. Report missing instrumentation as unobserved coverage; adding a new telemetry service is
a separate configuration change. Keep operational evidence tied to the deployment SHA and exclude
credentials and user payloads. Preserve fixture cleanup and rollback-readiness outcomes in the
acceptance report alongside public behavior and persistence results.
