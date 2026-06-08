# Repo Harness Tuner

Repo Harness Tuner is a local Codex plugin that helps Codex set up and keep improving the smallest useful repo-local working harness for a project.

It is meant to feel like a one-request assistant: you ask once, it inspects the repo, decides the next harness step, and keeps writes behind explicit approval.

## Start Here

In Codex, start with one request:

```text
Use repo-harness-tuner on this repo. Inspect the project, diagnose the Codex harness, recommend the next step, and keep file writes behind approval.
```

From the command line, run one read-only planning pass:

```powershell
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "your project"
```

For diagnosis only:

```powershell
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "your project"
```

## What Happens Next

The loop does the harness work in order:

```text
Analyze -> Diagnose -> Design -> Factory -> Tune -> Evaluate
```

It decides whether the repo needs:

- no change because the current harness is fit,
- a minimal first harness with `bootstrap`,
- a focused update to stale harness docs with `tune`,
- a project-specific team/skill plan with `factory`,
- an evaluation or history record so future runs can learn from the result.

You do not need to choose all of those commands up front. Start with `run-loop` or `doctor`; use the recommended next action after reviewing it.

## Safety Model

The plugin is read-first.

- `doctor` and default `run-loop` do not edit files.
- File writes require explicit flags such as `--write`, `--write-plan`, `--write-recommended`, or `--write-artifacts`.
- Human involvement levels 4 and 5 also require `--confirm-write`.
- Dependency, release, CI, secret, credential, marketplace, install/uninstall, migration, privacy-sensitive, and destructive changes require explicit approval.
- `tune` updates managed markdown sections instead of rewriting whole files.
- `bootstrap` and factory artifact writes preserve existing files unless an explicit force path is used.

## When To Use It

Use this plugin when:

- a repo needs `AGENTS.md` or `Docs/AI/*`,
- Codex is using too much or too little process,
- validation guidance, ask-before-edit rules, or worker visibility needs to be made repo-specific,
- a project would benefit from repo-specific Codex team or skill planning,
- you want history/eval evidence to guide future harness tuning.

You usually do not need it for ordinary coding, debugging, or review when the repo harness is already fit.

## Adaptive Harness Loop

Repo Harness Tuner is designed for projects that keep changing.

It tracks:

- phase-specific review cadence,
- next review triggers,
- readiness score movement,
- repeated validation drift,
- repeated process overhead,
- repeated human-involvement gaps,
- eval regressions and unchanged failures.

Those signals raise review pressure and can make the next `run-loop` recommend `tune`, `eval-review`, or a shorter review interval.

`doctor` and `run-loop` also emit structured `adaptive` recommendations for cadence and human involvement. There is no background scheduler yet. Re-run `doctor` or `run-loop` at the recommended trigger, after meaningful project changes, after repeated Codex misses, or before high-risk/release work.

## Human Involvement

Human involvement controls how much Codex should ask before acting.

By default, the plugin chooses a level from the project phase:

| Phase | Default |
| --- | ---: |
| `prototype` | 2 |
| `new-project` | 3 |
| `active-development` | 3 |
| `maintenance` | 3 |
| `pre-release` | 4 |
| `high-risk` | 5 |

You can override it:

```powershell
python scripts\console.py run-loop --repo C:\path\to\repo --human-involvement 4
python scripts\console.py run-loop --repo C:\path\to\repo --module "Release flow: 5"
```

Level guide:

- `1`: Codex can move autonomously unless a protected area appears.
- `2`: Codex follows repo patterns and reports assumptions.
- `3`: Codex infers from context but asks before hard-to-reverse or user-visible direction changes.
- `4`: Codex asks focused questions before edits unless the repo already answers them.
- `5`: Codex needs explicit approval before edits.

Current behavior detects human-involvement gaps and can recommend keeping, raising, or lowering the default level from history/eval evidence. It never applies that policy change silently; changing repo-local policy requires review and explicit approval.

## Core Commands

Run from this plugin directory:

```powershell
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "your project"
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "your project"
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --dry-run --diff
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project
python scripts\console.py fixture-test
```

Full command details and JSON examples are in [Docs/commands.md](Docs/commands.md).

## Install

For first-time install, clone to `$HOME\plugins\repo-harness-tuner`, add the personal marketplace entry, then run:

```powershell
codex plugin add repo-harness-tuner@personal
```

See [Docs/install.md](Docs/install.md) for fresh-clone setup, refresh, troubleshooting, Windows `codex.exe` shim issues, PyYAML validator setup, and validation.

## More Docs

- Korean README: [README_KO.md](README_KO.md)
- Install and troubleshooting: [Docs/install.md](Docs/install.md)
- Full command reference: [Docs/commands.md](Docs/commands.md)
- CLI contracts: [Docs/cli-contracts.md](Docs/cli-contracts.md)
- Versioning and breaking changes: [Docs/versioning.md](Docs/versioning.md)
- Fixture tests: [Docs/fixture-tests.md](Docs/fixture-tests.md)
- Roadmap: [ROADMAP.md](ROADMAP.md)
- Handoff for another PC/thread: [HANDOFF.md](HANDOFF.md)
