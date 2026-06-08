# Versioning And Breaking-Change Policy

This document defines how Harness Tuner versions public behavior and classifies breaking changes for the v1.0.0 stabilization track.

The display name is **Harness Tuner**. The GitHub repo, plugin id, install command, and skill entry point remain `repo-harness-tuner` unless a future breaking-change release says otherwise.

It does not duplicate the command reference, install guide, or JSON contract details. Use these documents together:

- `Docs/cli-contracts.md` for stable CLI names, exit codes, JSON envelopes, write-safety behavior, and console compatibility.
- `Docs/commands.md` for command examples and options.
- `Docs/install.md` for clone, install, refresh, reinstall, validation, and troubleshooting steps.

## Version Format

Harness Tuner uses a SemVer-style base version:

```text
MAJOR.MINOR.PATCH
```

- Increase `MAJOR` for breaking public behavior.
- Increase `MINOR` for compatible new commands, fields, fixtures, docs, or capabilities.
- Increase `PATCH` for compatible fixes and small documentation corrections.

The Codex plugin manifest may include build metadata for local cache busting:

```text
1.5.0+codex.20260607133103
```

Treat the part before `+` as the release version. The `+codex.<timestamp>` suffix is only for refreshing the local Codex plugin cache and must not be used to imply a new semantic release.

Release tags should use the base version, for example:

```text
v1.0.0
```

## Public Stability Surface

The public stability surface is the behavior users, docs, CI, and downstream automation can rely on:

- stable command names, aliases, and primary meanings documented in `Docs/cli-contracts.md`
- stable exit code meanings
- documented top-level JSON fields and envelopes for `--json` commands
- write-safety defaults, write flags, confirmation flags, and refusal behavior
- managed artifact markers and bounded update paths used by `bootstrap`, `factory`, and `tune`
- plugin and skill entry points, including `repo-harness-tuner` and `codex-harness-setup`
- install, refresh, and local plugin cachebuster expectations documented in `Docs/install.md`
- stored harness history and eval score formats when later commands are expected to read them
- stored or emitted skill recommendation plans and adapter skill install boundaries
- emitted and generated harness contract sections: Scope, Access & Actions, Definition of Done, and Human Approval Points
- emitted next-action category values for the one-command assistant flow
- `release-check` fresh-copy validation expectations
- default Windows PowerShell compatibility for normal text output

Internal helper functions, private nested fields, text formatting, fixture internals, and wording in human-readable output may evolve unless they are explicitly documented as stable.

## Breaking Changes

A change is breaking when it makes a documented workflow, automation, or installed plugin expectation stop working without a migration path.

Breaking changes include:

- removing or renaming a stable command or alias
- removing, renaming, or changing the primary meaning of a stable flag
- removing or renaming documented top-level JSON fields
- changing the type or meaning of documented JSON fields in a way existing automation cannot safely ignore
- changing exit code meanings
- making a read-only command write by default
- weakening write-safety guarantees, confirmation requirements, or bounded write paths
- changing managed marker names so existing generated sections cannot be updated safely
- changing plugin name, skill IDs, install assumptions, or local refresh expectations
- making stored history or eval result files unreadable without a migration
- changing `recommend-skills` from adapter-only to external bulk install without a new documented approval path
- removing or silently weakening the generated harness contract boundaries for scope, access/actions, done criteria, or human approval points
- removing or silently changing documented next-action category meanings
- introducing text output that crashes in a default Windows PowerShell console

Breaking changes must be called out in `CHANGELOG.md` with `BREAKING:` and should update the relevant contract document.

## Non-Breaking Changes

Compatible changes include:

- adding a new command, optional flag, warning, or diagnostic
- adding JSON fields while preserving documented fields and meanings
- adding nested JSON details that automation can ignore
- changing human-readable text for clarity, as long as the documented concepts remain visible
- adding fixtures, validation checks, project-type detection, or factory evidence
- fixing behavior so it matches the documented CLI contract
- improving docs, examples, install notes, or troubleshooting guidance
- making a refusal clearer without changing a documented successful workflow

When in doubt, treat command names, exit codes, JSON top-level fields, and write safety as stable.

## Deprecation Policy

Prefer deprecation over removal.

For v1.x releases:

1. Add the replacement path to `CHANGELOG.md` under `Deprecated`.
2. Keep aliases or compatibility fields for at least one minor release when practical.
3. Update `Docs/cli-contracts.md`, `Docs/commands.md`, or `Docs/install.md` with the migration path.
4. Warn in human-readable output when that does not break JSON stdout or normal automation.
5. Remove only in a later major release, unless the old behavior is unsafe.

If a safety issue requires immediate removal, document the reason under `Removed` or `Security` and include the safest available migration.

## Changelog Rules

Use these sections in `CHANGELOG.md` when they apply:

- `Added`
- `Changed`
- `Deprecated`
- `Removed`
- `Fixed`
- `Security`

Use `BREAKING:` at the start of a bullet when the change affects the public stability surface. The bullet should name the affected command, flag, schema, install path, or artifact format and include a migration note.

Example:

```text
- BREAKING: `run-loop --json` no longer emits `summary.next_action`; use `summary.recommended_action` instead.
```

## Release Checklist

Before publishing or tagging a release:

1. Classify changes as breaking or non-breaking using this policy.
2. Update `CHANGELOG.md` with the release version and change categories.
3. Update `.codex-plugin/plugin.json` base version.
4. Run the plugin-creator cachebuster helper if Codex must refresh the local plugin.
5. Update affected contract docs, especially `Docs/cli-contracts.md`, `Docs/commands.md`, and `Docs/install.md`.
6. Run local validation from `Docs/install.md` and `Docs/AI/validation.md`.
7. Commit and push.
8. Confirm GitHub Actions passes on the branch or `main`.
9. Create and push the release tag using the base version, for example `v1.0.0`.
10. Confirm GitHub Actions passes on the tag.
11. Refresh the local Codex install if needed with `codex plugin add repo-harness-tuner@personal`.

Do not bump the semantic base version only because the cachebuster timestamp changed.
