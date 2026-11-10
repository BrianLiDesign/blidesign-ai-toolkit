# Native host setup

Documentation checked 2026-11-10. Check the installed version and available native tools before use;
these examples are optional, user-managed configuration, not files installed by skill sync.
Use built-in workers first. All hosts need explicit assignment context and observed tool results.

## Codex

Ask: "Use orchestrate to split these independent tasks between two native subagents, wait for both,
and verify their combined result." Current local Codex permits spawning after a direct request or
applicable skill instruction. The harness manages creation, follow-ups, waiting, and interruption.

Optional custom agent: `.codex/agents/toolkit-worker.toml` (project) or
`~/.codex/agents/toolkit-worker.toml` (personal):

```toml
name = "toolkit-worker"
description = "Implement one coordinator-assigned task in its designated worktree."
developer_instructions = "Work only on the assigned task. Return commits, checks, and blockers. Delegate additional needs back to the coordinator."
```

Omitting model settings retains configured inheritance. Global `[agents]` settings include
`enabled` and `max_concurrent_threads_per_session` (spawned threads excluding the primary).
Custom agents inherit parent permissions and MCP servers; instructions alone do not enforce a
read-only sandbox. Create and assign implementation worktrees explicitly.

Source: [official OpenAI subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## Claude Code

Ask: "Use orchestrate with two native subagents for these independent tasks." Optional definitions
are Markdown with YAML frontmatter in `.claude/agents/` or `~/.claude/agents/`:

```markdown
---
name: toolkit-worker
description: Implement one coordinator-assigned task in its designated worktree.
model: inherit
isolation: worktree
---
Work only on the assigned task. Return commits, checks, and blockers.
Delegate additional needs back to the coordinator.
```

Check the resulting worktree's base: native isolation may branch from the default branch rather
than the parent's HEAD. Use an explicitly prepared integration-based worktree if necessary.
Agent teams remain optional and experimental, enabled separately with
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. They can change delegation behavior; verify the resulting
working directory rather than assuming subagent isolation applies. In-process mode supports ordinary
terminals; split panes require tmux or iTerm2. In-process teammates are not restored on resumption.

Sources: [subagents](https://code.claude.com/docs/en/sub-agents),
[agent teams](https://code.claude.com/docs/en/agent-teams).

## Cursor

Ask: "Use orchestrate with two subagents, each in its own isolated worktree, and integrate results
one at a time." Custom Markdown definitions live in `.cursor/agents/` or `~/.cursor/agents/`:

```markdown
---
name: toolkit-worker
description: Implement one coordinator-assigned task in its designated worktree.
model: inherit
---
Work only on the assigned task. Return commits, checks, and blockers.
Delegate additional needs back to the coordinator.
```

Subagents share the parent checkout by default; request isolation and verify both the directory and
base SHA. A clean child context needs source pointers and acceptance criteria supplied explicitly.
Cloud workers have separate environments and MCP configuration; local access does not establish
equivalent cloud access. Fall back to sequential work when the required environment is unavailable.

Source: [Cursor subagent documentation](https://cursor.com/docs/subagents).

## Installation and smoke checks

The existing development/full profile distributes this skill. Skill sync copies its entire folder;
it does not register custom agents, rewrite host configuration, or start a scheduler. A user may copy
an optional example into the chosen host's configuration after reviewing it. Avoid duplicate names
and preserve existing customization. Reload/restart as the host requires, then ask it to identify
the discovered skill and perform a harmless assignment.

Use [acceptance scenarios](acceptance.md) for live checks. Report documentation coverage separately
from file discovery, native execution, isolation, and combined verification.
