# Verification manifest and evidence

The bundled runner requires Python 3.10 or later and no third-party packages. It can be invoked from
any directory after the skill is copied to a harness. `{python}` resolves to the current interpreter.
Its default action is discovery; execution requires `--run` and an explicit manifest.

Example project-owned `.project-check.json`:

```json
{
  "schemaVersion": 1,
  "requiredCategories": ["test", "lint"],
  "checks": [
    {
      "id": "tests",
      "category": "test",
      "argv": ["{python}", "-m", "unittest", "discover", "-s", "tests", "-v"],
      "timeoutSeconds": 120
    },
    {
      "id": "lint",
      "category": "lint",
      "argv": ["npm", "run", "lint"],
      "cwd": "frontend",
      "timeoutSeconds": 60
    }
  ]
}
```

Use actual documented project commands. Supported categories are `build`, `lint`, `typecheck`,
`test`, `security`, and `acceptance`. Checks require unique IDs and an argument list. Optional
`required: false` allows an unselected check to remain unrun without blocking completeness, but any
executed failure still fails the run. The default timeout is 120 seconds, with a maximum of 86400.
`requiredCategories` defaults to `test`; an empty check list cannot satisfy it. All paths in the
manifest must resolve within the project. Shell command strings and unknown fields are rejected.

The runner does not infer success criteria from prose or automatically execute package scripts.
Discovery lists candidate commands and sources for review. Missing package-manager evidence leaves
the candidate command unresolved. It does not install dependencies or retry failed tests.

Execution uses argument arrays without an implicit shell. On Windows, npm/pnpm/yarn shims are
translated to their installed Node entrypoints. Other shell scripts need an explicit interpreter,
for example PowerShell with a script file, in the reviewed manifest.

Exit codes: `0` for a passed execution or successful discovery; `1` for an executed check failure,
timeout, or launch error; `2` for an invalid request or incomplete execution. Read `mode` and
`status` in the JSON report: discovery has no execution verdict. Invalid plans are rejected before
any check executes. Focused selections report required unselected checks as `not_run`.

Reports contain UTC time, commit, dirty state, and source fingerprints before/after, check arguments, working directory,
duration, exit code, and bounded stdout/stderr tails. Output is limited to 32 KiB per stream and
marked when truncated. The runner masks common token patterns and values of environment variables
with credential-like names; `--redact-env NAME` adds a variable. Keep credentials in environment
variables, not arguments. Redaction is best-effort; do not publish unreviewed output or raw traces.

Store reports outside the project, for example under the operating system's temporary directory or
a private evidence directory. Commands run with the caller's filesystem, network, and account
permissions. This runner is not a sandbox; timeouts attempt process-tree termination. Commands that
launch detached services or retain inherited output pipes need their own explicit cleanup.
