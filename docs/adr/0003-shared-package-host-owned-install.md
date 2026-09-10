# ADR 0003: Shared package, host-owned install

## Status

Accepted.

## Decision

Ship portable Agent Skills (`SKILL.md` folders) and optional MCP definitions as the canonical
package. Each host installs that package with its own mechanism:

- Codex uses the existing marketplace registration and `scripts/bootstrap.*`.
- Cursor, Claude Code, and other agents copy skills with `scripts/sync_skills.py` into a path they
  already discover (for example `~/.cursor/skills`, `.cursor/skills`, `~/.claude/skills`, or
  `.claude/skills`), and register MCP servers through their own config if needed.

Do not maintain host-specific install adapters that rewrite Cursor or Claude configuration.

## Consequences

Profiles remain a shared selection of plugins. Codex keeps first-class marketplace UX. Other agents
get a stable skill payload without this repository encoding their private install layouts. MCP
registration outside Codex is documented rather than automated.
