---
name: repo-harness-tuner
description: Continuously analyze, diagnose, design, restructure, and evaluate repo-local Codex harness design, including AGENTS.md, Docs/AI/*, validation guidance, target files, human-involvement policy, prompt templates, and visible/background worker policy. Use when the user asks whether a project has the right Codex harness, wants to bootstrap a first project, or wants to reduce/strengthen project-specific agent process over time.
---

# Repo Harness Tuner

## Purpose

Use this skill as the front-end for the repo harness improvement loop:

```text
Analyze -> Diagnose -> Design -> Restructure -> Evaluate
```

This plugin includes `codex-harness-setup`. Use `repo-harness-tuner` to gather evidence and decide what should change; use the embedded `codex-harness-setup` skill as the implementation engine when harness files need to be created, shortened, split, or tuned.

## Capabilities

- Scan the current repository for `AGENTS.md`, `Docs/AI/*`, `docs/ai/*`, `Docs/SKILLS.md`, package scripts, and common project docs.
- Compare installed capabilities against what the current repo actually documents or needs.
- Score harness readiness and recommend concrete tuning changes.
- Detect the project type and apply a lightweight preset for Unity, Godot, Vite/Node, Node, Python, docs-only, or unknown projects.
- Generate a concrete harness design with target files, worker architecture, evaluation steps, and the next review trigger.
- Recommend phase-aware harness review cadence.
- Detect drift between `package.json` scripts and validation docs.
- Detect overbroad process rules that require full QA, detailed reports, visible chats, or plans for every small task.
- Detect human-involvement enforcement gaps where ask-before-edit rules are missing or not linked from the repo entrypoint.
- Generate a human-involvement and worker visibility matrix.
- Emit a diagnosis-based `codex-harness-setup` prompt.
- Write `Docs/AI/harness-status.md` only when the user explicitly asks for a durable status record.
- Generate harness-design prompts for `codex-harness-setup`.
- Explain whether parallel work should be hidden/backgrounded or exposed as visible user-facing chats.
- List installed skills and plugins only as supporting context for harness diagnosis.
- Apply harness restructuring through the embedded `codex-harness-setup` skill when the user asks for changes.

## Improvement Loop

1. **Analyze**: inspect project type, existing harness files, package scripts, CI/hooks, reports, and coordination docs.
2. **Diagnose**: run `scripts/console.py diagnose --repo <repo-root> --phase <phase>` and review readiness, drift, overbroad process, cadence, and human-involvement matrix.
3. **Design**: run `scripts/console.py design --repo <repo-root> --phase <phase>` or inspect `harness_design` from diagnosis to choose target files, worker visibility, validation evidence, and next review timing.
4. **Restructure**: invoke the embedded `codex-harness-setup` skill to make the smallest useful change. Prefer `AGENTS.md`, `Docs/AI/harness-profile.md`, and `Docs/AI/validation.md` for first setup.
5. **Evaluate**: run the embedded `codex-harness-setup/scripts/check_harness.py <repo-root>` when harness files changed, then rerun `diagnose`. Write `Docs/AI/harness-status.md` or `Docs/AI/harness-design-plan.md` only when durable status is useful or requested.

## Recommended Workflow

1. For a combined diagnosis overview, run `scripts/console.py overview --repo <repo-root>` from the plugin root.
2. For harness scoring and tuning recommendations, run `scripts/console.py diagnose --repo <repo-root> --phase <phase>`.
   - Add `--emit-prompt` to generate a `codex-harness-setup` prompt from the diagnosis.
   - Add `--write-status` only when the user wants a durable `Docs/AI/harness-status.md` record.
   - Add `--write-plan` only when the user wants a durable `Docs/AI/harness-design-plan.md` record.
3. For the next design only, run `scripts/console.py design --repo <repo-root> --phase <phase>`.
4. For installed skills, run `scripts/console.py skills --json`.
5. For installed plugins, run `scripts/console.py plugins --json`.
6. For the active repo, run `scripts/console.py repo --repo <repo-root> --json`.
7. For a setup prompt, run `scripts/console.py prompt --repo-type "<type>" --mode Setup --human-involvement 3`.
8. When the user wants actual repo harness changes, invoke the embedded `codex-harness-setup` after inspection.

## Project Phases

- `new-project`: initial harness bootstrap. Tune now, after the first working feature, then every 3-5 meaningful cycles.
- `prototype`: fast iteration. Tune after structure, validation, or product direction changes.
- `active-development`: regular work. Do a lightweight fit check each task and short review every 3-5 meaningful cycles.
- `pre-release`: QA/release confidence. Tune before release candidates and after QA failures.
- `maintenance`: stable work. Tune monthly, after repeated mistakes, or before high-risk changes.
- `high-risk`: migration, destructive, release, data, secrets, or difficult rollback. Tune before planning, before implementation, and after validation.

## Human Involvement

The user-facing control is human involvement, from 1 to 5:

- Human involvement 1: Codex explores autonomously unless a protected area or explicit approval trigger appears.
- Human involvement 2: Codex proceeds from existing patterns and mentions assumptions in closeout.
- Human involvement 3: Codex infers from repo context, but asks before hard-to-reverse or user-visible direction changes.
- Human involvement 4: Codex asks 1-3 focused questions before edits unless a named repo source of truth already answers them.
- Human involvement 5: Codex stops and asks for explicit approval before edits.

Internally, the repo harness can store this as ask-before rules. Any `Ask before` row in `Docs/AI/ambiguity-profile.md` is a stop condition before file edits.

## Parallel Work Visibility Policy

`codex-harness-setup` currently decides when subagents are worth the overhead, but it does not fully encode whether those workers should run as hidden background tasks or as visible chats.

Use this policy in generated prompts:

- Use visible chats for product decisions, scope negotiation, roadmap changes, QA reports the user must inspect, or specialist work where the user benefits from seeing the thread.
- Use background/read-only workers for independent code review, test review, security review, static audits, or repo scans where only the final findings matter.
- Use a single agent for small changes, docs edits, narrow validation fixes, or low-risk content corrections.
- Persist reports only for staged/high-risk cycles, multi-agent handoffs, QA evidence, or decisions future agents must reuse.

## Safety

- Treat install, uninstall, enable, disable, and marketplace edits as explicit actions. Prefer inspection and generated instructions unless the user asks for changes.
- Do not delete skills, plugins, marketplace entries, repo docs, or harness files without direct user approval.
- Do not show secrets from environment files, credentials, logs, or private configuration.

## Output

For scans, report:

- what was inspected,
- harness readiness score,
- missing, stale, or excessive harness rules,
- drift between repo scripts and validation docs,
- overbroad process rules and recommended demotions,
- human-involvement enforcement gaps,
- target files and reasons from the harness design,
- worker architecture and evaluation steps,
- recommended review cadence,
- human-involvement and visibility matrix,
- suggested next action,
- exact prompt text when requested.
