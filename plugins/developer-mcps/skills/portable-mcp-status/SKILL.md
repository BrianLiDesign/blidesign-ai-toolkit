---
name: portable-mcp-status
description: Inspect the installed portable marketplace's plugin, profile, provenance, and skill counts. Use for marketplace health or inventory questions.
---

# Portable MCP Status

Call the `marketplace_status` MCP tool and report its structured result. A healthy response means the
repository manifests could be read; it does not prove that optional external plugins are available
or authenticated.

If the tool fails, run `python scripts/verify.py` from the marketplace repository when local shell
access is available. Do not inspect credential files or expose environment-variable values while
diagnosing status.
