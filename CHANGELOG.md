# Changelog

## 0.1.0 - 2026-06-07

Initial GitHub release.

### Added

- Reviewable `tune --dry-run --diff` command that converts diagnosis into managed-section unified diffs.
- Repo-local Codex harness diagnosis for `AGENTS.md`, `Docs/AI/*`, package scripts, and common agent instruction files.
- Project-type presets for Unity, Godot, Vite/Node, Node, Python, docs-only, and unknown repositories.
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
