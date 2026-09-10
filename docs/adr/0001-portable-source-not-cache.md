# ADR 0001: Package portable source, not installed caches

## Status

Accepted.

## Decision

The marketplace vendors only owned or redistribution-compatible source. OpenAI-managed plugins and
other external integrations are recorded as profile references and installed from their original
marketplaces. Credentials, generated caches, runtime paths, and local agent configuration are never
copied.

## Consequences

Each machine authenticates external services independently. The repository remains reviewable,
license-aware, and portable, while managed plugins continue receiving upstream updates.
