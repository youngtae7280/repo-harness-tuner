# Repo Harness Tuner

Local Codex plugin for continuously improving repo-local Codex working rules. It runs a repeatable loop:

```text
Analyze -> Diagnose -> Design -> Restructure -> Evaluate
```

It focuses on designing and improving `AGENTS.md`, `Docs/AI/*`, validation guidance, target files, human-involvement policy, and visible/background worker policy as the project evolves.

## What It Provides

- `repo-harness-tuner` skill for the analyze/diagnose/restructure/evaluate loop.
- Embedded `codex-harness-setup` skill for creating and tuning repo-local harness files.
- Read-only scanners for installed skills and plugins as supporting evidence.
- A repo harness scanner for `AGENTS.md`, `Docs/AI/*`, `docs/ai/*`, `Docs/SKILLS.md`, and package scripts.
- A `diagnose` command that scores harness readiness and recommends tuning changes.
- Project-type detection and presets for Unity, Godot, Vite/Node, Node, Python, and docs-only projects.
- A `design` command that turns diagnosis into target files, worker architecture, evaluation steps, and next review triggers.
- Phase-aware tuning cadence for new projects, prototypes, active development, pre-release, maintenance, and high-risk work.
- Drift checks between package scripts and validation guidance.
- Human-involvement and worker-visibility matrix generation.
- A prompt generator for `codex-harness-setup`.
- A standalone HTML prototype for human-involvement and worker-visibility prompt building.

## Improvement Loop

Use the loop whenever a project starts, changes shape, accumulates repeated agent mistakes, or feels too heavy/light:

1. **Analyze**: inspect repo shape, scripts, existing `AGENTS.md`, `Docs/AI/*`, and coordination docs.
2. **Diagnose**: score readiness, detect drift, detect overbroad process, and recommend the next smallest change.
3. **Design**: choose target files, worker visibility, validation evidence, and the next review trigger.
4. **Restructure**: use the embedded `codex-harness-setup` skill to add, shorten, split, or tune harness files.
5. **Evaluate**: run the harness checker, record status when useful, and set the next tuning cadence.

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
python scripts\console.py diagnose --repo C:\path\to\repo --phase new-project
python scripts\console.py diagnose --repo C:\path\to\repo --phase new-project --human-involvement 3 --emit-prompt
python scripts\console.py design --repo C:\path\to\repo --phase active-development --human-involvement 3
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
python scripts\console.py diagnose --repo C:\path\to\repo --phase prototype --json
python scripts\console.py design --repo C:\path\to\repo --phase prototype --json
python scripts\console.py skills --json
python scripts\console.py plugins --json
python scripts\console.py repo --repo C:\path\to\repo --json
```

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
- evaluation steps and next review trigger,
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

Use `--write-plan` only when you want a durable design plan in the target repository:

```powershell
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --write-plan
```

This writes:

```text
Docs/AI/harness-design-plan.md
```

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
Run repo-harness-tuner on this project: analyze, diagnose, restructure, and evaluate the Codex harness.
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
