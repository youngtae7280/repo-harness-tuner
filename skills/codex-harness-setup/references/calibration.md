# Calibration and Scorecards

Use this reference when checking whether a harness set is actually appropriate for a repository.

## When to Calibrate

Calibrate after:

- first installing a harness set,
- materially changing `AGENTS.md` or `docs/ai/`,
- repeated Codex mistakes,
- a missed regression, security issue, data issue, unreadable diff, or release failure,
- user feedback that the process feels too heavy or too light.

For stable projects, use a short calibration every 3-5 meaningful cycles and a repo-level review weekly or per sprint.

## Golden Task Set

Pick 2-4 representative tasks. Do not require all of them for every repo.

1. **Low-risk task**: docs, copy, small style, or test-only edit that should stay lightweight.
2. **Normal task**: behavior change or bug fix that should activate regression evidence.
3. **High-risk task**: security, data, release, public API, payment, permission, production config, or hard rollback risk.
4. **Known failure task**: a past agent failure, if one exists.

For each task, compare expected versus actual:

- cycle size,
- selected harnesses,
- skipped harnesses,
- evidence requested,
- subagents spawned or avoided,
- whether human review would be easy,
- whether the process was too heavy, too light, or right-sized.

Prefer audit-only or dry-run calibration unless the user explicitly wants files changed.

## Harness Scorecard

Score harnesses by evidence, not by how good they sound.

| Dimension | Keep or promote when | Demote or retire when |
|---|---|---|
| Signal | catches issues, clarifies decisions, or improves review | never changes decisions or evidence |
| Cost | cheap relative to risk | slows low-risk work or creates large reports |
| Adoption | agents consistently use it correctly | agents ignore it or misuse it |
| Recency | matches current project structure and tools | stale, duplicated, or contradictory |
| Coverage | maps to a real high-cost failure mode | covers only generic best practice |

Decisions:

- **Keep**: useful and right-sized.
- **Promote**: repeatedly useful; consider script, hook, CI, or mandatory approval.
- **Demote**: useful sometimes but too heavy; move from CI/script to checklist/advisory.
- **Retire**: stale, duplicated, or no evidence value.
- **Rewrite**: valid risk, but current rule is vague, too broad, or hard to apply.

## Overlap Test

Before adding or keeping a rule, ask:

- Is this already done by the default agent loop?
- Is it already enforced by CI, package scripts, hooks, framework conventions, or review policy?
- Does the rule tell the agent when to behave differently, or only repeat generic advice?
- Does it produce evidence a human can inspect?
- Would removing this rule materially increase risk?

Rules that fail the overlap test should be removed, narrowed, or moved to a lower enforcement level.
