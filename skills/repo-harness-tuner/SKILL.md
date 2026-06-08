---
name: repo-harness-tuner
description: Continuously analyze, diagnose, design, generate, tune, restructure, and evaluate repo-local Codex harnesses and project-specific Codex team/skill plans, including AGENTS.md, Docs/AI/*, validation guidance, target files, human-involvement policy, prompt templates, visible/background worker policy, agent roles, skill plans, orchestration docs, Codex SKILL.md drafts, minimal skill/agent recommendations, ECC seed catalog adapters, approved adapter skill installs, and continuous history/eval-based curator recommendations. Use when the user asks whether a project has the right Codex harness, wants to bootstrap a first project, wants to generate a project-specific agent team/skill plan or skill drafts, wants to recommend or install only the smallest useful skills/agents, or wants to reduce/strengthen project-specific agent process over time.
---

# Repo Harness Tuner

## Purpose

Use this skill as the front-end for the repo harness improvement loop and the team/skill factory loop.

Final product goal:

- **Factory**: generate project-specific Codex agent teams, role prompts, skill plans, and orchestration docs.
- **Engine**: analyze, diagnose, tune, evaluate, and keep those generated harnesses right-sized over time.

```text
Analyze -> Diagnose -> Design -> Factory -> Recommend Skills -> Tune -> Restructure -> Evaluate
```

This plugin includes `codex-harness-setup`. Use `repo-harness-tuner` to gather evidence and decide what should change; use the embedded `codex-harness-setup` skill as the implementation engine when harness files need to be created, shortened, split, or tuned.

## Capabilities

- Scan the current repository for `AGENTS.md`, `Docs/AI/*`, `docs/ai/*`, `Docs/SKILLS.md`, package scripts, and common project docs.
- Compare installed capabilities against what the current repo actually documents or needs.
- Score harness readiness and recommend concrete tuning changes.
- Run `next` for the friendliest read-only answer to "what should Codex do next?"
- Run `doctor` for a read-only one-command health check, loop summary, and recommended next action.
- Run `run-loop` or `loop` for the full analyze -> diagnose -> design -> factory -> tune -> evaluate -> history planning pass.
- Run `fixture-test` to validate project detection, readiness bands, next actions, eval golden tasks, factory labels, write guards, and read-only behavior across fixture repositories.
- Detect the project type and apply a lightweight preset for Unity, Godot, Vite/Node, Node, Python, Codex plugin, docs-only, or unknown projects.
- Generate a concrete harness design with target files, worker architecture, evaluation steps, and the next review trigger.
- Apply Codex plugin-specific presets for plugin.json, bundled skill validation, cachebuster, and CLI smoke-test workflows.
- Generate a Codex team/skill factory plan with `factory`, including concrete repo evidence, agent roles, planned skill files, orchestration rules, artifact inventory, update paths, and planned outputs.
- Generate repo-local factory artifacts with `factory --write-artifacts`: `Docs/AI/agent-team.md`, `Docs/AI/team-orchestration.md`, and `Docs/AI/skills/*.md`.
- Generate copyable Codex skill draft folders with `factory --write-codex-skills`: `Docs/AI/codex-skills/<skill-id>/SKILL.md`.
- Install generated Codex skill drafts with `factory --install-codex-skills --confirm-install` into `$CODEX_HOME/skills` or `~/.codex/skills`.
- Recommend minimal skill/agent capabilities with `recommend-skills` or `catalog`, including built-in factory candidates and ECC seed catalog candidates.
- Install only small Codex adapter skills from recommendations with `recommend-skills --install --confirm-install`; do not bulk-install ECC hooks, MCP servers, slash commands, native agents, or marketplace entries.
- Curate prior skill recommendations from history/eval evidence through `skill_recommendations.curator`, including baseline, repair, reduce, keep, and watch actions.
- Detect generic factory output, stale/unmanaged factory artifacts, planned skill conflicts, installed/generated skill overlap, and safe update paths.
- Select a Codex worker pattern such as single-agent, background-review, visible-decision-thread, producer-reviewer, fanout-review, supervisor-cycle, or phase-handoff.
- Generate a plan-only with-harness vs baseline evaluation with golden tasks and assertion scoring.
- Score recorded with-harness vs baseline evaluation JSON using `eval --score`.
- Persist scored eval results with `eval --score --write-score` into `Docs/AI/harness-eval-results.jsonl` so future diagnosis, tuning, factory planning, and run-loop next actions can use them.
- Generate a minimal initial harness with `bootstrap` or `apply`, dry-run by default and write-gated by `--write`.
- Generate reviewable tuning diffs with `tune --dry-run --diff`, using managed sections instead of whole-file rewrites.
- Record and summarize harness evolution through `Docs/AI/harness-history.jsonl`, then feed recurring history signals back into diagnosis and tuning.
- Merge history and eval-score signals into closed-loop review pressure, recommendations, factory quality fields, and run-loop next-action selection.
- Recommend phase-aware harness review cadence and structured adaptive cadence/human-involvement changes without silently applying policy changes.
- Detect drift between `package.json` scripts and validation docs.
- Detect overbroad process rules that require full QA, detailed reports, visible chats, or plans for every small task.
- Detect human-involvement enforcement gaps where ask-before-edit rules are missing or not linked from the repo entrypoint.
- Generate a human-involvement and worker visibility matrix.
- Emit a diagnosis-based `codex-harness-setup` prompt.
- Generate bounded worker assignment prompts with `patterns --prompt <pattern-id>`.
- Write `Docs/AI/harness-loop-plan.md`, apply the next recommended write action, or append `Docs/AI/harness-history.jsonl` through explicit `next`/`run-loop` flags only.
- Write `Docs/AI/harness-status.md` only when the user explicitly asks for a durable status record.
- Generate harness-design prompts for `codex-harness-setup`.
- Explain whether parallel work should be hidden/backgrounded or exposed as visible user-facing chats.
- List installed skills and plugins only as supporting context for harness diagnosis.
- Apply harness restructuring through the embedded `codex-harness-setup` skill when the user asks for changes.

## Improvement Loop

1. **Analyze**: inspect project type, existing harness files, package scripts, CI/hooks, reports, and coordination docs. Prefer `scripts/console.py next --repo <repo-root>` for the first read-only "what should Codex do next?" pass.
2. **Diagnose**: run `scripts/console.py diagnose --repo <repo-root> --phase <phase>` and review readiness, drift, overbroad process, adaptive cadence, and human-involvement recommendations.
3. **Design**: run `scripts/console.py design --repo <repo-root> --phase <phase>` or inspect `harness_design` from diagnosis to choose target files, worker pattern, validation evidence, and next review timing.
4. **Factory**: when the user wants team/skill generation, run `scripts/console.py factory --repo <repo-root> --domain "<domain>" --phase <phase>` to design repo-specific agent roles, planned skill files, orchestration rules, evidence-backed triggers, artifact inventory, update paths, and durable outputs. Add `--write-artifacts` only when the user wants repo-local team/skill docs written. Add `--write-codex-skills` only when the user wants copyable Codex `SKILL.md` drafts. Add `--install-codex-skills --confirm-install` only when the user explicitly wants generated skill drafts installed.
5. **Recommend skills**: run `scripts/console.py recommend-skills --repo <repo-root> --domain "<domain>" --phase <phase>` to rank only the smallest useful built-in or ECC-seed skill/agent candidates. Add `--write-plan` only for `Docs/AI/skill-recommendations.md`. Add `--install --confirm-install` only when the user explicitly approves adapter skill installation.
6. **Restructure**: invoke the embedded `codex-harness-setup` skill to make the smallest useful change. Prefer `AGENTS.md`, `Docs/AI/harness-profile.md`, and `Docs/AI/validation.md` for first setup.
7. **Restructure or Bootstrap**: for new projects, run `scripts/console.py bootstrap --repo <repo-root> --phase new-project` first as a dry-run. For existing harnesses, run `scripts/console.py tune --repo <repo-root> --phase <phase> --dry-run --diff`. Add `--write` only after the user wants files written. When human involvement is 4 or 5, add `--confirm-write` after reviewing the dry-run/diff. Existing bootstrap files require `--force` to overwrite.
8. **Evaluate**: run the embedded `codex-harness-setup/scripts/check_harness.py <repo-root>` when harness files changed, then rerun `diagnose`. Use `scripts/console.py eval --repo <repo-root> --phase <phase>` when the user wants with-harness vs baseline evidence, and `scripts/console.py eval --score <results.json>` after assertion results are recorded. Add `--repo <repo-root> --write-score --note "<why>"` when the score should influence future loops. Write `Docs/AI/harness-status.md`, `Docs/AI/harness-design-plan.md`, `Docs/AI/factory-plan.md`, `Docs/AI/skill-recommendations.md`, `Docs/AI/harness-eval-plan.md`, `Docs/AI/harness-eval-results.jsonl`, or `Docs/AI/harness-history.jsonl` only when durable status is useful or requested.

## Recommended Workflow

1. For the simplest entry point, run `scripts/console.py next --repo <repo-root> --phase <phase> --domain "<domain>"`.
2. For a shorter health check, run `scripts/console.py doctor --repo <repo-root> --phase <phase> --domain "<domain>"`.
3. For the full planning pass by its original name, run `scripts/console.py run-loop --repo <repo-root> --phase <phase> --domain "<domain>"`. Add `--write-plan`, `--write-recommended`, or `--record-history` only after reviewing the read-only result.
4. For a combined diagnosis overview, run `scripts/console.py overview --repo <repo-root>` from the plugin root.
5. For harness scoring and tuning recommendations, run `scripts/console.py diagnose --repo <repo-root> --phase <phase>`.
   - Add `--emit-prompt` to generate a `codex-harness-setup` prompt from the diagnosis.
   - Add `--write-status` only when the user wants a durable `Docs/AI/harness-status.md` record.
   - Add `--write-plan` only when the user wants a durable `Docs/AI/harness-design-plan.md` record.
6. For the next design only, run `scripts/console.py design --repo <repo-root> --phase <phase>`.
7. For available worker architectures, run `scripts/console.py patterns --json`. For a bounded worker prompt, run `scripts/console.py patterns --prompt <pattern-id> --repo <repo-root> --scope "<scope>"`.
8. For team/skill factory planning, run `scripts/console.py factory --repo <repo-root> --domain "<domain>" --phase <phase> --json`. For repo-local docs, run `scripts/console.py factory --repo <repo-root> --domain "<domain>" --write-artifacts`. For Codex skill drafts, run `scripts/console.py factory --repo <repo-root> --domain "<domain>" --write-codex-skills`. For confirmed installation, run `scripts/console.py factory --repo <repo-root> --domain "<domain>" --install-codex-skills --confirm-install`.
9. For minimal skill/agent recommendations, run `scripts/console.py recommend-skills --repo <repo-root> --domain "<domain>" --phase <phase> --json`. For a repo-local plan, add `--write-plan`. For confirmed adapter installation, add `--install --confirm-install`.
10. For evaluation planning, run `scripts/console.py eval --repo <repo-root> --phase <phase> --json`. For scoring recorded results, run `scripts/console.py eval --score <results.json> --json`. To feed the next loop, run `scripts/console.py eval --repo <repo-root> --score <results.json> --write-score --note "<why>"`.
11. For fixture regression coverage before release-facing changes, run `scripts/console.py fixture-test`.
12. For safe initial harness generation, run `scripts/console.py bootstrap --repo <repo-root> --phase new-project --json`.
13. For existing harness tuning diffs, run `scripts/console.py tune --repo <repo-root> --phase <phase> --dry-run --diff`.
14. For durable history, run `scripts/console.py history --repo <repo-root> --record --write --note "<why>"`.
15. For installed skills, run `scripts/console.py skills --json`.
16. For installed plugins, run `scripts/console.py plugins --json`.
17. For the active repo, run `scripts/console.py repo --repo <repo-root> --json`.
18. For a setup prompt, run `scripts/console.py prompt --repo-type "<type>" --mode Setup --human-involvement 3`.
19. When the user wants actual repo harness changes, invoke the embedded `codex-harness-setup` after inspection.

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

Use the worker-pattern selector first, then apply this policy in generated prompts:

- Use visible chats for product decisions, scope negotiation, roadmap changes, QA reports the user must inspect, or specialist work where the user benefits from seeing the thread.
- Use background/read-only workers for independent code review, test review, security review, static audits, or repo scans where only the final findings matter.
- Use a single agent for small changes, docs edits, narrow validation fixes, or low-risk content corrections.
- Persist reports only for staged/high-risk cycles, multi-agent handoffs, QA evidence, or decisions future agents must reuse.

## Evaluation Policy

Use `eval` when the user asks whether the tuner is actually improving results. The command is plan-only: it creates golden tasks, baseline/with-harness comparison instructions, and assertions, but does not automatically run separate agents.

Promote a harness change only when the evaluation suggests it improves correctness, reviewability, evidence quality, or overhead. Do not overfit the harness to one prompt.

Use `eval --score --write-score` after reviewing recorded assertion results when the score should guide future work. The durable record is `Docs/AI/harness-eval-results.jsonl`. Eval regressions and unchanged failures raise review pressure and can make `next` / `run-loop` recommend `tune` or `eval-review`; eval improvements support keeping the current harness direction while watching overhead.

## Fixture Test Policy

Use `fixture-test` before changing scanners, diagnosis scoring, loop next-action selection, factory presets, factory evidence quality, evaluation golden tasks, write guards, or read-only behavior. Fixtures live under `tests/fixtures` and are documented in `Docs/fixture-tests.md`. Keep fixtures small and free of dependency folders, Unity generated folders, secrets, logs, private data, or large generated artifacts.

## Factory Policy

Use `factory` when the user asks to generate a project-specific team, skill set, or harness like `revfactory/harness` style agent-team design. The first output should be a plan: repo evidence, roles, planned skills, orchestration, visible/background policy, artifact inventory, update paths, and evaluation hooks. Generated role prompts and skill triggers should cite concrete evidence such as project type, scripts, harness files, source markers, and validation commands when available. Use `--write-artifacts` to create repo-local markdown artifacts after the user wants files written. Use `--write-codex-skills` to create copyable Codex `SKILL.md` draft folders under `Docs/AI/codex-skills`. Use `--install-codex-skills --confirm-install` only after the user wants installation; default installs to `$CODEX_HOME/skills` or `~/.codex/skills`, and `--skill-install-root` may redirect installs for testing or team workflows.

Factory writes preserve existing files by default. Generated files contain the `repo-harness-tuner:generated:factory` marker. Use `--force` for reviewed generated files. Use `--force --replace-unmanaged` only after reviewing a file or installed skill that lacks the generated marker. Report stale/unmanaged artifacts, planned skill conflicts, installed overlaps, and the recommended update path before writing.

The factory side and engine side must stay linked: generated teams and skills should be evaluated with `eval`, recorded in `history`, and tuned by `diagnose`/`tune` as the project evolves.

## Skill Recommendation Policy

Use `recommend-skills` when the user wants the plugin to decide which skills or agents would help, including whether ECC-style assets are worth considering. The command should start read-only and recommend at most three candidates. It should prefer existing repo evidence and local factory output before external candidates, and it should suppress low-evidence external recommendations.

External catalog support is adapter-only in this plugin. `--source ecc` can recommend ECC seed candidates, but the approved install path creates small Codex adapter skills rather than copying or enabling ECC hooks, MCP servers, slash commands, native agents, or marketplace entries. Use `--catalog-root <path>` only to check whether a local ECC checkout has matching files; absence of a local checkout should not imply that native ECC is installed.

Use `skill_recommendations.curator` to decide whether the next cycle should baseline, repair, reduce, keep, or watch the skill set. Eval regressions, unchanged failures, readiness regression, and failure notes should bias toward repair. Repeated process overhead should bias toward reduction instead of adding more skills. No curator action may silently install skills or change human-involvement policy.

## Bootstrap And History Policy

Use `bootstrap` for first-project setup or empty harnesses. It is dry-run by default and should show actions before writing files. Use `apply` as an alias only when the user clearly wants generated files applied.

Use `tune` for projects with existing harness files. It should generate a reviewable unified diff first and update only managed sections marked with `repo-harness-tuner:start:*` / `repo-harness-tuner:end:*`, unless creating a missing baseline file.

Use `history` after meaningful harness changes, repeated mistakes, evaluation runs, or user feedback. The history record should stay concise: readiness, worker pattern, drift counts, target actions, next review trigger, and a short note.

Future `diagnose`, `tune`, `factory`, and `next` / `run-loop` runs should treat repeated history and eval-score signals as design evidence: readiness regression, repeated validation drift, repeated process overhead, repeated human-involvement gaps, recent failure notes, eval regressions, and unchanged eval failures raise review pressure and can justify a harness-profile update. `next`, `doctor`, and `run-loop` expose this as `adaptive.cadence` and `adaptive.human_involvement`; policy changes require explicit approval.

## Safety

- Treat install, uninstall, enable, disable, and marketplace edits as explicit actions. Prefer inspection and generated instructions unless the user asks for changes.
- Do not delete skills, plugins, marketplace entries, repo docs, or harness files without direct user approval.
- For file-writing commands at human involvement 4 or 5, require `--confirm-write` after the dry-run or diff has been inspected.
- `next --write-recommended` / `run-loop --write-recommended` may only apply low-risk managed harness writes under `AGENTS.md` or `Docs/AI/*`; it must refuse deletion, dependency changes, CI changes, install/uninstall, marketplace edits, and paths outside those managed harness surfaces.
- `next --write-recommended` / `run-loop --write-recommended` may write `Docs/AI/skill-recommendations.md`, but it must not install adapter skills. Adapter installs require `recommend-skills --install --confirm-install`.
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
- worker architecture, selected pattern, and evaluation steps,
- factory plan repo evidence, roles, planned skills, orchestration, artifact inventory, update paths, and planned outputs when requested,
- skill recommendation capabilities, sources, install strategy, curator action, and adapter-only install boundary when requested,
- eval plan golden tasks and assertions when requested,
- fixture-test pass/fail summary when requested,
- bootstrap dry-run or write results,
- tune diff proposals and write results,
- harness history summary or written event path,
- recommended review cadence,
- structured adaptive cadence and human-involvement recommendations,
- human-involvement and visibility matrix,
- suggested next action,
- exact prompt text when requested.
