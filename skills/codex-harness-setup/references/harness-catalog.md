# Harness Catalog

Use this catalog to choose the smallest sufficient harness. Pick only harnesses tied to real repository and task risks.

## Contents

- Baseline Harness
- Native Capability and Overlap Harness
- Cycle Sizing Harness
- Planning Harness
- TDD and Regression Harness
- Security Harness
- Code Review Harness
- UI and Visual Evidence Harness
- Data Safety Harness
- Observability and Reliability Harness
- Release Harness
- Ephemeral Subagent Harness
- Ambiguity Profile Harness
- Calibration Harness
- Entropy and Cleanup Harness

## Baseline Harness

Use for almost every active code repository, but keep it short.

Signals:
- No `AGENTS.md` or existing agent instructions are stale, huge, missing, or contradictory.
- Codex repeatedly asks where files live, which commands to run, or what not to edit.

Create or update:
- `AGENTS.md` as a short table of contents and rule entrypoint.
- `docs/ai/harness-profile.md` for project-specific always-on and usually-off harnesses.
- `docs/ai/project-map.md` for architecture, important paths, generated files, and ownership.
- `docs/ai/validation.md` for common commands and when to use each one.

Avoid:
- Long project history, style essays, copied README content, or generic agent advice.
- Commands that are not known to work.

## Native Capability and Overlap Harness

Use when the project has accumulated generic rules that may duplicate Codex defaults, CI, or existing tools.

Signals:
- `AGENTS.md` or docs contain generic advice such as "plan first", "run tests", or "summarize changes" without task-specific triggers.
- Multiple harnesses require the same evidence.
- Agents spend more time following process than reducing risk.
- Users report that Codex already does a requested step without the harness.

Create or update:
- `docs/ai/harness-profile.md` with default-agent-loop assumptions.
- A short overlap note listing which checks are already enforced by scripts, hooks, CI, or platform behavior.

Default rule:
- Keep only rules that change decisions, constraints, evidence, escalation, or project-specific source-of-truth lookup.

Skip when:
- The repo has no agent instructions yet or the first setup is intentionally minimal.

## Cycle Sizing Harness

Use when Codex tends to return huge diffs, mix unrelated refactors with feature work, or attempt final delivery before review.

Create or update:
- `AGENTS.md` with the cycle sizing gate.
- `docs/ai/harness-profile.md` with project-specific reviewable-diff limits.

Default rule:
- Optimize for the largest safe, reviewable, reversible unit of progress, not for one-pass completion.

Skip when:
- The project only uses the skill for small, low-risk one-shot edits.

## Planning Harness

Use when scope is unclear, feature work spans multiple systems, product judgment matters, or the next step needs human approval.

Create or update:
- `docs/ai/planning.md` with plan-first rules, acceptance criteria format, scope/non-scope, decision log guidance, and stop/continue conditions.
- Optional `docs/plans/` convention for larger work.

Keep light when:
- The task is a small, well-contained edit.

## TDD and Regression Harness

Use when behavior may change.

Signals:
- Bug fix, state machine, parser, calculations, business rules, API contract, persistence, concurrency, permissions, or prior regression.

Create or update:
- `docs/ai/testing.md` or `docs/ai/validation.md` with test-first guidance.
- Regression reproduction instructions.
- Focused retest command list.

Default rule:
- Prefer a failing test, reproduction, fixture, or smoke path before implementation.
- If test-first is impractical, require an explicit reason and an alternative validation path.

Skip or keep light for:
- Copy changes, docs-only changes, minor styling, throwaway prototypes.

## Security Harness

Use when the work touches trust boundaries.

Signals:
- Auth, authorization, sessions, secrets, credentials, user data, payments, uploads/downloads, file paths, URLs, shell commands, dependency changes, CI config, telemetry/logging of sensitive fields.

Create or update:
- `docs/ai/security.md` with guardrails and review checklist.
- Secret-handling rules in `AGENTS.md`.
- Optional secret scanning or dependency audit instructions when already available.

Default rules:
- Never expose secrets in logs, tests, screenshots, reports, or prompts.
- Validate untrusted input at boundaries.
- Preserve least privilege and existing permission checks.
- Treat dependency, CI, and config changes as security-sensitive.

Skip for:
- Pure docs, local-only comments, or isolated UI copy with no data handling.

## Code Review Harness

Use for shared or high-blast-radius changes.

Signals:
- Public APIs, shared utilities, architecture layers, migrations, performance-sensitive paths, concurrency, framework upgrades, large refactors.

Create or update:
- `docs/ai/review-gates.md`.
- PR checklist or reviewer prompt.

Review focus:
- Scope discipline, human reviewability, readability, test evidence, edge cases, contracts, backward compatibility, error handling, observability, performance, maintainability.

Skip or keep light for:
- Small isolated changes with clear tests.

## UI and Visual Evidence Harness

Use for user-facing UI, navigation, layout, accessibility, browser/mobile flows, visual assets, or interactive presentation.

Signals:
- Layout, rendering, user flow, keyboard/focus behavior, responsive behavior, screenshots, animation, canvas/game scene, or visual regression risk.

Create or update:
- `docs/ai/ui-evidence.md`.
- Browser smoke/capture commands if they already exist or are easy to add.

Default rules:
- Capture evidence that proves the acceptance criteria, not just a pretty default state.
- If capture fails, distinguish environment blocker from product blocker.

Skip for:
- Backend-only, docs-only, or nonvisual code changes.

## Data Safety Harness

Use for persisted data changes.

Signals:
- Migrations, schema changes, destructive operations, ETL, imports/exports, backfills, data repair, retention, or irreversible transformations.

Create or update:
- `docs/ai/data-safety.md`.
- Dry-run commands, rollback expectations, fixture data, before/after counts.

Default rules:
- No destructive operation without explicit user approval.
- Prefer dry-run and backup/rollback notes.
- Record assumptions about idempotency and retry safety.

Skip for:
- Code-only changes that do not touch persistence or data transformations.

## Observability and Reliability Harness

Use for services, incidents, performance, background jobs, distributed systems, or reliability goals.

Create or update:
- `docs/ai/observability.md` with logs, metrics, traces, dashboards, local runbooks, performance thresholds, and evidence capture instructions.

Skip for:
- Offline libraries or simple scripts unless performance/reliability is the task.

## Release Harness

Use for packaging, deployment, signing, publishing, store submissions, versioning, or production rollout.

Create or update:
- `docs/ai/release.md`.
- Release checklist, version bump rules, artifact validation, rollback notes.

Skip for:
- Pre-merge implementation work with no packaging or deployment impact.

## Ephemeral Subagent Harness

Use when independent review is worth the overhead.

Signals:
- High-risk code where the implementer should not self-approve.
- Multiple distinct risk domains: security plus data, UI plus backend, release plus migration.
- The user has access to thread/task tooling that can spawn separate workers.

Create or update:
- `docs/ai/subagents.md` or a section in `harness-profile.md`.
- Role-specific prompts, read-only defaults, report paths, and completion rules.

Skip for:
- Low-risk single-pass work.
- Environments where no separate agent/thread mechanism exists; instead produce a reviewer checklist.

## Ambiguity Profile Harness

Use when the repo needs different ask-vs-infer behavior across modules, risk areas, or task types.

Signals:
- Users complain that agents ask too many questions for routine work.
- Users complain that agents make assumptions in preference-heavy or high-risk areas.
- Different modules clearly need different confirmation levels.
- The user asks for ambiguity levels, interview budgets, or module-specific autonomy.

Create or update:
- `docs/ai/ambiguity-profile.md` with default ambiguity, module rows, risk overrides, ask-before boundaries, agent-may-decide boundaries, and calibration notes.

Default rule:
- Use ambiguity 3 globally unless repo evidence or user preference says otherwise.
- Lower ambiguity for irreversible, data, security, release, payment, permission, or public contract risks.
- Raise ambiguity for low-risk refactors, internal tools, prototypes, and exploration.

Skip when:
- One sentence in `AGENTS.md` is enough.
- The repo has no stable module or risk boundaries yet.
- The user wants a one-off task, not durable agent behavior.

## Calibration Harness

Use after creating or materially changing harnesses, or when the user asks whether the harness set is appropriate.

Signals:
- New skill or repo harness was installed.
- Harnesses feel too heavy or too light.
- Codex repeatedly bypasses, overuses, or misclassifies harnesses.
- A regression, security issue, unreadable diff, or release failure escaped the current process.

Create or update:
- `docs/ai/harness-calibration.md` with representative tasks, expected harnesses, actual behavior, and adjustments.
- `docs/ai/known-failures.md` when calibration is based on repeated or high-cost failures.

Default rule:
- Test the harness with at least one low-risk task and one risk-bearing task before calling it stable.

Skip when:
- The setup is a disposable prototype or the user only wants a one-off advisory audit.

## Entropy and Cleanup Harness

Use when agent work causes drift, duplicated patterns, stale docs, or recurring style issues.

Create or update:
- `docs/ai/cleanup.md`, `docs/ai/known-failures.md`, or a quality score doc.
- Lightweight recurring checks for stale docs, duplicate utilities, overlarge files, or architectural boundary violations.

Skip for:
- Early prototypes where rules would change immediately.
