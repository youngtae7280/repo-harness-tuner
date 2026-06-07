# Agent Instructions

## Start Here
- Read `README.md` when present, then `Docs/AI/harness-profile.md`, `Docs/AI/validation.md`, and `Docs/AI/ambiguity-profile.md`.
- Keep changes scoped to the request and existing project patterns.
- Prefer the smallest reversible edit that improves correctness, reviewability, or evidence.

## Human Involvement
- Default human involvement: 3/5.
- Any `Ask before` rule in `Docs/AI/ambiguity-profile.md` is a stop condition before file edits.
- Ask before destructive operations, dependency/release changes, secrets, migrations, or hard-to-reverse user-facing direction changes.

## Worker Visibility
- Default worker pattern: Supervisor Cycle (`supervisor-cycle`).
- Default visibility: main visible coordinator plus optional background workers.
- Use visible chats for approval, product, roadmap, UX, release, or scope decisions.
- Use background/read-only review for focused code, test, security, validation, or harness audits.

## Validation
- Use `Docs/AI/validation.md` to choose focused checks.
- Do not require full validation for every small task; explain skipped checks when validation is unavailable or not relevant.
