---
name: marketplace-maintainer
description: Audit, update, and prepare this portable Codex plugin marketplace for release. Use when changing its plugins, profiles, upstream pins, or bootstrap workflow.
---

# Marketplace Maintainer

Work from the marketplace repository root.

Before changing anything, read `.agents/plugins/marketplace.json`, the selected profile under
`profiles/`, and `upstream/sources.lock.json`. Treat the marketplace and plugin names as stable
public identifiers.

Keep the repository portable:

- Never copy Codex caches, runtime directories, local config, credentials, or absolute machine paths.
- Vendor third-party source only when redistribution is allowed. Preserve its license and record a
  full commit SHA in `upstream/sources.lock.json`.
- Keep secrets out of manifests. MCP credentials must be requested through environment-variable
  names or provider authentication on each machine.
- Add plugins through `.agents/plugins/marketplace.json`; every source path must remain relative to
  the marketplace root.

Run `python scripts/verify.py` after each logical change. Before a stable release, run the full
Python test suite, validate every plugin with Codex's plugin validator when it is available, and
smoke-test `scripts/bootstrap.ps1 -DryRun` or `scripts/bootstrap.sh --dry-run` for each profile.

Only update upstream pins or publish a Git release when the user asks. Summarize changed versions,
licenses, required authentication, and any optional plugin that could not be installed.
