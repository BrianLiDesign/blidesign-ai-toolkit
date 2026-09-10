# Repository guidance

Keep this repository portable across Windows, macOS, and Linux. Never commit credentials, agent
caches, runtime folders, local configuration, or absolute user paths. Preserve licenses and full
commit provenance for all vendored sources.

Run `python scripts/verify.py` and `python -m unittest discover -s tests -v` after changes. Test both
bootstrap scripts in dry-run mode when their shells are available, and dry-run
`python scripts/sync_skills.py --profile development --target <tmp> --dry-run`.

## Agent skills

### Issue tracker

Track work in the GitHub Issues repository associated with the configured remote. See
`docs/agents/issue-tracker.md`.

### Triage labels

Use the five canonical Matt Pocock triage roles. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md` and `CONTEXT.md`.
