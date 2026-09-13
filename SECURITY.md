# Security Policy

## Reporting a vulnerability

Report suspected vulnerabilities privately through this repository's GitHub Security Advisories.
Do not open a public issue for credentials, exploitable connector behavior, command injection,
path traversal, or another vulnerability that could put users or their data at risk.

Include the affected plugin or script, impact, reproduction steps, and any suggested mitigation.
Do not include real credentials, private data, or tokens in the report.

## Security boundaries

- This repository never stores credentials or authentication state.
- Plugin and MCP paths must remain inside their plugin and must not contain absolute user paths.
- External plugins authenticate with their original provider and remain subject to that provider's
  permissions, terms, and data handling.
- Host configuration is owned by the host and user. Repository scripts must not rewrite private
  Cursor, Claude Code, Codex, or other agent configuration.
- Vendored source must retain its license, full upstream commit provenance, documented
  transformations, and verified content digest.

Only the `main` branch receives active development. The `stable` branch contains changes promoted
after repository verification and installation smoke testing.
