# Security CI selection

Use language-appropriate CodeQL analysis, dependency review for supported manifests/lockfiles, and
redacted secret scanning. Verify action versions against primary documentation before adding a
workflow. Pin new actions to reviewed full commit SHAs, with a version comment for maintenance.
Use `contents: read` by default and grant `security-events: write` only to the analysis job that
uploads findings. Prefer `pull_request` and protected/default-branch pushes; do not use privileged
PR triggers to run untrusted code. Automatic repository tokens are sufficient where supported;
do not introduce personal credentials into workflow files.

For this toolkit, `.github/workflows/security.yml` is the maintained concrete integration. It covers
Python, JavaScript, and GitHub Actions with CodeQL, reviews dependency changes on PRs, and scans Git
history for secrets. These tools inspect source and supported inventories; they do not certify the
security of remote MCP packages resolved at runtime. Pinned Git URLs and package-runner references
need a separate upstream/dependency review when changed.

Before reporting success, inspect the scanner findings and exact SHA. CodeQL alert availability and
dependency graph support depend on repository settings and account permissions. Gitleaks Action
requires a license for organization-owned repositories; personal repositories do not require one.
Preserve missing-access and unsupported-inventory cases as coverage limitations.

Primary sources:

- https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options
- https://github.com/actions/dependency-review-action
- https://github.com/gitleaks/gitleaks-action
- https://docs.github.com/en/actions/reference/security/secure-use
