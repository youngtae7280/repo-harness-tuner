# Changelog

## 0.1.0 - 2026-06-07

Initial GitHub release.

### Added

- History-informed diagnosis and tuning: repeated readiness regression, validation drift, process overhead, human-involvement gaps, and failure notes now feed back into `diagnose` and `tune`.
- `eval --score` for semi-automatic scoring of recorded baseline vs with-harness assertion results.
- Human-involvement write guards: file-writing commands at involvement level 4 or 5 require `--confirm-write`.
- `patterns --prompt <pattern-id>` for visible/background Codex worker assignment prompts.
- GitHub Actions validation workflow template for script compilation and CLI smoke tests.
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
