# Domain context

## Marketplace

The Git repository Codex registers as a plugin source. Its public identifier is
`brian-ai-tools`, defined in `.agents/plugins/marketplace.json`.

## Marketplace plugin

A portable installable unit under `plugins/`. Each plugin has a matching folder name and
`.codex-plugin/plugin.json` name. A plugin may contain skills, MCP servers, scripts, or assets.

## Profile

A named selection of marketplace plugins plus optional external plugin references. Profiles make
machine setup intentional rather than installing every integration everywhere.

## Vendored source

Licensed third-party source copied into a marketplace plugin. Every vendored source has a full Git
commit and license recorded in `upstream/sources.lock.json`.

## External plugin

A plugin installed from another configured marketplace by identifier. Its source, cache, and
authentication state are not copied into this repository.

## Portable configuration

Configuration containing relative paths and environment-variable names only. It excludes secrets,
tokens, user-specific paths, Codex caches, and generated runtime files.
