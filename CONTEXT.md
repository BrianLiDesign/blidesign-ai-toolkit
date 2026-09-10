# Domain context

## Marketplace

The Git repository that packages portable plugins for AI coding agents. Its public identifier is
`blidesign-ai-toolkit`, defined in `.agents/plugins/marketplace.json`. Codex can register it as a
plugin source; other agents consume the same skill folders through their own install paths.

## Marketplace plugin

A portable installable unit under `plugins/`. Each plugin has a matching folder name. Codex packaging
uses a matching `.codex-plugin/plugin.json` name. A plugin may contain skills, MCP servers, scripts,
or assets.

## Profile

A named selection of marketplace plugins plus optional external plugin references. Profiles make
machine setup intentional rather than installing every integration everywhere. Codex bootstrap and
`scripts/sync_skills.py` both read the same profiles.

## Vendored source

Licensed third-party source copied into a marketplace plugin. Every vendored source has a full Git
commit and license recorded in `upstream/sources.lock.json`.

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
