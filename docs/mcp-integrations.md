# Development MCP integrations

The portable `plugins/*/mcp.json` files are canonical. Compatibility `.mcp.json` definitions use the
same commands, arguments, environments, and endpoints. External packages are referenced, not
vendored; their upstream licenses still apply. No native analysis engine is bundled.

| Capability | Toolkit route | Installation and authentication |
| --- | --- | --- |
| Current library documentation | `find-docs` skill and Context7 CLI | No additional MCP registration; Context7 may request its own login or API key |
| GitHub | Managed Codex plugin, authenticated `gh` CLI, or optional `github-integration` | Hosted MCP authentication depends on the client; Claude Code's documented remote setup requires a token |
| Browser inspection | Existing Browser Act or opt-in `browser-diagnostics` | Avoid installing another general browser MCP for the same task |
| Semantic code navigation | `semantic-code` | Serena pinned to commit `d9e4c796fae0207ba6848d1df4b331122a5567b5`; requires `uvx`, Git, Python 3.13, and project language servers |
| Reverse engineering | Optional `reverse-engineering` | `rea-agents@6.7.0`; Node.js 22.19+, 24.11+, or 26+ in supported major versions; native providers are separate |
| Application errors and performance | Optional `error-monitoring` | Official hosted Sentry MCP; needs a Sentry account and host OAuth |

## Install on a machine

Codex uses the existing profile bootstrap. Development and full include Serena. Install optional
plugins individually using the documented `codex plugin add` command in the README. Keep the managed
GitHub plugin when it is already installed; the standalone GitHub plugin is an alternative for a
host with compatible authentication. The portable definition carries no token or authorization
header. GitHub's Claude Code guide documents token authentication for the remote server, so a bare
URL may fail OAuth discovery. Keep the authenticated `gh` CLI when it already covers the workflow;
do not migrate its credentials into another application's settings automatically. If remote MCP is
required, configure credentials through that host's supported mechanism or use the official native
server with its documented login flow.

Claude Code and Cursor use `scripts/sync_skills.py` for skills and `scripts/sync_mcps.py` for MCPs.
For example, after syncing skills:

```text
python scripts/sync_mcps.py --host claude-code --profile full --plugin github-integration --plugin reverse-engineering --dry-run
python scripts/sync_mcps.py --host claude-code --profile full --plugin github-integration --plugin reverse-engineering
```

Substitute `--host cursor` for Cursor. Add `--plugin browser-diagnostics` only if that host needs it.
Use `--replace` after reviewing a dry-run to replace an existing definition with the same server name.
The installer backs up changed configuration files beside the originals, preserves all other JSON
fields, and keeps payloads in versioned directories under the user's `.blidesign/ai-toolkit/plugins`.
Treat backups as private configuration because they may contain unrelated credentials.

Claude Code user MCP settings live in `~/.claude.json`. When `CLAUDE_CONFIG_DIR` is set, the installer
uses its `.claude.json`. Cursor uses `~/.cursor/mcp.json`. Windows npm command shims are wrapped with
`cmd.exe /d /c`; Node and uv launchers resolve to installed executables. System certificate trust is
used for the referenced package downloads, with TLS validation retained.

Claude Desktop uses a different installation surface. Its local stdio configuration may be
translated from the same canonical definitions after locating its actual configuration directory;
use `--host claude-desktop --config PATH_TO_CONFIG` with the actual configuration file. The script
intentionally does not guess a Windows Store app's redirected path. Remote connectors
belong in the application's supported connector UI. Files written to disk require an application
reload before discovery can be confirmed.

## Use REA when an investigation needs it

Start with a specific behavior question and a target you own or are authorized to examine. Prefer
static inspection first. Inspect the active tool schemas and distinguish source facts, observed
runtime behavior, and inferred explanations in the findings. Preserve target digests and evidence
locations so conclusions can be checked.

JavaScript/Electron and .NET static inspection can work without a native decompiler. Ghidra, Hopper,
and IDA have their own installation and licensing requirements. Windows native analysis has
provider-specific limitations. Registering REA does not establish that every provider is usable.
Runtime capture can launch or interact with the chosen application; select its scope deliberately.
Local analysis results sent to an agent remain subject to the agent provider's data policy.

REA stays opt-in on future machines. Neither installation script starts a persistent background
service or installs commercial analysis tools. REA's packaged workflows can also be installed through
its official setup if needed; review its plan rather than running a second overlapping registration.

## Verify an update

Run the repository verifier and Python tests, both bootstrap dry-runs where shells are available,
and development skill/MCP sync dry-runs. For each installed stdio server, complete MCP initialization,
list tools, and invoke a harmless tool. For Serena, also verify symbol retrieval against a small owned
fixture. For REA, inspect an owned static fixture and check its evidence. Close probe processes.

Use host discovery commands where available. Report OAuth pending and reload pending separately from
configuration validity. A successful standalone MCP probe does not prove that a running application
has reloaded its configuration. Updates affect only the machine where the installation ran.

## Primary documentation

- [Serena running and configuration](https://oraios.github.io/serena/02-usage/020_running.html)
- [REA official installation and provider requirements](https://github.com/morluto/rea/blob/main/docs/installation.md)
- [GitHub official MCP server](https://github.com/github/github-mcp-server)
- [Sentry official MCP server](https://mcp.sentry.dev/)
- [Context7 CLI and MCP modes](https://github.com/upstash/context7)
- [Claude Code MCP configuration](https://code.claude.com/docs/en/mcp-quickstart)
- [Cursor MCP configuration](https://cursor.com/docs/mcp)
- [Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
