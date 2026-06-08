# CLI Contracts

This document defines the public command-line behavior to stabilize before the v1.0.0 release.

The goal is not to freeze every internal field forever. The goal is to make first-time users, docs, CI, and downstream automation safe to rely on the main command names, write-safety behavior, exit codes, and documented JSON envelopes.

## Stable Commands

These command names are treated as public:

| Command | Stability | Purpose |
| --- | --- | --- |
| `doctor` | Stable | Read-only one-command harness health check and next action. |
| `run-loop` | Stable | Read-only full analyze/diagnose/design/factory/tune/evaluate/history planning pass unless write flags are supplied. |
| `loop` | Stable alias | Alias for `run-loop`. |
| `next` | Stable alias | Friendly alias for `run-loop`; answers what Codex should do next. |
| `fixture-test` | Stable | Run fixture golden tests. |
| `release-check` | Stable | Run release validation and fresh-clone simulation checks. |
| `diagnose` | Stable | Score readiness and detect drift, overhead, and human-involvement gaps. |
| `design` | Stable | Build the next harness design plan from diagnosis. |
| `eval` | Stable | Build an evaluation plan or score recorded eval results. |
| `factory` | Stable | Build project-specific team and skill factory plans and optional artifacts. |
| `recommend-skills` | Stable | Recommend minimal repo-fit skill/agent capabilities and optional Codex adapter skill installs. |
| `catalog` | Stable alias | Alias for `recommend-skills`. |
| `bootstrap` | Stable | Dry-run or write a minimal repo harness. |
| `apply` | Stable alias | Alias for `bootstrap`; still requires `--write` to modify files. |
| `tune` | Stable | Generate dry-run tuning proposals and optional reviewed writes. |
| `history` | Stable | Summarize or append harness history records. |
| `repo` | Stable | Scan target repo harness files and project markers. |
| `overview` | Stable | Scan installed skills/plugins plus target repo harness evidence. |
| `skills` | Stable | List installed skills. |
| `plugins` | Stable | List installed plugins. |
| `patterns` | Stable | List worker patterns or generate a worker prompt. |
| `prompt` | Stable | Generate a `codex-harness-setup` prompt. |

Breaking changes to these names, aliases, or primary meanings need a changelog entry and a version-policy note in `Docs/versioning.md`.

## Exit Codes

| Exit code | Meaning |
| ---: | --- |
| `0` | Command completed successfully. Read-only commands may still report warnings, next actions, missing files, or dry-run proposals. |
| `1` | Validation failed or an unexpected runtime failure occurred. `fixture-test` returns `1` when one or more fixtures fail. |
| `2` | The command refused to continue because a safety precondition or CLI usage requirement was not satisfied. Examples include missing `--confirm-write`, missing `--confirm-install`, unsafe write policy, invalid argparse usage, or blocked unmanaged replacement. |

Commands should prefer a structured refusal with exit code `2` over partially applying a risky write.

## Write-Safety Contract

Read-only is the default. The following commands must not modify target files unless a write flag is supplied:

- `doctor`
- `run-loop`
- `loop`
- `next`
- `diagnose`
- `design`
- `eval`
- `factory`
- `recommend-skills`
- `catalog`
- `bootstrap`
- `apply`
- `tune`
- `history`
- `release-check`

Stable write flags:

| Flag | Commands | Contract |
| --- | --- | --- |
| `--write` | `bootstrap`, `apply`, `tune`, `history` | Enables file writes for the command's bounded target files. |
| `--write-plan` | `run-loop`, `loop`, `next`, `diagnose`, `design`, `eval`, `factory`, `recommend-skills`, `catalog` | Writes a durable plan document only. |
| `--write-recommended` | `run-loop`, `loop`, `next` | Applies only the bounded recommended low-risk harness action. |
| `--record-history` | `run-loop`, `loop`, `next` | Appends a harness history snapshot. |
| `--write-score` | `eval` | Appends eval score history after `--score`. |
| `--write-artifacts` | `factory` | Writes missing repo-local team and skill artifacts. |
| `--write-codex-skills` | `factory` | Writes generated Codex skill drafts under the configured output directory. |
| `--install-codex-skills` | `factory` | Installs generated Codex skills outside the target repo only with `--confirm-install`. |
| `--install` | `recommend-skills`, `catalog` | Installs only recommended Codex adapter skills outside the target repo; requires `--confirm-install`. |
| `--force` | write-capable commands | Allows overwriting generated or existing target files within the command's policy. |
| `--replace-unmanaged` | `factory`, `recommend-skills`, `catalog` | Allows replacement of unmanaged files only together with the documented force path. |
| `--confirm-write` | write-capable commands | Required when human involvement is 4 or 5. |

Write commands must keep refusing destructive operations, dependency changes, CI changes, install/uninstall, marketplace edits, and paths outside their documented scope unless the command explicitly exists for that action and requires explicit confirmation. `recommend-skills` never bulk-installs external catalogs; external ECC candidates are adapter-only unless a future explicitly documented command changes that contract.

For `doctor`, `run-loop`, `loop`, and `next`, `summary.next_action.command` must remain a preview/read-only command or dry-run/diff command. It must not include write, install, or policy-changing flags. When the action can write, record history, or persist a plan, the explicit approved command belongs in `summary.next_action.apply_command`.

## JSON Output

Commands with `--json` must emit valid JSON on stdout and should avoid non-ASCII console encoding failures by escaping Unicode when needed.

Stable top-level JSON fields:

| Command | Stable top-level fields |
| --- | --- |
| `doctor` | `schema`, `created_at`, `repo`, `phase`, `domain`, `options`, `status`, `summary`, `analyze`, `diagnose`, `closed_loop`, `adaptive`, `harness_contract`, `design`, `factory`, `skill_recommendations`, `tune`, `evaluate`, `history`, `commands` |
| `run-loop` / `loop` / `next` | Same top-level envelope as `doctor`, plus any write-result fields when write flags are used. |
| `diagnose` | `phase`, `cadence`, `human_involvement`, `human_involvement_policy`, `readiness`, `drift`, `process_overhead`, `human_involvement_enforcement`, `history_feedback`, `human_involvement_matrix`, `harness_design`, `adaptive` |
| `factory` | `schema`, `created_at`, `repo`, `domain`, `phase`, `project_type`, `factory_goal`, `harness_engine`, `repo_evidence`, `artifact_inventory`, `factory_quality`, `team_factory` |
| `recommend-skills` / `catalog` | `schema`, `created_at`, `repo`, `domain`, `phase`, `options`, `summary`, `capabilities`, `recommendations`, `curator`, `safety`, `commands` |
| `eval` | `schema`, `created_at`, `repo`, `phase`, `project_type`, `harness_readiness`, `human_involvement`, `worker_pattern`, `evaluation_mode`, `golden_tasks`, `runbook`, `result_schema` |
| `tune` | `schema`, `created_at`, `repo`, `phase`, `force`, `readiness`, `diagnosis`, `proposals`, `notes` |
| `bootstrap` / `apply` | `repo`, `phase`, `force`, `actions`, plus `results` when `--write` is used. |
| `history` | `count`, `parse_errors`, `by_type`, `by_worker_pattern`, `latest`, `readiness_min`, `readiness_max`, `readiness_latest`, `readiness_values`, `totals` |
| `fixture-test` | `schema`, `created_at`, `fixtures_root`, `count`, `passed`, `failed`, `results`, `journey_count`, `journey_passed`, `journey_failed`, `journeys` |
| `release-check` | `schema`, `created_at`, `source_root`, `mode`, `count`, `passed`, `failed`, `checks` |
| `repo` | `root`, `project_type`, `project_markers`, `files`, `package_scripts`, `docs_reports_count`, `missing_recommended` |
| `overview` | `skills`, `plugins`, `marketplace`, `repo`, `counts` |
| `skills` | `skills`, `count` |
| `plugins` | `plugins`, `marketplace`, `count` |
| `patterns` | `patterns`, or prompt fields when `--prompt` is used |

Nested fields may grow over time. Removing or renaming documented top-level fields before v2.0 requires a breaking-change note.

For `doctor`, `run-loop`, `loop`, and `next`, `summary.next_action` also includes `action_type`, `category`, `category_label`, and `category_summary`. `action_type` and `category` carry the same work-type value: one of `planning`, `development-support`, `review-validation`, `harness-tuning`, `skill-recommendation`, or `history`.

`summary.next_action.command` and `summary.next_action.preview_command` carry the same safe preview command. `summary.next_action.apply_command` is present only when the recommended action has a write, record, or plan-writing path that should run after user approval. `summary.next_action.approval_required` is `true` for those actions.

## Text Output

Text output is user-facing and may evolve for readability, but it must preserve these concepts:

- status/readiness/next action for `next`, `doctor`, and `run-loop`
- "what Codex found", "what Codex can do next", preview command, apply-after-approval command when relevant, approval boundary, and validation hints for `doctor`, `run-loop`, and `next`
- harness contract visibility for Scope, Access & Actions, Definition of Done, and Human Approval Points
- dry-run vs write distinction for `bootstrap`, `apply`, and `tune`
- refusal reason and required flag for write guards
- fixture pass/fail summary for `fixture-test`
- release pass/fail summary for `release-check`
- install/write target paths when commands write outside the current repo
- skill recommendation count, source, curator action, and adapter-only install boundary for `recommend-skills`

Text output must not crash in a default Windows PowerShell console. If a terminal cannot encode a character, the CLI should degrade gracefully instead of raising `UnicodeEncodeError`.

## Compatibility Checks

Before changing CLI output or write safety, run:

```powershell
python scripts\console.py overview --repo .
python scripts\console.py doctor --repo . --phase active-development --json
python scripts\console.py fixture-test
python scripts\console.py release-check
```

For broad validation, use the explicit file list in `Docs/AI/validation.md`; do not rely on PowerShell expanding `scripts/*.py`.
