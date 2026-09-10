# BliDesign AI Toolkit

A portable package of Agent Skills and MCP utilities you can install onto Codex, Cursor, Claude Code,
or any other host that discovers `SKILL.md` folders. The repository vendors redistributable source
and references managed plugins by their original marketplace identifiers where a host supports that.

## Included plugins

- **engineering-skills**: 37 pinned Matt Pocock engineering and productivity skills.
- **marketplace-maintainer**: a skill for auditing provenance, manifests, profiles, and releases.
- **developer-mcps**: a dependency-free local MCP server that reports marketplace health.

Profiles select which plugins to install. The `development` and `full` profiles also list useful
OpenAI-managed plugins as optional **Codex** external dependencies. They remain subject to account
availability and authenticate independently on each machine.

## Install skills on any agent

Copy the skills from a profile into a directory your agent already loads:

```powershell
py scripts/sync_skills.py --profile development --target $HOME\.cursor\skills
```

```bash
python scripts/sync_skills.py --profile development --target ~/.claude/skills
```

Common destinations:

| Host | Personal | Project |
| --- | --- | --- |
| Cursor | `~/.cursor/skills` | `.cursor/skills` |
| Claude Code | `~/.claude/skills` | `.claude/skills` |
| Other Agent Skills hosts | whatever path that host documents | project-local skills dir |

Use `--dry-run` to preview copies. Restart or reload the agent afterward so new skills are picked up.

To expose the local status MCP outside Codex, point your host's MCP config at
`plugins/developer-mcps/.mcp.json` (or the `node …/marketplace_status_mcp.mjs` command it declares),
using paths appropriate for that machine. Do not commit absolute paths.

## Install with Codex

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

### Install after hosting in Git

Push the repository to a Git host, then supply its source in a form accepted by Codex—such as
`OWNER/blidesign-ai-toolkit`, an HTTPS Git URL, or an SSH Git URL:

```powershell
.\scripts\bootstrap.ps1 -Profile full -Source OWNER/blidesign-ai-toolkit -Ref stable
```

```bash
bash scripts/bootstrap.sh --profile full --source OWNER/blidesign-ai-toolkit --ref stable
```

Use a `stable` branch for machines that should receive reviewed updates. Use `main` only for machines
that intentionally track development.

Codex keeps an existing marketplace registration. If a machine must switch to a different Git
source or ref, explicitly reconcile it:

```powershell
.\scripts\bootstrap.ps1 -Profile full -Source OWNER/blidesign-ai-toolkit -Ref main -ReconfigureMarketplace
```

```bash
bash scripts/bootstrap.sh --profile full --source OWNER/blidesign-ai-toolkit --ref main --reconfigure-marketplace
```

## Profiles

| Profile | Marketplace plugins | Optional external plugins (Codex) |
| --- | --- | --- |
| `minimal` | Maintainer | None |
| `development` | Engineering, maintainer, MCP status | GitHub, Browser Act |
| `full` | Engineering, maintainer, MCP status | GitHub, Notion, Browser Act, Data Analytics, Product Design |

Pass `-SkipExternal` or `--skip-external` on Codex bootstrap to install only plugins owned by this
marketplace. Use `-DryRun` or `--dry-run` to preview every Codex command. The same profile names feed
`scripts/sync_skills.py`.

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

Export the current machine's portable Codex inventory fields:

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

The updater also refreshes the packaged MCP catalog and adds a cachebuster to affected Codex plugin
versions. Commit those manifests, the updated skills, license file, and
`upstream/sources.lock.json` together.

After editing profiles or marketplace metadata directly, regenerate the MCP's packaged catalog:

```powershell
py scripts/sync_catalog.py
```

## Update installed machines

Refresh a Git-hosted Codex marketplace and rerun the profile bootstrap:

```powershell
codex plugin marketplace upgrade blidesign-ai-toolkit
.\scripts\bootstrap.ps1 -Profile development -Source OWNER/blidesign-ai-toolkit
```

Local-path marketplaces read the checkout directly and do not need a marketplace upgrade.

For Cursor, Claude Code, or other hosts, rerun `scripts/sync_skills.py` against the same target
directory after pulling updates.

## Security and licensing

- Never commit tokens, cookies, `.env` files, agent configuration, caches, or runtime folders.
- MCP definitions use relative plugin paths and require no credentials.
- External plugins are installed from their original marketplace rather than copied.
- Vendored source must retain its license and full commit provenance.

Matt Pocock's vendored skills remain covered by their upstream MIT license in
`plugins/engineering-skills/LICENSES/mattpocock-skills-MIT.txt`.
