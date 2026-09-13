# Contributing

Use GitHub Issues in this repository for proposed work. New issues should use one of the canonical
triage roles documented in `docs/agents/triage-labels.md`; work that is fully scoped and safe for an
agent should use `ready-for-agent`.

## Repository contracts

- Treat the marketplace name, plugin names, and released skill names as stable public identifiers.
- Keep paths portable and relative. Do not commit credentials, local configuration, agent caches,
  runtime directories, local inventory exports, or absolute user paths. The generated portable
  catalog under `plugins/developer-mcps/assets/` is a reviewed package artifact, not local state.
- Keep installation host-owned. Do not add scripts that rewrite Cursor, Claude Code, Codex, or
  another host's private configuration.
- Add third-party source only when redistribution is permitted. Preserve its license and record its
  repository, full commit SHA, transformation notes, license path, and content digest in
  `upstream/sources.lock.json`.
- Review upstream changes and licensing before applying an update. Do not automatically track a
  moving branch.

## Plugin changes

Root `plugin.json` is the portable plugin identity. Keep `.codex-plugin/plugin.json` as the OpenAI
compatibility overlay and keep their name, version, description, and license fields identical.
Portable MCP packages also require a schema-valid root `mcp.json`; `.mcp.json` remains the
compatibility configuration.

## Validation

Run the following before requesting review:

```text
python scripts/verify.py
python -m unittest discover -s tests -v
python scripts/sync_skills.py --profile development --target <temporary-directory> --dry-run
```

Dry-run both bootstrap scripts when their shells are available. Validate each compatibility
manifest with the installed Codex plugin validator from a Python environment that provides its
dependencies, including PyYAML. Include updated manifests, provenance records, licenses, and
generated catalog data in the same change.
