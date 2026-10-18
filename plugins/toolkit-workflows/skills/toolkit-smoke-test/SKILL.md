---
name: toolkit-smoke-test
description: Verify a toolkit update across installed agent hosts using skill discovery, installed versions, MCP startup, and harmless tool calls. Use after installation or for cross-host release checks.
---

# Toolkit smoke test

Start from the toolkit checkout and selected profile. Read its manifests for expected versions,
skill names, and MCP definitions. Discover available hosts and connected machines rather than
assuming that copied files prove an application loaded them. Keep machine paths and configuration
outside the repository; inspect only necessary configuration fields and redact credentials.

Run `python scripts/verify.py` and `python -m unittest discover -s tests -v` in the checkout. Dry-run
both bootstrap scripts when their shells exist, plus the development skill sync into a temporary
target. Use the installed host's help and current official documentation for host-specific commands.

For each intended host:

- Compare installed plugin versions or synced skill bytes with the selected profile. Check for
  duplicate discovery, especially personal skills that overlap plugin-provided skills. Preserve
  unrelated built-ins and user customizations; back up conflicting user files before replacement.
- Check the host's MCP registration and resolve its runtime paths. Initialize each toolkit MCP,
  list its tools, and call a harmless tool. For marketplaceStatus, require `healthy: true` and
  compare catalog counts with the checkout. This status describes the packaged catalog, not the
  install state of other applications or machines.
- For optional Chrome DevTools, use an isolated browser with a blank or owned local page. A successful
  initialization alone is insufficient: invoke a browser tool and verify its result. Close the
  temporary browser after probing. Keep this integration opt-in on future machines.
- When a host supports a discovery/status command, verify that it recognizes the skills and MCPs.
  Otherwise distinguish files/configuration verified from application discovery pending a reload.

Update only reachable machines and authorized hosts. A Git push does not update another computer.
For unavailable machines, report the missing connection and provide portable update commands using
the actual published ref. Never report them as updated.

Return a compact host matrix with expected and observed versions, file/discovery checks, MCP probe
results, and reload or authentication steps still pending. Store detailed machine-specific evidence
only in a user-local location when needed.
