# Gemini skills: official support, formats, and recommendations

Research date: 2026-09-18

Scope: current first-party Google documentation and Google-owned source repositories for Gemini CLI Agent Skills and Gemini Apps Gems. This note does not assess third-party skill marketplaces.

## Executive findings

- **Gemini CLI now has native Agent Skills support.** A skill is a directory containing a required `SKILL.md`; optional `scripts/`, `references/`, and `assets/` directories are supported. This is the same portable Agent Skills shape already used by this repository. [Google: Creating Agent Skills](https://geminicli.com/docs/cli/creating-skills/)
- **The portable `.agents/skills/` path is explicitly supported.** Gemini CLI discovers user skills under `~/.gemini/skills/` or `~/.agents/skills/`, and workspace skills under `.gemini/skills/` or `.agents/skills/`. Workspace skills have higher precedence than user skills; user skills have higher precedence than extension and built-in skills. [Google: Managing Agent Skills](https://geminicli.com/docs/cli/using-agent-skills/)
- **Gemini Apps Gems are a separate customization surface.** A Gem is created in the web app with instructions and optional Knowledge files. Google recommends covering persona, task, context, and output format. The official Gem guide does not describe importing or executing a `SKILL.md` directory. [Google: Tips for creating custom Gems](https://support.google.com/gemini/answer/15235603?hl=en)
- **Do not conflate `GEMINI.md`, custom commands, extensions, and skills.** They solve different problems: always-on context, prompt shortcuts, packaged integrations, and on-demand procedures respectively.

## Gemini CLI terminology and compatibility

### Agent Skills

Gemini CLI describes Agent Skills as specialized expertise that is discovered from metadata and activated on demand. The model initially sees a skill's `name` and `description`; after a match it calls `activate_skill` and asks the user for permission before accessing the skill's full instructions and resources. [Google: Managing Agent Skills](https://geminicli.com/docs/cli/using-agent-skills/) [Google: activate_skill](https://geminicli.com/docs/tools/activate-skill/)

Required layout:

```text
skill-name/
├── SKILL.md       # required YAML frontmatter plus Markdown instructions
├── scripts/       # optional deterministic tools
├── references/    # optional detailed documentation
└── assets/        # optional templates and output resources
```

`SKILL.md` must start with YAML frontmatter containing `name` and `description`. Google calls the description critical because it controls discovery and activation. Gemini CLI explicitly documents `.agents/skills/` as an interoperability alias for tools following the Agent Skills standard. [Google: Creating Agent Skills](https://geminicli.com/docs/cli/creating-skills/)

Discovery and installation:

| Scope | Discovery path | Intended use |
| --- | --- | --- |
| User | `~/.gemini/skills/` or `~/.agents/skills/` | Across projects for the current user |
| Workspace | `.gemini/skills/` or `.agents/skills/` | Project-specific and shareable in version control |
| Extension | `<extension>/skills/<skill-name>/SKILL.md` | Distributed as part of a broader Gemini CLI extension |

Gemini CLI can install a skill repository or local `.skill` package with `gemini skills install <url-or-path>`; `--scope workspace` limits installation to the current project. `gemini skills link <path>` is intended for local development. In-session management includes `/skills list`, `/skills reload`, enable, and disable. [Google: Managing Agent Skills](https://geminicli.com/docs/cli/using-agent-skills/)

**Compatibility conclusion:** this repository's portable `SKILL.md` directories can target Gemini CLI without a Gemini-specific rewrite when they use the documented `name`/`description` frontmatter and ordinary `scripts/`, `references/`, and `assets/` layout. For cross-agent distribution, `.agents/skills/` is the most direct documented Gemini-compatible destination. This is an inference from Google's explicit alias support, not a claim that every host interprets every instruction identically.

### `GEMINI.md`

`GEMINI.md` provides persistent hierarchical context rather than on-demand procedural expertise. Global context lives at `~/.gemini/GEMINI.md`; project and subdirectory files can add more specific context. Gemini CLI concatenates relevant context into prompts, supports `@file.md` imports, and provides `/memory show` and `/memory reload` to inspect or refresh effective context. [Google: Provide context with GEMINI.md](https://geminicli.com/docs/cli/gemini-md/)

Recommended boundary:

- Put durable repository facts, conventions, and broad guardrails in `GEMINI.md` or a configured `AGENTS.md`.
- Put repeatable, task-triggered procedures and supporting resources in `SKILL.md`.

### Custom commands

Custom commands are reusable prompt shortcuts, not skills. Gemini CLI loads TOML files from `~/.gemini/commands/` and `<project>/.gemini/commands/`; project commands override same-named user commands. Commands can substitute arguments, inject files with `@{...}`, and inject shell output with `!{...}`. Shell execution requires confirmation. [Google: Custom commands](https://geminicli.com/docs/cli/custom-commands/)

Use a custom command when the desired behavior is explicitly invoked as a shortcut and does not need autonomous semantic discovery.

### Extensions and MCP

Extensions are broader installable packages that can bundle context, MCP servers, custom commands, hooks, subagents, and skills. An extension skill goes under `skills/<skill-name>/SKILL.md`. Extension manifests use `gemini-extension.json`; custom commands go under `commands/`, and hooks under `hooks/hooks.json`. [Google: Extension reference](https://geminicli.com/docs/extensions/reference/)

Use an extension or MCP server when the capability needs tools, external services, authentication, or a multi-component distribution rather than instructions alone.

## Gemini Apps Gems

A classic Gem is created in the Gemini web app through **Explore Gems > New Gem**. Google recommends clear instructions covering:

1. Persona: the role and response style.
2. Task: what the Gem should do.
3. Context: background, constraints, and assumptions.
4. Format: the desired response structure.

Knowledge files can be uploaded from the device or selected from Google Drive. Previewing does not save the Gem; the user must explicitly save it. [Google: Tips for creating custom Gems](https://support.google.com/gemini/answer/15235603?hl=en)

There is no documented `SKILL.md` install path for classic Gems. Therefore, translate a CLI skill into concise Gem instructions and selected knowledge files rather than claiming direct compatibility.

## Recommended skill portfolio

Google's design guidance favors focused, non-overlapping skills over a large catalog of generic personas. For a software-development workflow, the following small set is a strong starting point. The prioritization is an inference from Google's official best practices and the repository's domain, not an official Google ranking.

1. **Code review** — a concrete checklist for correctness, security, portability, tests, and repository standards.
2. **Security audit** — dependency/configuration review, secret detection guidance, permission checks, and safe escalation boundaries.
3. **Bug diagnosis** — an evidence-first reproduce, isolate, test-hypothesis, and report loop.
4. **Test-driven implementation** — red/green/refactor plus the repository's required verification commands.
5. **Current documentation research** — require primary/current sources for volatile APIs and record citations.
6. **Release/marketplace maintenance** — repository-specific packaging, provenance, portability, and validation workflow.
7. **Portable installation/status** — inspect profiles, installed plugins, skill counts, and host-specific smoke tests.

Add domain skills only when the domain is actually used:

- **Gemini API development:** Google publishes `gemini-api-dev` and `gemini-live-api-dev` in `google-gemini/gemini-skills`, designed to work with Google's Gemini Docs MCP for current API documentation. [Google: Set up your coding assistant with Gemini MCP and Skills](https://ai.google.dev/gemini-api/docs/coding-agents)
- **Firebase:** Google publishes focused Firebase skills for Auth, Firestore, Hosting, App Hosting, AI Logic, Data Connect, Crashlytics, Remote Config, and Firestore security-rule auditing. Install only the relevant modules. [Google: Firebase agent skills](https://firebase.google.com/docs/ai-assistance/agent-skills)
- **Broader tool integrations:** Google's Gemini CLI Extensions organization includes official extensions such as security, code review, Workspace, Stitch, and Conductor. Evaluate the permissions and components before installing. [Google: Gemini CLI Extensions organization](https://github.com/gemini-cli-extensions)

Avoid skills that merely restate generic model abilities, overlap heavily with another skill, or contain only a personality prompt. Put always-on personality and response preferences in persistent instructions or a Gem instead.

## Official skill-authoring guidance

Google's Agent Skill best-practices guide recommends:

- Write a specific `description` with likely user phrasing and a clear use trigger.
- Avoid overlapping descriptions.
- Keep the `SKILL.md` body focused; use progressive disclosure and move detailed material into `references/`.
- Match instruction rigidity to task fragility: flexible prose for contextual work, scripts for deterministic or error-prone work.
- Make scripts produce concise, model-friendly success and failure output.
- Put reusable templates and output resources in `assets/`.
- Never hardcode secrets; inspect third-party `SKILL.md` files and scripts before installation; keep each skill narrowly scoped.

Source: [Google: Agent Skill best practices](https://geminicli.com/docs/cli/skills-best-practices/)

## Security guidance

### Gemini CLI

- A skill can execute scripts and access files. Gemini CLI asks for consent when installing from a remote source and again when activating a skill. Review the displayed source/path before approving. [Google: Managing Agent Skills](https://geminicli.com/docs/cli/using-agent-skills/)
- Inspect third-party skill instructions and executable files before installation; do not put secrets in skill files; keep privileges and scope narrow. [Google: Agent Skill best practices](https://geminicli.com/docs/cli/skills-best-practices/)
- Folder Trust prevents untrusted workspaces from loading powerful project configuration. Safe mode ignores workspace settings and environment files, blocks extension management, forces tool confirmation, disables automatic memory loading and MCP connections, and does not load custom commands. Trust decisions are recorded in `~/.gemini/trustedFolders.json`. [Google: Trusted Folders](https://geminicli.com/docs/cli/trusted-folders/)
- Prefer sandboxing for skills that run shell commands or modify files, and preserve per-action confirmation for unfamiliar code.

### Gemini Apps Gems

- Gem instructions and uploaded knowledge are information supplied to Gemini Apps. Google's privacy notice says not to enter confidential information that the user would not want a reviewer to see or Google to use to improve services. Account and activity settings affect data handling. [Google: Gemini Apps Privacy Hub](https://support.google.com/gemini/answer/13594961?hl=en)
- When a Gem is shared, anyone with access can view its instructions and uploaded files; editors can modify or delete both. Do not share a Gem with anyone who should not see its knowledge files. [Google: Share a Gem](https://support.google.com/gemini/answer/16504957?hl=en)

## Practical recommendation for this repository

1. Reuse the existing portable skill sources and sync the chosen profile to the Gemini user-level alias `~/.agents/skills/` for cross-project availability.
2. Start with the seven focused workflow skills above, then add Gemini API or Firebase skills only when those technologies enter active work.
3. Keep repository-wide context in `AGENTS.md`/`GEMINI.md`; do not duplicate it across every skill.
4. Verify discovery with `/skills list`, reload after changes with `/skills reload`, and trigger each installed skill with a representative prompt before declaring installation successful.
5. Review scripts, secrets, external calls, and required permissions before activation or extension installation.

## Research method and limitation

The repository's Context7 lookup was attempted first, but the CLI did not return a library result after repeated waits. To avoid relying on stale model knowledge, the findings above were verified against live Google documentation, Google Help, and Google-owned GitHub repositories. No secondary guides were used.
