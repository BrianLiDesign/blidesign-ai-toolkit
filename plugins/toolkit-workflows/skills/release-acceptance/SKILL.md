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
