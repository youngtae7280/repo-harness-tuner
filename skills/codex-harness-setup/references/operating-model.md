# Operating Model

Use this reference when a harness task needs ephemeral subagents, assignment prompts, or persistent report rules. Use `decision-gates.md` for cycle sizing and native capability checks.

## Contents

- Ephemeral Subagent Pattern
- Spawn Triggers
- Suggested Subagent Prompts
- Persistent Reports

## Ephemeral Subagent Pattern

Default to one agent for low-risk harness work. Create short-lived subagents only when separate expertise or independent review is worth the overhead.

Every subagent assignment should include:

- Name and role.
- Purpose.
- Scope and non-scope.
- Read-only or edit allowed.
- Required evidence.
- Report path or final summary format.
- Completion condition.

Reviewer subagents are read-only by default. They report risks, evidence, and recommendations; they do not silently fix files while reviewing unless explicitly assigned.

Keep only durable outputs after completion: concise report, evidence paths, decisions, and follow-up actions. Do not preserve long intermediate logs unless they are needed evidence.

## Spawn Triggers

Spawn only the roles needed for the active risk:

- **Test/TDD reviewer**: behavior change, bug fix, regression risk, weak or missing tests.
- **Security reviewer**: auth, permissions, secrets, user data, payments, file/URL/path handling, dependency/config/CI changes, logs or telemetry risk.
- **Code reviewer**: public API, shared modules, architecture, performance, concurrency, migrations, large refactor.
- **UI/visual reviewer**: user-facing layout, flow, accessibility, responsive behavior, screenshots or captures.
- **Data reviewer**: migrations, destructive operations, ETL, imports/exports, persisted data changes.
- **Release reviewer**: packaging, deployment, signing, publishing, production rollout.

If no separate agent/thread mechanism exists, do not fake subagents. Produce a focused reviewer checklist instead.

## Suggested Subagent Prompts

### Test/TDD reviewer

```text
Role: Test/TDD reviewer.
Scope: Identify the smallest regression or reproduction evidence needed for this harness task.
Non-scope: Do not redesign the feature or perform broad optional testing.
Permissions: Read-only unless explicitly told to write tests.
Report: summarize missing tests, focused commands, and pass/fail evidence needed.
Completion: stop after the focused recommendation or test evidence is recorded.
```

### Security reviewer

```text
Role: Security reviewer.
Scope: Review only trust boundaries touched by the harness or upcoming agent work: auth, permissions, secrets, user data, dependencies, config, CI, logs, file/URL/path handling.
Non-scope: Do not perform a general security audit of unrelated systems.
Permissions: Read-only.
Report: risks, evidence, required human approvals, and skipped areas with reasons.
Completion: stop after the risk and evidence report.
```

### Code reviewer

```text
Role: Code-review harness reviewer.
Scope: Check whether review gates are right-sized for blast radius, public APIs, shared modules, architecture, performance, concurrency, generated files, migrations, and test quality.
Non-scope: Do not review unrelated product behavior.
Permissions: Read-only.
Report: gates to keep, narrow, remove, or escalate.
Completion: stop after review-gate recommendation.
```

### Data or release reviewer

```text
Role: Data/release reviewer.
Scope: Check dry-run, rollback, artifact, deployment, signing, versioning, and production rollout evidence needed for this harness.
Non-scope: Do not run destructive operations or deploy.
Permissions: Read-only unless explicitly approved.
Report: required evidence, blocked actions, approval points, and rollback expectations.
Completion: stop after readiness recommendation.
```

## Persistent Reports

Create persistent reports only when:

- the cycle is staged or high-risk,
- multiple agents or subagents are involved,
- QA/security/code review evidence must survive the thread,
- a decision changes future harness selection,
- the user explicitly asks for report files.

Prefer short paths such as:

```text
docs/ai/reports/YYYYMMDD_harness_audit.md
docs/ai/reports/YYYYMMDD_security_harness_review.md
docs/ai/reports/YYYYMMDD_calibration.md
```

Minimum fields:

- Date, mode, repository baseline if available.
- Scope and non-scope.
- Files reviewed or changed.
- Harnesses selected, skipped, added, retired, or deferred.
- Evidence and validation results.
- Human review points.
- Remaining risks and next adjustment.

For low-risk single-pass work, do not create report files. Use the final response summary only.
