# Domain context

## Marketplace

The Git repository that packages portable plugins for AI coding agents. Its public identifier is
`blidesign-ai-toolkit`, defined in `.agents/plugins/marketplace.json`. Codex can register it as a
plugin source; other agents consume the same skill folders through their own install paths.

## Marketplace plugin

A portable installable unit under `plugins/`. Each plugin has a matching folder name and uses a root
`plugin.json` as its portable identity. A plugin may contain skills, MCP servers, scripts, or assets.

## Compatibility overlay

Host-specific plugin metadata that supplements a portable marketplace plugin without redefining its
identity or content model. Codex compatibility metadata lives in `.codex-plugin/plugin.json`.

## Profile

A named selection of marketplace plugins plus optional external plugin references. Profiles make
machine setup intentional rather than installing every integration everywhere. Codex bootstrap and
`scripts/sync_skills.py` both read the same profiles.

## Vendored source

Licensed third-party source copied into a marketplace plugin. Every vendored source has its
repository, full Git commit, license, vendored license path, transformations, and exact-content
digest recorded in `upstream/sources.lock.json`.

## External plugin

A plugin installed from another configured marketplace by identifier. Its source, cache, and
authentication state are not copied into this repository. External plugin IDs in profiles are
Codex-oriented today.

## Portable configuration

Configuration containing relative paths and environment-variable names only. It excludes secrets,
tokens, user-specific paths, agent caches, and generated runtime files.

## Skill sync

Copying profile-selected `SKILL.md` directories to a host-chosen destination with
`scripts/sync_skills.py`. The host (Cursor, Claude Code, Codex, or another agent) is responsible for
discovering skills from that path.
