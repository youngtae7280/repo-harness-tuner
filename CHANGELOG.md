# Changelog

## Unreleased

### Added

- `Docs/cli-contracts.md` documenting stable CLI command names, exit codes, JSON envelopes, write-safety behavior, and Windows console compatibility expectations for the v1.0.0 contract pass.
- `Docs/install.md` documenting fresh-clone install, personal marketplace setup, plugin refresh, validation, and troubleshooting flows.
- `Docs/commands.md` as the full command reference split out from the README.
- `Docs/versioning.md` documenting version format, breaking-change classification, deprecation policy, changelog rules, and release checklist expectations.
- Structured `adaptive` recommendations in `next`, `doctor`, and `run-loop` output for cadence, review pressure, and human-involvement policy suggestions.
- `next` as a friendly `run-loop` alias for "what should Codex do next?" onboarding.
- `recommend-skills` and `catalog` commands for minimal repo-fit skill/agent recommendations.
- ECC seed catalog support for adapter-only recommendations.
- Approved adapter skill install flow with `recommend-skills --install --confirm-install`.
- `skill_recommendations.curator` for history/eval-informed baseline, repair, reduce, keep, and watch decisions.
- `harness_contract` in `next`, `doctor`, and `run-loop` output, with standard Scope, Access & Actions, Definition of Done, and Human Approval Points sections.
- `summary.next_action.category`, `category_label`, and `category_summary` for one-command assistant work types.
- `release-check` for fresh-copy release validation, including manifest, compile, fixture/user-journey, JSON, console, and bootstrap smoke checks.
- User-journey fixture coverage for fresh repo bootstrap and fit repo history recording.
- Vertical Mermaid one-command flow diagrams in the Korean default README and the English README.
- `README_EN.md` for the English README after making `README.md` Korean by default.

### Changed

- `README.md` is now the Korean default README with a softer one-request onboarding tone; `README_KO.md` remains as a compatibility pointer.
- `doctor`, `run-loop`, and `next` text output now highlights what Codex found, what it can do next, the next command, approval boundaries, and validation hints.
- `bootstrap`, `tune`, and `factory` outputs now write the standard harness contract into generated or tuned harness docs.
- CLI JSON output is now ASCII-safe by default, and console output is configured to avoid `UnicodeEncodeError` crashes on legacy Windows console encodings.
- ROADMAP and HANDOFF now separate v1.0 one-command onboarding from v1.1+ adaptive cadence and adaptive human-involvement work.
- Fixture tests now assert that closed-loop history/eval pressure produces structured adaptive cadence and human-involvement recommendations.
- `next`, `doctor`, and `run-loop` now include minimal skill recommendations while keeping external installs approval-based and adapter-only.
- `factory-artifacts` next action copy now explains that it documents how Codex should split planning, development, and review work.

### Fixed

- `run-loop --write-recommended` now records the recommended baseline history action instead of reporting that no file changes were recommended.

## 0.8.0 - 2026-06-07

Stronger closed-loop release.

### Added

- `eval --score --write-score` for appending durable score records to `Docs/AI/harness-eval-results.jsonl`.
- Closed-loop feedback that merges harness history and stored eval scores for future `diagnose`, `tune`, `factory`, and `run-loop` decisions.
- Eval-informed diagnosis signals for regressions, unchanged failures, and improvements.
- Closed-loop fields in doctor/run-loop summaries, including eval score records, review pressure, and signal counts.
- Factory quality fields and generated factory docs that include closed-loop review pressure and eval/history recommendations.
- Fixture scenarios for history-pressure and eval-score-pressure projects.
- Low-risk auto-apply guard for `run-loop --write-recommended`, limited to managed harness docs or `AGENTS.md`.

### Changed

- `run-loop` can select `tune` or `eval-review` when stored eval/history evidence says the harness needs repair.
- `diagnose` next-review triggers now react to eval regressions and unchanged eval failures.
- Fixture tests now assert history/eval signal counts, review pressure, and closed-loop signal types.
- Documentation now describes eval score persistence and how closed-loop feedback influences later harness design.

### Safety Defaults

- Durable eval score writes require explicit `--write-score`.
- Automatic recommended writes refuse deletion, dependency changes, CI changes, install/uninstall, marketplace edits, and paths outside managed harness docs or `AGENTS.md`.

## 0.5.0 - 2026-06-07

Factory output quality release.

### Added

- Repo evidence summaries in `factory` output, including project markers, package scripts, harness files, source markers, and validation commands.
- Evidence-backed role purposes, skill triggers, Codex skill draft descriptions, validation hints, and boundaries.
- Factory artifact inventory for existing repo-local artifacts, stale/unmanaged files, planned skill conflicts, and installed skill overlaps.
- `--replace-unmanaged` for explicitly replacing existing files or installed skills that do not contain the repo-harness-tuner generated marker.
- Fixture assertions for factory evidence quality, generic-output prevention, stale artifacts, and planned skill conflicts.

### Changed

- Factory writes now mark generated files and preserve unmanaged existing files unless `--force --replace-unmanaged` is used after review.
- Factory docs and skill instructions now distinguish planning, repo-local artifacts, Codex skill drafts, and confirmed skill installation.

## 0.3.0 - 2026-06-07

Fixture golden-test release.

### Added

- `fixture-test` command for running fixture-based golden tests from the unified CLI.
- Fixture corpus covering empty/new project, Vite/Node project, Unity project, Codex plugin project, and already-harnessed Vite project.
- Golden assertions for project type, readiness range, loop status, next action, evaluation task count, factory team label, high-risk write guard behavior, and read-only fixture stability.
- `Docs/fixture-tests.md` with fixture authoring rules and safety constraints.
- GitHub Actions coverage for `fixture-test`.

### Changed

- Validation docs, contributor docs, handoff docs, and roadmap now include fixture-test as the regression safety net for later milestones.
- Roadmap current priority now moves to v0.5.0 factory output quality after the v0.3.0 fixture suite.

## 0.2.0 - 2026-06-07

One-command loop release.

### Added

- `doctor` command for a read-only health check, readiness score, loop summary, and recommended next action.
- `run-loop` command, with `loop` alias, for the full analyze, diagnose, design, factory, tune, evaluate, and history planning pass.
- `run-loop --write-plan` for writing `Docs/AI/harness-loop-plan.md` after reviewing the read-only plan.
- `run-loop --write-recommended` for applying the next recommended bootstrap, tune, or factory artifact action.
- `run-loop --record-history` for appending a `run-loop-snapshot` event to `Docs/AI/harness-history.jsonl`.
- Smoke coverage for the new one-command loop and write guards.

### Safety Defaults

- `doctor` and default `run-loop` are read-only.
- Loop writes require explicit write flags.
- Human involvement 4 or 5 still requires `--confirm-write` before file writes.

## 0.1.0 - 2026-06-07

Initial GitHub release.

### Added

- `factory` command for project-specific Codex team/skill factory planning from domain and repo evidence.
- `factory --write-artifacts` for repo-local `Docs/AI/agent-team.md`, `Docs/AI/team-orchestration.md`, and `Docs/AI/skills/*.md` generation.
- `factory --write-codex-skills` for copyable Codex `SKILL.md` draft generation under `Docs/AI/codex-skills`.
- `factory --install-codex-skills --confirm-install` for installing generated Codex skill drafts into a selected skills directory.
- Codex plugin project preset with plugin-specific diagnosis, factory roles, evaluation golden task, and validation guidance.
- Repo-local self harness files under `AGENTS.md` and `Docs/AI/*` for this plugin.
- Harness checker now inspects `Docs/AI`, `docs/AI`, and `docs/ai` paths so Linux and Windows path casing do not hide applied docs.
- Product direction now explicitly combines a team/skill generation factory with the adaptive harness improvement engine.
- History-informed diagnosis and tuning: repeated readiness regression, validation drift, process overhead, human-involvement gaps, and failure notes now feed back into `diagnose` and `tune`.
- `eval --score` for semi-automatic scoring of recorded baseline vs with-harness assertion results.
- Human-involvement write guards: file-writing commands at involvement level 4 or 5 require `--confirm-write`.
- `patterns --prompt <pattern-id>` for visible/background Codex worker assignment prompts.
- GitHub Actions validation workflow for script compilation and CLI smoke tests.
- Reviewable `tune --dry-run --diff` command that converts diagnosis into managed-section unified diffs.
- Repo-local Codex harness diagnosis for `AGENTS.md`, `Docs/AI/*`, package scripts, and common agent instruction files.
- Project-type presets for Unity, Godot, Vite/Node, Node, Python, Codex plugin, docs-only, and unknown repositories.
- Harness design output with target files, validation steps, worker architecture, and next review trigger.
- Codex worker pattern catalog: `single-agent`, `background-review`, `visible-decision-thread`, `producer-reviewer`, `fanout-review`, `supervisor-cycle`, and `phase-handoff`.
- Plan-only with-harness vs baseline evaluation command with golden tasks and assertions.
- Safe bootstrap/apply flow for initial harness files, dry-run by default.
- Harness history snapshots in `Docs/AI/harness-history.jsonl`.
- Embedded `codex-harness-setup` skill.
- Local HTML prompt-building prototype.

### Safety Defaults

- File writes require explicit `--write`.
- Existing harness files are skipped unless `--force` is used with `--write`.
- Tuning existing files updates managed sections instead of rewriting whole harness files.
- Evaluation is plan-only and does not automatically spawn agents.
