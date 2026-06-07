---
name: codex-harness-setup
description: design, audit, and right-size repo-local codex harnesses and coding-agent scaffolding. use when the user asks to create, update, or review agents.md, docs/ai/*, validation guidance, review gates, subagent policy, calibration, known-failure notes, or agent workflow controls for a repository. do not use for ordinary coding, debugging, generic code review, or security review unless the task is specifically about agent scaffolding or harness design.
---

# Codex Harness Setup

## Principle

Set up the smallest repo-local harness that makes Codex or another coding agent reliable for the current repository. Do not maximize process. Maximize safe, reviewable, reversible progress.

A harness is repository scaffolding for agent work: `AGENTS.md`, `docs/ai/*`, validation guidance, review gates, safety notes, evidence paths, subagent policy, calibration tasks, known-failure notes, lightweight scripts, or cleanup rules.

This skill is not a general coding, debugging, code-review, or security-review skill. Use it only when the task is about designing, auditing, or tuning agent scaffolding or repository-local harnesses.

## Input Contract

Before editing, identify:

- repository type and primary language/framework,
- existing agent instruction files,
- existing validation commands,
- CI/hooks/review gates already present,
- known agent failures or user pain points,
- modules or risk areas where Codex should ask more or fewer clarifying questions,
- whether the user wants audit-only, setup, targeted upgrade, or recovery.

If repository files are unavailable, produce copyable recommendations instead of pretending to inspect the repo.

## Progressive Loading

Keep this entrypoint as the control plane. Load details only when needed:

- For cycle sizing, native capability checks, harness fit, enforcement levels, and effectiveness reviews, use [references/decision-gates.md](references/decision-gates.md).
- For choosing specific harnesses, use [references/harness-catalog.md](references/harness-catalog.md).
- For ephemeral subagents, assignment prompts, and reporting rules, use [references/operating-model.md](references/operating-model.md).
- For security, code, UI, data, release, TDD, and harness review checklists, use [references/review-checklists.md](references/review-checklists.md).
- For `AGENTS.md`, `docs/ai/*`, and script templates, use [references/file-templates.md](references/file-templates.md).
- For golden-task calibration and harness scorecards, use [references/calibration.md](references/calibration.md).
- For module-specific ambiguity levels, interview policy, and ask/decide boundaries, use [references/ambiguity-profile.md](references/ambiguity-profile.md).
- For checking applied harness files for common mistakes, use `scripts/check_harness.py` when script execution is available.

Do not load or apply every reference for every task.

## Operating Modes

Choose one mode before editing:

1. **Audit only**: inspect and report missing, excessive, stale, duplicated, or mis-sized harnesses. Do not edit files.
2. **Setup**: create or update repo-local harness files and scripts.
3. **Targeted upgrade**: tune one specific harness such as TDD, security, review, UI evidence, data safety, release checks, cycle sizing, calibration, or subagent policy.
4. **Recovery**: after repeated agent failure, unreadable diffs, missed bugs, failed validation, or user feedback that the process is too heavy/light, identify the missing or excessive harness and make the smallest correction.
5. **Ambiguity profiling**: map project modules or risk areas to 1-5 ambiguity levels so agents ask only the questions that materially reduce risk.

If the user does not specify a mode, use **Setup** when repository files are editable; otherwise use **Audit only** and provide copyable content.

## Minimal Workflow

### 1. Inspect current state

Inspect enough to satisfy the Input Contract. Look for `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`, `CLAUDE.md`, README, docs, package scripts, hooks, PR templates, workflows, and relevant issue/report history.

### 2. Run native capability and overlap checks

Before adding a rule, ask whether Codex already does it reliably, existing scripts/CI/hooks already enforce it, or a stronger project mechanism already exists. Keep only rules that add a project-specific decision, constraint, source of truth, evidence requirement, escalation trigger, or known-failure prevention.

### 3. Size the work cycle

Classify the work as **single-pass**, **mini-cycle**, **staged-cycle**, or **high-risk-cycle** before implementation. Do not optimize for one-pass completion; optimize for the largest safe, reviewable, reversible unit of progress. Split before editing when the expected diff would be hard for a human to review.

When user-interview friction is part of the problem, also classify ambiguity from 1-5: lower values require more confirmation before edits, higher values let the agent infer more from repository context.

### 4. Select only necessary harnesses

Classify project type and primary risks, then choose the smallest harness set tied to those risks. Explicitly skip important harnesses that are not needed now. Every selected harness must pay rent by reducing risk, improving reviewability, improving evidence, encoding project-specific correctness, or addressing a known failure mode.

### 5. Decide whether subagents are worth the overhead

Default to one agent for low-risk work. Use short-lived read-only reviewers only when independent review materially improves quality: Test/TDD, Security, Code, UI/Visual, Data, or Release. Preserve only concise reports, evidence paths, and decisions.

### 6. Implement with the lightest effective enforcement

Prefer repo-local, versioned artifacts. Keep `AGENTS.md` short and link to `docs/ai/*` rather than copying the whole project. Start with advisory docs and checklists; promote to scripts, hooks, CI gates, or mandatory human approval only when repeated evidence justifies it.

Do not add heavy dependencies, CI gates, migrations, destructive scripts, production config, or release blockers without user approval.

### 7. Prevent placeholder leakage

When using templates, never leave bracket placeholders such as `[paths]`, `[command]`, or `[example]` in final repository files. Replace them with repo-specific content, mark them as `unknown` with a reason, or delete the section.

### 8. Validate, calibrate, and close out

Run validation that matches the edit: markdown/lint checks, shell syntax checks, script dry-runs, or existing fast validation only when relevant. If script execution is available, run `scripts/check_harness.py <repo-root>` after creating or updating `AGENTS.md` or `docs/ai/*`.

For a new or materially changed harness set, propose or run small calibration tasks before treating it as stable. Record whether harnesses were right-sized after meaningful cycles or failures.

## Example Uses

### Example 1: New repo setup

User: "Set up Codex instructions for this repository."
Mode: Setup.
Do:

- inspect README, package scripts, existing CI, and existing agent instructions,
- create only `AGENTS.md` plus `docs/ai/validation.md` if useful,
- avoid adding security, UI, data, or release harnesses unless risks are present.

### Example 2: Too much process

User: "Codex keeps producing huge reports for tiny changes."
Mode: Recovery.
Do:

- audit `AGENTS.md` and `docs/ai/*`,
- remove generic planning/report rules,
- keep only task-specific escalation triggers,
- summarize retired rules and expected behavior change.

### Example 3: High-risk migration

User: "Tune the harness before Codex edits a migration."
Mode: Targeted upgrade.
Do:

- activate data-safety, review-gates, validation, and human approval points,
- require dry-run/rollback evidence,
- do not run destructive operations without explicit approval.

## Default Repo Layout

Create only files that are useful for the repository. Usually start with `AGENTS.md`, then add focused `docs/ai/*` files such as `validation.md`, `harness-profile.md`, or `project-map.md` only when they reduce a real future-agent risk.

Use existing project conventions and owner files when present. Merge and shorten stale or duplicate rules instead of creating competing sources of truth. Load [references/file-templates.md](references/file-templates.md) for concrete file templates, including optional ambiguity profiles.

## Output Format

After meaningful work, report only what helps the user review the harness: summary, mode, files reviewed or changed, key decisions, validation, and remaining risks. Compact or omit sections for small tasks.

For low-risk single-pass work, use the final response only. Create persistent report files only for staged/high-risk work, multi-agent work, durable evidence, decisions that affect future harness selection, or explicit user requests.

## Anti-Patterns

Avoid:

- One huge `AGENTS.md` that tries to teach the whole project.
- Requiring verbose goals, long plans, subagents, and report files for tiny changes.
- Enabling TDD, security, UI evidence, release checks, and observability for every change.
- Adding rules that duplicate Codex defaults, CI, scripts, hooks, or framework conventions without adding a project-specific decision or evidence requirement.
- Creating process docs that no future agent, command, review habit, or human will use.
- Treating a packaged skill or new harness as proven before representative calibration.
- Letting one agent implement and independently approve high-risk work without a separate review path.
- Adding new rules without retiring stale, conflicting, or low-signal old rules.
