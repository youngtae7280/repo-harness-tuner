# Agent Instructions

Use `Docs/AI/harness-profile.md` for project-specific Codex behavior.
Use `Docs/AI/validation.md` for validation selection.
Ask before hard-to-reverse or user-visible direction changes.

<!-- repo-harness-tuner:start:agents-core -->
## Repo Harness Tuner Core Rules

Before editing harness-sensitive files, read `Docs/AI/harness-profile.md`, `Docs/AI/validation.md`, and `Docs/AI/ambiguity-profile.md` when present.
Treat any `Ask before` rule in `Docs/AI/ambiguity-profile.md` as a stop condition before file edits.
Default human involvement is 3/5.
Default worker pattern is Visible Decision Thread (`visible-decision-thread`) with visible chat.
Do not add CI gates, release blockers, dependencies, destructive scripts, or mandatory approvals without explicit user approval.
<!-- repo-harness-tuner:end:agents-core -->
