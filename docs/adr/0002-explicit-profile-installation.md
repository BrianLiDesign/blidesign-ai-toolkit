# ADR 0002: Install explicit profiles

## Status

Accepted.

## Decision

Marketplace entries remain `AVAILABLE`. Bootstrap scripts explicitly install the plugins listed in
one of three profiles: `minimal`, `development`, or `full`. External plugins are optional and may be
skipped when account policy or availability prevents installation.

## Consequences

Installation failures are visible, machines can use different tool sets, and rerunning bootstrap
reconciles the chosen profile without silently installing every integration.
