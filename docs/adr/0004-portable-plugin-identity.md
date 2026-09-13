# ADR 0004: Use portable plugin manifests as package identity

## Status

Accepted.

## Decision

Owned plugins use a root `plugin.json` as their portable identity. OpenAI-specific presentation
remains in `.codex-plugin/plugin.json` as a compatibility overlay, and both manifests must agree on
stable identity fields. Portable components use the Agent Plugins fixed root paths, while host
configuration and installation remain owned by each host as established in ADR 0003.

## Consequences

Skills-only plugins can adopt the portable format without changing their payload. A plugin that
bundles MCP servers must provide a schema-valid root `mcp.json` before adding a root manifest so the
portable manifest does not disable discovery through the compatibility declaration.
