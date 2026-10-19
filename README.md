# BliDesign AI Toolkit

A portable package of Agent Skills and MCP utilities you can install onto Codex, Cursor, Claude Code,
or any other host that discovers `SKILL.md` folders. The repository vendors redistributable source
and references managed plugins by their original marketplace identifiers where a host supports that.

Owned plugins use the Agent Plugins root `plugin.json` as their portable identity and retain
`.codex-plugin/plugin.json` for OpenAI compatibility. The local MCP plugin likewise provides portable
`mcp.json` and compatibility `.mcp.json` definitions.

## Included plugins

- **engineering-skills**: 38 pinned Matt Pocock engineering and productivity skills.
- **marketplace-maintainer**: a skill for auditing provenance, manifests, profiles, and releases.
- **developer-mcps**: a dependency-free local MCP server that reports marketplace health.
- **toolkit-workflows**: project verification and security checks, PR closeout, release acceptance,
  research and recommendations, current documentation lookup, engineering visuals, and cross-host
  installation smoke tests.
- **browser-diagnostics**: opt-in Chrome DevTools MCP, pinned to version 1.11.0.
- **semantic-code**: pinned Serena MCP for symbol navigation, references, and editing.
- **reverse-engineering**: opt-in REA MCP for inspecting applications and binaries.
- **github-integration**: optional official GitHub MCP for other hosts; Codex keeps its managed plugin.
- **error-monitoring**: optional official Sentry MCP, authenticated separately on each host.

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

To expose the local status MCP outside Codex, use `plugins/developer-mcps/mcp.json` as the portable
source of truth and translate its relative stdio command into the host's documented MCP
configuration. `.mcp.json` is retained only as the Codex compatibility definition. Use paths
appropriate for that machine and do not commit absolute paths.

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

Push the repository to a Git host, then supply its source in a form accepted by Codexâ€”such as
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
| `development` | Engineering, maintainer, MCP status, toolkit workflows, Serena | GitHub, Browser Act |
| `full` | Engineering, maintainer, MCP status, toolkit workflows, Serena | GitHub, Notion, Browser Act, Data Analytics, Product Design |

Pass `-SkipExternal` or `--skip-external` on Codex bootstrap to install only plugins owned by this
marketplace. Use `-DryRun` or `--dry-run` to preview every Codex command. The same profile names feed
`scripts/sync_skills.py`.

### Development MCP integrations

Context7 stays available through the existing `find-docs` CLI workflow. Use the existing browser
integration before adding another browser server. Serena is included in development and full;
it requires `uvx`, Git, Python 3.13, and language servers appropriate to the project. Its source is
pinned to a full commit. Browser windows and the Serena dashboard are disabled at startup.

For Claude Code and Cursor, install MCPs separately from skills:

```text
python scripts/sync_mcps.py --host claude-code --profile full --dry-run
python scripts/sync_mcps.py --host claude-code --profile full
python scripts/sync_mcps.py --host cursor --profile full
```

Add `--plugin github-integration` when the host lacks GitHub access, or `--plugin reverse-engineering`
for REA. Sentry is available with `--plugin error-monitoring` when you have a Sentry account.
These plugins remain outside default profiles. Codex users install an optional plugin with
`codex plugin add PLUGIN_NAME@blidesign-ai-toolkit` instead of running the MCP sync script.

The installer preserves unrelated settings and stages versioned runtime files outside the checkout.
Conflicting named entries require `--replace`, which creates a timestamped configuration backup.
Reload the host afterward. OAuth connections need authentication in each application; registration
does not establish account access. See [integration requirements and verification](docs/mcp-integrations.md).

### Optional browser diagnostics

Install this integration separately after registering the marketplace:

```text
codex plugin add browser-diagnostics@blidesign-ai-toolkit
```

For other MCP hosts, translate `plugins/browser-diagnostics/mcp.json` into the host's documented
configuration. It requires Node.js supported by the pinned package and an installed Google Chrome.
The first launch downloads the package through npm; each host starts its own temporary headless
Chrome profile. Usage statistics and CrUX field-data requests are disabled. The server is launched
on demand by the host rather than installed as a background service. See the
[upstream documentation](https://github.com/ChromeDevTools/chrome-devtools-mcp) for requirements.

The integration is absent from every default profile. Install it only on hosts where browser
diagnostics are wanted. Browser Act remains the profile's general browser interaction option.
The upstream package runs through npm; its source is not vendored into this repository.

### Toolkit workflows

The development and full profiles include these owned workflows:

- `pr-closeout`: review remediation, CI, metadata, authorized merge, and post-merge verification.
- `release-acceptance`: public behavior checks, persistence read-back, evidence, and fixture cleanup.
- `find-docs`: current documentation through the Context7 CLI, with source citations.
- `research-and-recommend`: primary-source research, applicable standards, comparison of viable
  approaches, and a recommendation with tradeoffs and an implementation outline.
- `toolkit-smoke-test`: installed versions, skill discovery, MCP startup, and harmless tool calls.
- `project-check`: reviewed project commands, bounded execution, and commit-specific JSON evidence.
- `security-check`: scanner findings, dependency and secret checks, and changed trust boundaries.
- `engineering-visuals`: routes each diagram to a specialist with standards and rendering checks.
- `engineering-diagrams`: Mermaid flow, sequence, state, and entity-relationship diagrams.
- `architecture-diagrams`: C4 views, system boundaries, and existing or proposed designs.
- `dependency-graphs`: evidence-backed module, package, and build dependency graphs.
- `editable-diagrams`: draw.io sources for manual layout and continued editing.

For an unfamiliar implementation or open decision, ask: "Use research-and-recommend to investigate
[question], compare viable approaches against [constraints], and recommend the best fit."

Keep an existing personal `find-docs` installation in only one host-discovered location to avoid
duplicate discovery. Back up personal customizations before replacing it with the packaged skill.
The new workflows are maintained separately from the pinned Matt Pocock collection. Small owned
additions to its router, TDD, review, and debugging guidance are declared in
`upstream/mattpocock-overlays.json` and reapplied by the updater without changing the upstream pin.

### Project verification

The runner is self-contained inside the `project-check` skill, so it works after syncing to any
harness. Discovery reads package scripts and lists documentation/CI sources without executing them:

```text
python plugins/toolkit-workflows/skills/project-check/scripts/project_check.py --root . --discover
```

Review commands before adding them to a project's `.project-check.json`. This repository's manifest
uses its existing verifier and unit tests. Run it and save evidence outside the checkout:

```text
python plugins/toolkit-workflows/skills/project-check/scripts/project_check.py --root . --run --report ../toolkit-project-check.json
```

The JSON includes commit/dirty state, source fingerprints, command results, durations, bounded
redacted output, and missing checks. Focused `--check ID` runs can be partial. Discovery is not a
verification pass. Commands run with your permissions; the runner is not a sandbox. See the
[manifest and evidence reference](plugins/toolkit-workflows/skills/project-check/references/manifest.md).

Security CI separately runs CodeQL for Python, JavaScript and Actions, dependency review on PRs,
and a history secret scan. Scanner completion does not establish application security; inspect
findings and inventory coverage. Remote MCP package-runner references need separate dependency
review. CI preserves verification evidence for seven days; local reports remain outside Git.

## Verify

```powershell
py scripts/verify.py
py -m unittest discover -s tests -v
```

The verifier checks marketplace and plugin schemas, portable-to-compatibility identity consistency,
portable MCP transports, profiles, semver, upstream provenance and content digests, declared
component paths, licenses, and common committed-secret signatures.

Validate a plugin with the Codex plugin validator when developing locally:

```powershell
py C:\Users\YOUR_NAME\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py plugins\engineering-skills
```

The validation command intentionally contains a placeholder because the system skill path is local
to each account; do not commit an expanded user-specific path. Run it from a Python environment that
provides the validator's dependencies, including PyYAML.

## Inventory

Export the current machine's portable Codex inventory fields:

```powershell
py scripts/export_inventory.py
```

The ignored `inventory.local.json` contains names, versions, enablement, transport types, and auth
status only. It excludes MCP environment maps, commands, local paths, and credential values.

## Engineering visuals

The `development` and `full` profiles include an engineering visual workflow through
`toolkit-workflows`. Ask for a diagram directly, or use `engineering-visuals` to choose a specialist:

| Skill | Use |
| --- | --- |
| [engineering-visuals](plugins/toolkit-workflows/skills/engineering-visuals/SKILL.md) | Route each visual to the appropriate specialist. |
| [engineering-diagrams](plugins/toolkit-workflows/skills/engineering-diagrams/SKILL.md) | Mermaid flowcharts, sequences, states, and data models. |
| [architecture-diagrams](plugins/toolkit-workflows/skills/architecture-diagrams/SKILL.md) | C4 views and architecture comparisons. |
| [dependency-graphs](plugins/toolkit-workflows/skills/dependency-graphs/SKILL.md) | Evidence-backed module and package graphs. |
| [editable-diagrams](plugins/toolkit-workflows/skills/editable-diagrams/SKILL.md) | Editable draw.io diagrams and manual layout. |

Each specialist includes researched practices, dated primary-source references, examples, and
domain checks. They share [delivery and validation standards](plugins/toolkit-workflows/skills/engineering-visuals/references/standards.md)
and a [local rendering helper](plugins/toolkit-workflows/skills/engineering-visuals/references/rendering.md).
Editable source is retained; rendering and visual inspection are reported separately. Renderers
are optional external dependencies, installed separately with exact versions when needed. Skill
sync copies the full skill set and does not install a browser, Node package, or diagram editor.
Interactive simulations and UI wireframes are outside this workflow's first release.

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
- MCP definitions use relative plugin paths or public HTTPS endpoints. Account integrations use
  host-managed authentication; credentials remain outside the repository.
- External plugins are installed from their original marketplace rather than copied.
- Vendored source must retain its license and full commit provenance.

Matt Pocock's vendored skills remain covered by their upstream MIT license in
`plugins/engineering-skills/LICENSES/mattpocock-skills-MIT.txt`.
