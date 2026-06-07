# Changelog

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
