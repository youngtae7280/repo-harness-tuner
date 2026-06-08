# Agent Instructions

## Start Here
- Read `README.md` when present, then `Docs/AI/harness-profile.md`, `Docs/AI/validation.md`, and `Docs/AI/ambiguity-profile.md`.
- Keep changes scoped to the request and existing project patterns.
- Prefer the smallest reversible edit that improves correctness, reviewability, or evidence.

## Human Involvement
- Default human involvement: 3/5.
- Any `Ask before` rule in `Docs/AI/ambiguity-profile.md` is a stop condition before file edits.
- Ask before destructive operations, dependency/release changes, secrets, migrations, or hard-to-reverse user-facing direction changes.

## Cycle Budget
- Default work command budget: up to 3 cycles, stopping earlier when the task is complete.
- Use 1-2 cycles for small docs, copy, or single-file fixes; use up to 5 cycles for shared contracts, CLI behavior, plugin metadata, or validation-flow changes.
- For release, CI, install, marketplace, dependency, destructive, or hard-to-reverse changes, do one read/preview cycle and ask before applying.
- At the budget limit, report progress, validation evidence or skipped checks, remaining risk, and the next safe options.

## Worker Visibility
- Default worker pattern: Supervisor Cycle (`supervisor-cycle`).
- Default visibility: main visible coordinator plus optional background workers.
- Use visible chats for approval, product, roadmap, UX, release, or scope decisions.
- Use background/read-only review for focused code, test, security, validation, or harness audits.

## Validation
- Use `Docs/AI/validation.md` to choose focused checks.
- Do not require full validation for every small task; explain skipped checks when validation is unavailable or not relevant.
