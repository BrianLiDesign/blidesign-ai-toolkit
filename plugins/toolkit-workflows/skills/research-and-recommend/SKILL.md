---
name: research-and-recommend
description: Research an open question or unfamiliar implementation, compare viable approaches against the user's constraints, and recommend the best fit using primary sources and applicable standards. Use when the user wants evidence-backed options and a recommendation; a single documentation lookup belongs to find-docs.
---

# Research and recommend

Turn an uncertain question into a defensible decision and a practical next step. Scale the research
to the decision's cost, reversibility, and uncertainty; keep small questions concise.

## Frame the decision

Identify the desired outcome, constraints, existing environment, and criteria that would make one
approach preferable. Inspect available project context before asking the user for facts. Ask only
when a missing preference or constraint could materially change the recommendation; otherwise state
reasonable assumptions and proceed. Preserve explicit choices and previously authorized work.

## Gather evidence and alternatives

- Search for materially different approaches before selecting a favorite. Normally investigate
  two to four credible candidates; expand when the decision warrants it. Include the existing
  approach or a simpler solution when viable. Explain if only one candidate meets the constraints
  rather than inventing alternatives to fill a quota.
- Use search to discover candidates, then verify decision-driving claims at their primary sources:
  official documentation, specifications, standards bodies, original studies, source code, or
  first-party measurements. Secondary sources can surface experience and alternatives; label their
  limitations and trace factual claims to the owner where possible. Open the underlying sources
  rather than relying on search snippets.
- Identify standards that actually govern the question. Check their edition, status, scope, and
  applicability. Distinguish mandatory requirements from recommendations and common practice.
  State when authoritative text is inaccessible or no relevant standard was found.
- For library, framework, SDK, API, CLI, or cloud-service details, follow
  [find-docs](../find-docs/SKILL.md) for current documentation. For other subjects, use the available
  search and browsing tools directly. Verify time-sensitive claims and version compatibility;
  report access failures and the resulting evidence gaps.
- Look for evidence that could disqualify the leading candidate, including maintenance status,
  limitations, and contradictory findings. Cite the source beside each decisive claim. Distinguish
  verified facts, source claims, assumptions, and your own judgment.

Research is sufficient when the viable candidates have been assessed against the decisive criteria
and remaining unknowns either cannot change the choice or are explicitly identified as blockers.
If an important uncertainty remains, recommend the smallest useful experiment or information check
instead of presenting a tentative choice as settled.

## Compare and recommend

Compare candidates using the user's priorities. Cover relevant tradeoffs such as correctness,
standards compliance, compatibility, effort, operating cost, maintainability, performance, and risk.
Use a compact table when it makes the differences clearer. Explain any scoring weights or estimates;
avoid numerical precision that the evidence cannot support. Vendor benchmarks establish behavior
only under their stated conditions; identify what still needs local validation.

Recommend one best fit for the stated context, with its decisive advantages and meaningful costs.
Explain why the strongest alternatives lose here and what changed conditions would favor them.
Give a confidence level with its evidence basis and identify any uncertainty that could reverse
the recommendation. A conditional recommendation is appropriate when a decisive fact is missing.

## Deliver and continue within scope

Lead with the recommendation, then provide the decision criteria, alternatives and tradeoffs,
supporting sources, and material unknowns. End with an implementation outline or concrete next
step, including how to validate the choice. Match detail to the question; avoid forcing a lengthy
report on a small decision.

Answer in chat unless the user requests a saved artifact or the project requires one; follow its
existing research-note convention when saving. Research alone does not authorize implementation
or external changes. When implementation is already requested, continue with the selected approach
within that authorization after presenting the rationale, asking only for unresolved decisions
that materially affect the work.
