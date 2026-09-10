# Brian's AI Tools

A portable Codex plugin marketplace for installing a consistent set of skills and MCP utilities on
multiple machines. The repository packages source that can be redistributed and references managed
plugins by their original marketplace identifiers.

## Included plugins

- **engineering-skills**: 37 pinned Matt Pocock engineering and productivity skills.
- **marketplace-maintainer**: a skill for auditing provenance, manifests, profiles, and releases.
- **developer-mcps**: a dependency-free local MCP server that reports marketplace health.

The `development` and `full` profiles also list useful OpenAI-managed plugins as optional external
dependencies. They remain subject to account availability and authenticate independently on each
machine.

## Install from this checkout

Windows PowerShell:

```powershell
.\scripts\bootstrap.ps1 -Profile development
```

macOS or Linux:

```bash
bash scripts/bootstrap.sh --profile development
```

This registers the checkout as a user-level Codex marketplace and installs the selected plugins.
Start a new Codex task afterward so the new skills and MCP tools are loaded.

## Install after hosting in Git

Push the repository to a Git host, then supply its source in a form accepted by Codex—such as
`OWNER/ai-toolkit-marketplace`, an HTTPS Git URL, or an SSH Git URL:

```powershell
.\scripts\bootstrap.ps1 -Profile full -Source OWNER/ai-toolkit-marketplace -Ref stable
```

```bash
bash scripts/bootstrap.sh --profile full --source OWNER/ai-toolkit-marketplace --ref stable
```

Use a `stable` branch for machines that should receive reviewed updates. Use `main` only for machines
that intentionally track development.

Codex keeps an existing marketplace registration. If a machine must switch to a different Git
source or ref, explicitly reconcile it:

```powershell
.\scripts\bootstrap.ps1 -Profile full -Source OWNER/ai-toolkit-marketplace -Ref main -ReconfigureMarketplace
```

```bash
bash scripts/bootstrap.sh --profile full --source OWNER/ai-toolkit-marketplace --ref main --reconfigure-marketplace
```

## Profiles

| Profile | Marketplace plugins | Optional external plugins |
| --- | --- | --- |
| `minimal` | Maintainer | None |
| `development` | Engineering, maintainer, MCP status | GitHub, Browser Act |
| `full` | Engineering, maintainer, MCP status | GitHub, Notion, Browser Act, Data Analytics, Product Design |

Pass `-SkipExternal` or `--skip-external` to install only plugins owned by this marketplace. Use
`-DryRun` or `--dry-run` to preview every Codex command.

## Verify

```powershell
py scripts/verify.py
py -m unittest discover -s tests -v
```

The verifier checks marketplace and plugin schemas, profiles, semver, upstream provenance, declared
component paths, licenses, and common committed-secret signatures.

Validate a plugin with the Codex plugin validator when developing locally:

```powershell
py C:\Users\YOUR_NAME\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py plugins\engineering-skills
```

The validation command intentionally contains a placeholder because the system skill path is local
to each account; do not commit an expanded user-specific path.

## Inventory

Export the current machine's portable inventory fields:

```powershell
py scripts/export_inventory.py
```

The ignored `inventory.local.json` contains names, versions, enablement, transport types, and auth
status only. It excludes MCP environment maps, commands, local paths, and credential values.

## Update vendored skills

Check the pinned upstream commit:

```powershell
py scripts/update_upstreams.py
```

Review upstream changes and licensing before applying them:

```powershell
py scripts/update_upstreams.py --apply
py scripts/verify.py
py -m unittest discover -s tests -v
```

The updater also refreshes the packaged MCP catalog and adds a Codex cachebuster to affected plugin
versions. Commit those manifests, the updated skills, license file, and
`upstream/sources.lock.json` together.

After editing profiles or marketplace metadata directly, regenerate the MCP's packaged catalog:

```powershell
py scripts/sync_catalog.py
```

## Update installed machines

Refresh a Git-hosted marketplace and rerun the profile bootstrap:

```powershell
codex plugin marketplace upgrade brian-ai-tools
.\scripts\bootstrap.ps1 -Profile development -Source OWNER/ai-toolkit-marketplace
```

Local-path marketplaces read the checkout directly and do not need a marketplace upgrade.

## Security and licensing

- Never commit tokens, cookies, `.env` files, Codex configuration, caches, or runtime folders.
- MCP definitions use relative plugin paths and require no credentials.
- External plugins are installed from their original marketplace rather than copied.
- Vendored source must retain its license and full commit provenance.

Matt Pocock's vendored skills remain covered by their upstream MIT license in
`plugins/engineering-skills/LICENSES/mattpocock-skills-MIT.txt`.
