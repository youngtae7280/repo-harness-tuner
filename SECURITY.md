# Security Policy

Repo Harness Tuner is a local Codex plugin that inspects repository metadata and can optionally write harness files when explicitly requested.

## Safety Model

- Scan and diagnosis commands are read-only.
- `bootstrap`, `apply`, `history --record`, `eval --write-plan`, and status/design-plan writers modify a target repository only when explicit write flags are used.
- Existing harness files are skipped by default.
- Overwrites require `--force` together with `--write`.
- Evaluation is plan-only and does not automatically run separate agents or execute project commands.

## Sensitive Data

Do not include secrets, tokens, credentials, private keys, personal data, proprietary logs, or private screenshots in:

- harness docs,
- evaluation plans,
- history snapshots,
- issue reports,
- prompts,
- test fixtures.

If a diagnosis needs to mention a sensitive area, describe the category and path pattern without exposing values.

## Reporting Issues

For private deployments, report issues through your repository's private issue tracker.

For public forks, open a GitHub issue with:

- plugin version,
- command run,
- operating system,
- sanitized output,
- whether any write flags were used.
