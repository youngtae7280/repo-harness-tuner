# File Templates

Use these templates as copyable starting points. Adapt them to the repository, delete irrelevant sections, and do not create every file by default.

## Contents

- AGENTS.md
- docs/ai/harness-profile.md
- docs/ai/project-map.md
- docs/ai/validation.md
- docs/ai/review-gates.md
- docs/ai/security.md
- docs/ai/ui-evidence.md
- docs/ai/data-safety.md
- docs/ai/release.md
- docs/ai/known-failures.md
- docs/ai/ambiguity-profile.md
- scripts/ai/smoke.sh

## Template Use Rules

These are templates, not final repository files. Adapt them to the repository and delete irrelevant sections. When using templates, never leave bracket placeholders such as `[paths]`, `[command]`, or `[example]` in final repository files. Replace them with repo-specific content, mark them as `unknown` with a reason, or delete the section.

Do not create every file by default. Create only the files that control a real project risk or improve future agent work.

## AGENTS.md

```md
# Agent Instructions

## Start here
- Use this file as a map, not a full manual.
- Use `docs/ai/harness-profile.md` to decide whether the default agent loop is enough.
- Use `docs/ai/project-map.md` to locate systems and ownership.
- Use `docs/ai/validation.md` to choose focused validation commands.

## Default behavior
- For low-risk single-pass work, avoid verbose planning and report files.
- For staged or high-risk work, state cycle scope, non-scope, selected harnesses, required evidence, and human review points before editing.
- Prefer the smallest safe, reviewable, reversible change.

## Cycle sizing
- single-pass: small, clear, low-risk, easy to review and revert.
- mini-cycle: moderate behavior change or isolated bug fix.
- staged-cycle: unclear scope, cross-layer feature, architecture or UX judgment.
- high-risk-cycle: security, permissions, payments, user data, migrations, release, production config, public API, or destructive operations.

## Do not edit without approval
- `.env*`, secrets, credentials
- generated files: [paths]
- migrations/destructive data scripts: [paths]
- production config: [paths]
- dependencies, CI, or release gates unless the task requires it

## Required checks by risk
- Behavior or bug fix: follow `docs/ai/validation.md`.
- Auth, permissions, user data, secrets, file/URL/path handling, dependencies, or CI: follow `docs/ai/security.md`.
- Public API, shared modules, architecture, migration, or high-blast-radius change: follow `docs/ai/review-gates.md`.
- UI/visual flow: follow `docs/ai/ui-evidence.md`.
- Data/migration/destructive operation: follow `docs/ai/data-safety.md`.

## Closeout
Report changed files, validation commands/results, skipped checks with reasons, human review points, and remaining risks.
```

## docs/ai/harness-profile.md

```md
# Harness Profile

## Project risk summary
[Describe the project type and highest-cost mistakes.]

## Default agent loop
The default agent loop is enough for:
- [small docs/copy/test-only tasks]

Require an explicit plan before editing for:
- [multi-step or high-risk tasks]

Native capability assumptions:
- Codex can usually: [inspect files / infer simple goals / run obvious tests / summarize diffs]
- Repo tools already enforce: [lint / typecheck / tests / CI / hooks]
- Do not duplicate: [rules already enforced elsewhere]

## Cycle sizing defaults
- single-pass allowed for: [task types]
- mini-cycle required for: [task types]
- staged-cycle required for: [task types]
- high-risk-cycle required for: [task types]

Human review budget:
- Prefer cycles with one core behavior change and a reviewable diff.
- Split work before implementation if expected changes cross [N] files or [project-specific boundary].

## Always activate these harnesses
| Trigger | Harness | Evidence |
|---|---|---|
| [auth/roles/etc.] | Security + regression | [test/review evidence] |

## Usually skip these harnesses
| Situation | Skipped harness | Reason |
|---|---|---|
| [docs-only] | [security/ui/release] | [no trust/UI/release surface] |

## Subagent policy
Use a single agent for low-risk work.
Spawn short-lived reviewers only when independent review materially improves safety.
Reviewers are read-only by default.

## Effectiveness review cadence
- Lightweight fit check: every task.
- Short effectiveness review: every 3-5 meaningful cycles.
- Full profile review: weekly, per sprint, or after a serious missed bug.
```

## docs/ai/project-map.md

```md
# Project Map for Coding Agents

## Purpose
[One paragraph describing what this repository builds.]

## Important paths
| Path | Purpose | Notes |
|---|---|---|
| `src/` | [main source] | [architecture notes] |
| `tests/` | [tests] | [how to run focused tests] |
| `docs/` | [documentation] | [source of truth] |

## Architecture boundaries
- [Layer/module boundary]
- [Allowed dependency direction]
- [Generated code location]

## Do not edit without approval
- `.env*`, secrets, credentials
- generated files: [paths]
- migrations/destructive data scripts: [paths]
- production config: [paths]

## Common task entry points
- Bug fix: [files/docs/tests]
- Feature: [files/docs/tests]
- UI change: [files/docs/tests]
- Release: [files/docs/tests]
```

## docs/ai/validation.md

```md
# Validation Guide

## Command selection
Use focused validation first. Run broad validation only when the change has broad impact or before final integration.

| Situation | Preferred validation | Notes |
|---|---|---|
| Bug fix | [focused test command] | Prefer failing reproduction first. |
| Type/API change | [typecheck command] | Include contract tests if available. |
| UI flow | [browser/smoke command] | Capture evidence if visual behavior changed. |
| Full pre-merge | [broad command] | Run when impact is broad. |

## TDD/regression discipline
- For behavior changes and bug fixes, first create or identify a failing test, reproduction, or focused smoke check.
- If test-first is not practical, document why and choose an alternative validation.
- After fixing, rerun the focused check and summarize pass/fail evidence.

## If validation fails
- Summarize the failure.
- Decide whether it is caused by the change, environment, flake, or pre-existing issue.
- Fix owner-scoped failures when safe.
- Do not hide failing checks.
```

## docs/ai/security.md

```md
# Security Harness

Use this when a task touches auth, permissions, secrets, user data, payments, file/URL/path handling, dependencies, CI, telemetry, or logging.

## Required review
- No secrets, tokens, credentials, or personal data in logs, reports, tests, screenshots, or prompts.
- Untrusted input is validated at boundaries.
- Authorization checks are preserved or strengthened.
- File paths, URLs, shell commands, and uploads/downloads avoid injection and traversal risks.
- Dependency, CI, and config changes are treated as security-sensitive.
- Error messages do not leak sensitive implementation details.

## Closeout evidence
- Security-sensitive files changed.
- Security checks performed.
- Residual risks or required human approval.
```

## docs/ai/review-gates.md

```md
# Code Review Gates

Apply review depth based on blast radius and human review budget.

## Lightweight review
Use for small isolated changes.
- Scope stayed narrow.
- Focused validation passed or was skipped with reason.
- No unrelated formatting or opportunistic refactor.
- Diff is easy for a human to review.

## Deep review
Use for public APIs, shared modules, architecture, migrations, concurrency, performance-sensitive paths, dependency changes, or security-sensitive code.
- Edge cases and failure paths considered.
- Backward compatibility and contracts preserved.
- Test quality matches risk.
- Error handling and observability remain useful.
- Performance and complexity are acceptable.
- Security/data/release gates were activated when relevant.
```

## docs/ai/ui-evidence.md

```md
# UI and Visual Evidence

Use when user-facing layout, navigation, accessibility, rendering, visual assets, or interaction behavior changes.

## Evidence expectations
- Capture before/after screenshots or short recordings when possible.
- Exercise the user flow that proves the acceptance criteria.
- Check responsive/mobile states when relevant.
- Note accessibility concerns such as focus order, labels, contrast, and keyboard navigation when relevant.

If capture fails, state whether the blocker is environmental or product-related.
```

## docs/ai/data-safety.md

```md
# Data Safety Harness

Use for migrations, destructive operations, imports/exports, ETL, backfills, schema changes, or data repair.

## Required safeguards
- Explain the affected data and expected transformation.
- Prefer dry-run or fixture validation first.
- Record before/after counts or invariants when possible.
- Define rollback or recovery path.
- Do not run destructive operations without explicit approval.
```

## docs/ai/known-failures.md

```md
# Known Agent Failure Modes

Use this file only for repeated or high-cost failures. Keep entries short.

| Date | Failure | Missed or excessive harness | Adjustment |
|---|---|---|---|
| YYYY-MM-DD | [what happened] | [missing/overhead/stale rule] | [add/remove/change] |
```

## docs/ai/ambiguity-profile.md

Create this only when the repository needs repeatable rules for how much Codex should ask versus infer. See this skill's `references/ambiguity-profile.md` for selection guidance.

```md
# Ambiguity Profile

## Default
- Default ambiguity: 3
- User interview style: ask only questions that change direction, risk, or irreversible decisions.

## Module ambiguity
| Area | Paths / signals | Ambiguity | Ask before | Agent may decide | Evidence |
|---|---|---:|---|---|---|
| [area] | [paths or task signals] | [1-5] | [decisions requiring user input] | [safe inferred decisions] | [validation/review evidence] |

## Risk overrides
- Lower to 1 when: [destructive/data/payment/auth/release triggers]
- Lower to 2 when: [preference-heavy or public-contract triggers]
- Allow 4 when: [isolated low-risk work]
- Allow 5 when: [exploration or prototype work]

## Calibration notes
| Date | Task | Expected ambiguity | Actual behavior | Adjustment |
|---|---|---:|---|---|
| YYYY-MM-DD | [task] | [1-5] | [too many questions / too few / right] | [change] |
```

## docs/ai/harness-calibration.md

This generated repo file corresponds to the guidance in this skill's `references/calibration.md`.

```md
# Harness Calibration

Use this file after creating or materially changing agent harnesses. Keep it short.

## Golden tasks
| Task | Expected cycle size | Expected harnesses | Expected skipped harnesses | Evidence expected | Result | Adjustment |
|---|---|---|---|---|---|---|
| Low-risk task: [example] | single-pass | [light validation] | [security/data/release] | [summary/check] | [right/heavy/light] | [change] |
| Normal task: [example] | mini-cycle | [test/review] | [release/etc.] | [test evidence] | [right/heavy/light] | [change] |
| High-risk task: [example] | high-risk-cycle | [security/data/release/etc.] | [irrelevant] | [review/evidence] | [right/heavy/light] | [change] |

## Scorecard
| Harness | Signal | Cost | Adoption | Recency | Decision |
|---|---|---|---|---|---|
| [name] | [caught issues / none] | [low/med/high] | [used/ignored] | [fresh/stale] | [keep/promote/demote/retire] |
```

## Harness Selection Review output

```md
# Harness Selection Review

## Classification
- Project/task type:
- Cycle size:
- Primary risks:

## Selected harnesses
| Harness | Risk controlled | Native/tooling gap | Evidence required | Overhead |
|---|---|---|---|---|
| [name] | [risk] | [why defaults are not enough] | [command/report/capture/checklist] | [low/medium/high] |

## Skipped harnesses
| Harness | Why skipped | What would activate it |
|---|---|---|
| [name] | [reason] | [trigger] |

## Human review points
- [diff area or decision]
```

## Harness Effectiveness Review output

```md
# Harness Effectiveness Review

## Recent cycle(s)
- [cycle/task]

## Useful harnesses
- [what helped]

## Unnecessary overhead
- [what to remove or lighten]

## Missing harnesses
- [what would have reduced risk]

## Adjustments
- [add/remove/promote/demote/change]
```
