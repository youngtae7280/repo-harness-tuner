# Repo Harness Tuner

Local Codex plugin for continuously improving repo-local Codex working rules and generating project-specific Codex team/skill plans. The final product direction is to carry both sides together:

- **Factory**: generate project-specific agent teams, role prompts, skill plans, and orchestration docs.
- **Engine**: analyze, diagnose, tune, evaluate, and keep those harnesses right-sized as the project evolves.

It runs a repeatable loop:

```text
Analyze -> Diagnose -> Design -> Factory -> Tune -> Restructure -> Evaluate
```

It focuses on designing and improving `AGENTS.md`, `Docs/AI/*`, validation guidance, target files, human-involvement policy, visible/background worker policy, and repo-local team/skill artifacts as the project evolves.

See [ROADMAP.md](ROADMAP.md) for the release plan from v0.3.0 fixture golden tests through v1.0.0. See [HANDOFF.md](HANDOFF.md) when continuing the work from another PC using GitHub as the source of truth.

## What It Provides

- `repo-harness-tuner` skill for the analyze/diagnose/design/tune/restructure/evaluate loop.
- Embedded `codex-harness-setup` skill for creating and tuning repo-local harness files.
- A `doctor` command for a read-only one-command health check, readiness score, loop summary, and recommended next action.
- A `run-loop` command, also available as `loop`, that executes the full analyze -> diagnose -> design -> factory -> tune -> evaluate -> history planning pass and can optionally write a loop plan, apply the next recommended write action, or record history.
- A `fixture-test` command that runs golden tests across empty, Vite/Node, Unity, Codex plugin, and harnessed-project fixtures.
- Read-only scanners for installed skills and plugins as supporting evidence.
- A repo harness scanner for `AGENTS.md`, `Docs/AI/*`, `docs/ai/*`, `Docs/SKILLS.md`, and package scripts.
- A `diagnose` command that scores harness readiness and recommends tuning changes.
- Project-type detection and presets for Unity, Godot, Vite/Node, Node, Python, Codex plugin, and docs-only projects.
- A `design` command that turns diagnosis into target files, worker architecture, evaluation steps, and next review triggers.
- A `factory` command that turns a domain description plus concrete repo evidence into a Codex team/skill factory plan, optional repo-local team/skill artifacts, optional Codex `SKILL.md` draft folders, and confirmed skill installs.
- Factory quality checks for evidence-backed role prompts, repo-specific skill triggers, validation hints, stale generated artifacts, planned skill conflicts, and safe update paths.
- A Codex worker-pattern catalog inspired by team-architecture harnesses, translated into practical Codex modes.
- An `eval` command that creates a plan-only with-harness vs baseline evaluation with golden tasks and assertions.
- An `eval --score` mode that scores recorded baseline vs with-harness assertion results.
- An `eval --score --write-score` mode that stores durable score history in `Docs/AI/harness-eval-results.jsonl`.
- A safe `bootstrap`/`apply` flow that generates initial harness files in dry-run mode by default.
- A `tune` command that turns diagnosis into reviewable unified diffs before writing files.
- A `history` command that records diagnosis snapshots, summarizes harness evolution, and feeds recurring signals back into diagnosis.
- Closed-loop feedback that uses stored eval scores and history records to raise review pressure, choose the next action, tune managed sections, and annotate factory plans.
- Codex plugin-specific detection, factory roles, evaluation tasks, and validation guidance for plugin.json, bundled skills, and CLI smoke flows.
- Phase-aware tuning cadence for new projects, prototypes, active development, pre-release, maintenance, and high-risk work.
- Drift checks between package scripts and validation guidance.
- Human-involvement and worker-visibility matrix generation.
- Human-involvement write guards: levels 4 and 5 require `--confirm-write` for file-writing commands.
- Worker assignment prompt generation for visible/background Codex worker patterns.
- A prompt generator for `codex-harness-setup`.
- A standalone HTML prototype for human-involvement and worker-visibility prompt building.

## Improvement Loop

Use the loop whenever a project starts, changes shape, accumulates repeated agent mistakes, or feels too heavy/light:

1. **Analyze**: inspect repo shape, scripts, existing `AGENTS.md`, `Docs/AI/*`, and coordination docs.
2. **Diagnose**: score readiness, detect drift, detect overbroad process, and recommend the next smallest change.
3. **Design**: choose target files, worker visibility, validation evidence, and the next review trigger.
4. **Factory**: design the project-specific Codex worker team and planned skills when the work benefits from specialized roles.
5. **Tune**: generate a reviewable diff for missing or stale harness sections.
6. **Restructure**: use the embedded `codex-harness-setup` skill to add, shorten, split, or tune harness files.
7. **Evaluate**: run the harness checker, record status when useful, and set the next tuning cadence.

For a brand-new project, this plugin should usually bootstrap only:

```text
AGENTS.md
Docs/AI/harness-profile.md
Docs/AI/validation.md
```

Add heavier harnesses only after real project risk appears.

## Common Commands

Run these from this plugin directory.

```powershell
python scripts\console.py overview --repo C:\path\to\repo
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "technical documentation"
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "technical documentation"
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "technical documentation" --write-plan
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "technical documentation" --record-history --note "after first feature"
python scripts\console.py fixture-test
python scripts\console.py diagnose --repo C:\path\to\repo --phase new-project
python scripts\console.py diagnose --repo C:\path\to\repo --phase new-project --human-involvement 3 --emit-prompt
python scripts\console.py design --repo C:\path\to\repo --phase active-development --human-involvement 3
python scripts\console.py factory --repo C:\path\to\repo --domain "Unity tycoon game UI" --phase active-development
python scripts\console.py factory --repo C:\path\to\repo --domain "deep research" --team-size 3 --write-plan
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --write-artifacts
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --write-codex-skills
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --install-codex-skills --confirm-install
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --write-artifacts --force --replace-unmanaged
python scripts\console.py patterns
python scripts\console.py patterns --prompt background-review --repo C:\path\to\repo --phase active-development --scope "validation drift"
python scripts\console.py eval --repo C:\path\to\repo --phase active-development --human-involvement 3
python scripts\console.py eval --repo C:\path\to\repo --phase active-development --write-plan
python scripts\console.py eval --score C:\path\to\eval-results.json
python scripts\console.py eval --repo C:\path\to\repo --score C:\path\to\eval-results.json --write-score --note "after factory team tune"
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 3
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 3 --write
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 5 --write --confirm-write
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --dry-run --diff
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --write
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --human-involvement 4 --write --confirm-write
python scripts\console.py apply --repo C:\path\to\repo --phase new-project --write --force
python scripts\console.py history --repo C:\path\to\repo
python scripts\console.py history --repo C:\path\to\repo --record --write --note "after first feature"
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --module "Ending taxonomy: 5"
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --write-status
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --write-plan
python scripts\console.py skills
python scripts\console.py plugins
python scripts\console.py repo --repo C:\path\to\repo
python scripts\console.py prompt --repo-type "Vite + TypeScript + JSON game prototype" --phase prototype --human-involvement 2
```

JSON output is available for the scan commands:

```powershell
python scripts\console.py overview --repo C:\path\to\repo --json
python scripts\console.py doctor --repo C:\path\to\repo --phase prototype --json
python scripts\console.py run-loop --repo C:\path\to\repo --phase prototype --json
python scripts\console.py fixture-test --json
python scripts\console.py diagnose --repo C:\path\to\repo --phase prototype --json
python scripts\console.py design --repo C:\path\to\repo --phase prototype --json
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --json
python scripts\console.py patterns --json
python scripts\console.py eval --repo C:\path\to\repo --phase prototype --json
python scripts\console.py eval --score C:\path\to\eval-results.json --json
python scripts\console.py eval --repo C:\path\to\repo --score C:\path\to\eval-results.json --write-score --json
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --json
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --json
python scripts\console.py history --repo C:\path\to\repo --record --json
python scripts\console.py skills --json
python scripts\console.py plugins --json
python scripts\console.py repo --repo C:\path\to\repo --json
```

## One-Command Doctor And Loop

Use `doctor` first when you want to know whether the current repo harness is healthy without changing files:

```powershell
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "technical documentation"
```

It reports the project type, readiness, selected worker pattern, loop module counts, history count, eval score count, closed-loop review pressure, and one next action.

Use `run-loop` when you want the full planning pass in one command:

```powershell
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "technical documentation"
```

By default `run-loop` is read-only. Add write flags only after reviewing the output:

```powershell
python scripts\console.py run-loop --repo C:\path\to\repo --write-plan
python scripts\console.py run-loop --repo C:\path\to\repo --write-recommended
python scripts\console.py run-loop --repo C:\path\to\repo --record-history --note "after first feature"
```

These write, respectively:

```text
Docs/AI/harness-loop-plan.md
the next recommended bootstrap, tune, or factory artifact action
Docs/AI/harness-history.jsonl
```

`loop` is an alias for `run-loop`. At human involvement 4 or 5, every file-writing loop command also requires `--confirm-write`.

`--write-recommended` is bounded to low-risk managed harness writes. It refuses deletion, dependency changes, CI changes, install/uninstall, marketplace edits, and paths outside `AGENTS.md` or `Docs/AI/*`.

## Fixture Golden Tests

Run `fixture-test` before changing detection, diagnosis, loop planning, factory presets, evaluation tasks, or write safety:

```powershell
python scripts\console.py fixture-test
```

The fixture suite currently covers empty/new projects, Vite/Node projects, Unity projects, Codex plugin projects, an already-harnessed Vite project, history-pressure scenarios, and eval-score-pressure scenarios. It checks project type, readiness range, next action, golden task count, factory label, factory evidence quality, stale/conflicting generated artifacts, closed-loop signal handling, high-risk write guards, and read-only command behavior.

See [Docs/fixture-tests.md](Docs/fixture-tests.md) for fixture authoring rules.

## Project Phases

Use the phase that matches the repository's current risk:

- `new-project`: no stable agent harness yet.
- `prototype`: fast iteration, changing structure, exploratory features.
- `active-development`: regular feature work with known validation paths.
- `pre-release`: QA, packaging, polish, and release confidence.
- `maintenance`: mostly fixes and small enhancements.
- `high-risk`: migrations, destructive operations, secrets, release, or difficult rollback.

The diagnose command returns a recommended harness tuning cadence for the selected phase.

## Diagnosis Outputs

`diagnose` reports:

- harness readiness score,
- missing or stale harness files,
- detected drift between package scripts and validation docs,
- human-involvement enforcement gaps where ask/decide rules are missing or not linked from the repo entrypoint,
- overbroad process rules such as always-full-QA, always-detailed-report, or always-visible-chat,
- harness design target files and reasons,
- recommended worker architecture,
- worker-pattern selection reason,
- evaluation steps and next review trigger,
- history feedback from `Docs/AI/harness-history.jsonl`, including readiness regression, repeated drift, repeated overhead, repeated human-involvement gaps, or recent failure notes,
- eval score feedback from `Docs/AI/harness-eval-results.jsonl`, including regressions, unchanged failures, or improvements,
- bootstrap actions for missing or existing harness files,
- generated tuning diffs for missing or stale harness sections,
- history snapshot summaries when requested,
- human-involvement and worker visibility matrix,
- phase-specific tuning cadence.

Use `--emit-prompt` to append a `codex-harness-setup` prompt based on the diagnosis:

```powershell
python scripts\console.py diagnose --repo C:\path\to\repo --phase prototype --emit-prompt
```

Use `--write-status` only when you want to update the target repository with a durable status file:

```powershell
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --write-status
```

This writes:

```text
Docs/AI/harness-status.md
```

Use `design` when you want the next harness structure without the full diagnosis text:

```powershell
python scripts\console.py design --repo C:\path\to\repo --phase active-development --human-involvement 3
```

Use `factory` when you want the team/skill factory side of the plugin:

```powershell
python scripts\console.py factory --repo C:\path\to\repo --domain "full-stack website development" --phase active-development
```

It combines repo diagnosis with a domain preset and returns:

- concrete repo evidence such as project markers, package scripts, harness files, source markers, and validation commands,
- planned Codex worker roles,
- planned skill files under `Docs/AI/skills/*.md`,
- repo-specific skill triggers, boundaries, and validation hints,
- a team architecture pattern,
- orchestration rules for visible chats vs background workers,
- existing artifact conflicts, stale/unmanaged artifact signals, installed skill overlaps, and recommended update paths,
- evaluation and history feedback hooks.

Use `--write-plan` only when you want a durable factory plan:

```powershell
python scripts\console.py factory --repo C:\path\to\repo --domain "Unity tycoon game UI" --write-plan
```

This writes:

```text
Docs/AI/factory-plan.md
```

Use `--write-artifacts` when you want the factory to create the repo-local team/skill docs:

```powershell
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --write-artifacts
```

This writes missing files only:

```text
Docs/AI/agent-team.md
Docs/AI/team-orchestration.md
Docs/AI/skills/*.md
```

Existing files are preserved by default. Generated files contain a `repo-harness-tuner` marker. Use `--force` only when you intentionally want to replace existing generated factory files. If an existing file has no generated marker, it is treated as user-authored or unmanaged and also requires `--replace-unmanaged` after review.

Use `--write-codex-skills` when you want copyable/installable Codex skill drafts:

```powershell
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --write-codex-skills
```

This writes draft skill folders:

```text
Docs/AI/codex-skills/<skill-id>/SKILL.md
```

These drafts are not installed automatically. Review and validate them before copying or installing them into a Codex skills directory.

Use `--install-codex-skills --confirm-install` when you want the generated skill drafts installed into Codex's skills directory:

```powershell
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --install-codex-skills --confirm-install
```

By default this installs under `$CODEX_HOME/skills`, or `~/.codex/skills` when `CODEX_HOME` is not set. Use `--skill-install-root` for a different destination. Existing installed skills are preserved by default; use `--force` for generated skills and `--force --replace-unmanaged` only after reviewing a manually authored installed skill.

Use `--write-plan` only when you want a durable design plan in the target repository:

```powershell
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --write-plan
```

This writes:

```text
Docs/AI/harness-design-plan.md
```

Use `patterns` to inspect the available Codex worker architectures:

```powershell
python scripts\console.py patterns
```

Current patterns are:

- `single-agent`: one Codex thread handles analysis, edits, and closeout.
- `background-review`: main thread edits while a short-lived read-only reviewer checks a focused risk.
- `visible-decision-thread`: visible user-facing decision path for approval, product, roadmap, UX, release, or scope tradeoffs.
- `producer-reviewer`: one worker produces, another independently checks objective criteria.
- `fanout-review`: parallel read-only reviewers inspect separate risk surfaces.
- `supervisor-cycle`: staged multi-slice harness improvement coordinated by the main thread.
- `phase-handoff`: persistent artifacts support later phases or future sessions.

Use `patterns --prompt <pattern-id>` to create a bounded assignment prompt for a visible or background worker:

```powershell
python scripts\console.py patterns --prompt producer-reviewer --repo C:\path\to\repo --phase active-development --scope "review harness validation drift"
```

Use `eval` to create a safe evaluation plan for comparing normal Codex behavior against repo-harness-tuner-guided behavior:

```powershell
python scripts\console.py eval --repo C:\path\to\repo --phase active-development --human-involvement 3
```

Use `--write-plan` only when you want a durable evaluation plan in the target repository:

```powershell
python scripts\console.py eval --repo C:\path\to\repo --phase active-development --write-plan
```

This writes:

```text
Docs/AI/harness-eval-plan.md
```

After recording assertion results, score them:

```powershell
python scripts\console.py eval --score C:\path\to\eval-results.json
```

Accepted result files can contain either `{"results": [...]}` or a list of task results using the eval result schema. The scorer reports improved, regressed, unchanged pass, unchanged fail, and a keep/revise recommendation.

To let future `diagnose`, `tune`, `factory`, and `run-loop` commands learn from that score, write it into the target repo:

```powershell
python scripts\console.py eval --repo C:\path\to\repo --score C:\path\to\eval-results.json --write-score --note "after harness change"
```

This appends JSONL records to:

```text
Docs/AI/harness-eval-results.jsonl
```

Stored eval regressions and unchanged failures raise closed-loop review pressure and can make the next `run-loop` action become `tune` or `eval-review`.

Use `bootstrap` to generate the smallest useful initial harness. It is dry-run by default:

```powershell
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 3
```

Write files only after reviewing the dry-run:

```powershell
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 3 --write
```

When human involvement is 4 or 5, writing commands require `--confirm-write` after the dry-run/diff has been reviewed:

```powershell
python scripts\console.py tune --repo C:\path\to\repo --phase high-risk --write --confirm-write
```

Existing files are skipped unless `--force` is used together with `--write`.

```powershell
python scripts\console.py apply --repo C:\path\to\repo --phase new-project --write --force
```

Use `tune` when a repository already has harness files and you want a reviewable patch instead of a whole-file bootstrap:

```powershell
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --dry-run --diff
```

The diff uses managed markdown sections such as:

```text
<!-- repo-harness-tuner:start:validation -->
...
<!-- repo-harness-tuner:end:validation -->
```

Apply the proposed changes only after reviewing the diff:

```powershell
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --write
```

Use `--force` only when you intentionally want to apply despite local file changes since the diff was generated.

Use `history` to track whether the harness is improving over time:

```powershell
python scripts\console.py history --repo C:\path\to\repo
python scripts\console.py history --repo C:\path\to\repo --record --write --note "after first feature"
```

This appends JSONL records to:

```text
Docs/AI/harness-history.jsonl
```

Future `diagnose` and `tune` runs read this history and raise review pressure when readiness regresses or the same drift, overhead, human-involvement gap, or failure note repeats.

Stored history and eval scores are intentionally separate files. History records describe the repo harness state; eval score records describe measured baseline-vs-with-harness outcomes. The closed-loop feedback layer reads both.

## Human Involvement

The user-facing control is human involvement, from 1 to 5:

- Human involvement 1: Codex explores autonomously unless a protected area or explicit approval trigger appears.
- Human involvement 2: Codex proceeds from existing patterns and mentions assumptions in closeout.
- Human involvement 3: Codex infers from repo context, but asks before hard-to-reverse or user-visible direction changes.
- Human involvement 4: Codex asks 1-3 focused questions before edits unless a named repo source of truth already answers them.
- Human involvement 5: Codex stops and asks for explicit approval before edits.

Internally, this can still be stored in the repo harness as ask-before rules. Rows marked `Ask before` in `Docs/AI/ambiguity-profile.md` are stop conditions before file edits.

## Natural Language Use

After installing the plugin in Codex, ask for the loop directly:

```text
Run repo-harness-tuner on this project: analyze, diagnose, design, tune, restructure, and evaluate the Codex harness.
```

For diagnosis only:

```text
Use repo-harness-tuner to diagnose this repo's Codex harness without editing files.
```

For first-project setup:

```text
Use repo-harness-tuner and the embedded codex-harness-setup skill to bootstrap the smallest useful Codex harness for this new project.
```

## GUI Prototype

Open this file in a browser:

```text
assets/repo-harness-tuner.html
```

The prototype generates prompts locally in the browser. It does not read or write files.

## Worker Visibility Policy

Use visible chats when the user benefits from seeing the specialist context:

- product or roadmap decisions,
- scope negotiation,
- QA reports the user must inspect,
- UI/UX or content specialist work with subjective tradeoffs.

Use background/read-only workers when only the final findings matter:

- static scans,
- code review,
- test review,
- security review,
- harness audits.

Use a single agent for small, low-risk tasks.

## Safety

This plugin is read-first. Install, uninstall, enable, disable, delete, and marketplace edits should be explicit user-requested actions. Do not delete skills, plugins, marketplace entries, or repo harness files without direct approval.

File-writing commands require `--write`. When human involvement is 4 or 5, file-writing commands also require `--confirm-write`. Existing harness files are skipped by default for `bootstrap`/`apply` and require `--force` to overwrite. `tune` updates only managed sections or creates missing files.

## Additional Docs

- Korean README: `README_KO.md`
- Changelog: `CHANGELOG.md`
- Contributing guide: `CONTRIBUTING.md`
- Fixture test guide: `Docs/fixture-tests.md`
- Security policy: `SECURITY.md`
- License: `LICENSE`
- Notices: `NOTICE.md`
