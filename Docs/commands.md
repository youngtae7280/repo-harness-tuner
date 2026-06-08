# Command Reference

Run these from the Harness Tuner plugin directory unless noted otherwise.

The display name is **Harness Tuner**. The technical plugin id remains `repo-harness-tuner`.

For the stability contract behind these commands, see `Docs/cli-contracts.md`.

## One-Command Entry

In Codex chat, explicitly name Harness Tuner when you want project-direction routing:

```text
Use $repo-harness-tuner to inspect this repo read-only and tell me the next safe step.
Do not open apps, run tests, write files, or install anything; show preview/apply boundaries.
```

Short prompts are fine when they include the routing intent:

```text
What should I do next? Use Harness Tuner read-only first.
Plan this project with Harness Tuner: scope, definition of done, and approval points first.
Draft a roadmap with Harness Tuner, but show the draft first and ask before writing files.
Plan the next milestone and development sequence with Harness Tuner read-only first.
Review this repo with Harness Tuner, but only summarize the validation loop.
```

The skill should treat those as `next`-style requests first: inspect the repo, label the work type, propose one next action, show approval boundaries, and suggest validation.

Do not rely on a bare chat message like `next`. In chat, `next` is ambiguous and can be interpreted as continuing prior work. The CLI command is still named `next`; chat prompts should explicitly invoke Harness Tuner.

In repos with strong project-specific skills, Harness Tuner should route the work type and approval boundary first. Treat domain-specific skills as recommended next steps, not as the entry pass.

Roadmap requests should produce a chat draft by default: phases, milestones, priorities, validation gates, dependencies, risks, approval points, and the next review trigger. Creating or updating `ROADMAP.md`, `Docs/AI/*`, issues, tasks, release notes, or milestone files requires explicit approval.

Use `next` when you want the plugin to answer "what should Codex do next?" without writing files:

```powershell
python scripts\console.py next --repo C:\path\to\repo --phase active-development --domain "technical documentation"
```

`next` is a friendly alias for `run-loop`. It prints what Codex found, what Codex can do next, the preview command, the apply-after-approval command when a write is useful, what needs approval, and validation to run.

The recommended next action includes a work type: `planning`, `development-support`, `review-validation`, `harness-tuning`, `skill-recommendation`, or `history`.

For `next`, `doctor`, and `run-loop`, `summary.next_action.command` is the safe preview command and matches `summary.next_action.preview_command`. If the recommended action can write files, record history, or write a plan, `summary.next_action.apply_command` contains the explicit command to run only after approval.

## Read-Only First

```powershell
python scripts\console.py overview --repo C:\path\to\repo
python scripts\console.py next --repo C:\path\to\repo --phase active-development --domain "technical documentation"
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "technical documentation"
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "technical documentation"
python scripts\console.py recommend-skills --repo C:\path\to\repo --phase active-development --domain "technical documentation"
python scripts\console.py fixture-test
python scripts\console.py release-check
```

## Plans And History

```powershell
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "technical documentation" --write-plan
python scripts\console.py next --repo C:\path\to\repo --phase active-development --domain "technical documentation" --write-plan
python scripts\console.py next --repo C:\path\to\repo --phase active-development --domain "technical documentation" --write-recommended
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "technical documentation" --record-history --note "after first feature"
python scripts\console.py history --repo C:\path\to\repo
python scripts\console.py history --repo C:\path\to\repo --record --write --note "after first feature"
```

`--write-recommended` applies only the bounded next action selected by `next` / `run-loop`. Review `summary.next_action.apply_command` or the text output's "Apply after approval" command first. It can write managed harness docs, repo-local factory artifacts, skill recommendation plans, or a baseline harness history record when that exact action is recommended.

## Diagnose And Design

```powershell
python scripts\console.py diagnose --repo C:\path\to\repo --phase new-project
python scripts\console.py diagnose --repo C:\path\to\repo --phase new-project --human-involvement 3 --emit-prompt
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --module "Ending taxonomy: 5"
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --write-status
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development --write-plan
python scripts\console.py design --repo C:\path\to\repo --phase active-development --human-involvement 3
```

## Factory

```powershell
python scripts\console.py factory --repo C:\path\to\repo --domain "Unity tycoon game UI" --phase active-development
python scripts\console.py factory --repo C:\path\to\repo --domain "deep research" --team-size 3 --write-plan
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --write-artifacts
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --write-codex-skills
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --install-codex-skills --confirm-install
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --write-artifacts --force --replace-unmanaged
```

## Skill And Catalog Recommendations

```powershell
python scripts\console.py recommend-skills --repo C:\path\to\repo --phase active-development --domain "technical documentation"
python scripts\console.py recommend-skills --repo C:\path\to\repo --phase active-development --domain "technical documentation" --source builtin,ecc
python scripts\console.py recommend-skills --repo C:\path\to\repo --phase active-development --domain "technical documentation" --source ecc --limit 2
python scripts\console.py recommend-skills --repo C:\path\to\repo --phase active-development --domain "technical documentation" --write-plan
python scripts\console.py recommend-skills --repo C:\path\to\repo --phase active-development --domain "technical documentation" --install --confirm-install
python scripts\console.py catalog --repo C:\path\to\repo --phase active-development --domain "technical documentation"
```

`recommend-skills` ranks minimal repo-fit capabilities such as code review, TDD, security, docs, build repair, frontend UI, release checks, and harness curation. The command is read-only by default.

Safety boundaries:

- Recommendations are capped at 3.
- ECC is a seed catalog source, not a bulk installer.
- `--write-plan` writes only `Docs/AI/skill-recommendations.md`.
- `--install --confirm-install` installs Codex adapter skills only.
- External hooks, MCP servers, slash commands, native agents, marketplace edits, and human-involvement policy changes are not silently installed or applied.

## Worker Patterns

```powershell
python scripts\console.py patterns
python scripts\console.py patterns --prompt background-review --repo C:\path\to\repo --phase active-development --scope "validation drift"
```

## Evaluation

```powershell
python scripts\console.py eval --repo C:\path\to\repo --phase active-development --human-involvement 3
python scripts\console.py eval --repo C:\path\to\repo --phase active-development --write-plan
python scripts\console.py eval --score C:\path\to\eval-results.json
python scripts\console.py eval --repo C:\path\to\repo --score C:\path\to\eval-results.json --write-score --note "after factory team tune"
```

## Bootstrap And Tune

```powershell
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 3
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 3 --write
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --human-involvement 5 --write --confirm-write
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --dry-run --diff
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --write
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --human-involvement 4 --write --confirm-write
python scripts\console.py apply --repo C:\path\to\repo --phase new-project --write --force
```

## Scanners And Prompt Generation

```powershell
python scripts\console.py skills
python scripts\console.py plugins
python scripts\console.py repo --repo C:\path\to\repo
python scripts\console.py prompt --repo-type "Vite + TypeScript + JSON game prototype" --phase prototype --human-involvement 2
```

## Release Validation

```powershell
python scripts\console.py release-check
python scripts\console.py release-check --json
```

`release-check` runs a fresh-copy simulation of the current checkout. It validates plugin JSON, bundled skill frontmatter, Python compilation, fixture tests including user journeys, `next`/`doctor` JSON contracts, Windows-console text output tolerance, and bootstrap/harness-check behavior in a clean temp target.

## JSON Output

```powershell
python scripts\console.py overview --repo C:\path\to\repo --json
python scripts\console.py next --repo C:\path\to\repo --phase prototype --json
python scripts\console.py doctor --repo C:\path\to\repo --phase prototype --json
python scripts\console.py run-loop --repo C:\path\to\repo --phase prototype --json
python scripts\console.py fixture-test --json
python scripts\console.py release-check --json
python scripts\console.py diagnose --repo C:\path\to\repo --phase prototype --json
python scripts\console.py design --repo C:\path\to\repo --phase prototype --json
python scripts\console.py factory --repo C:\path\to\repo --domain "technical documentation" --json
python scripts\console.py recommend-skills --repo C:\path\to\repo --domain "technical documentation" --json
python scripts\console.py patterns --json
python scripts\console.py eval --repo C:\path\to\repo --phase prototype --json
python scripts\console.py eval --score C:\path\to\eval-results.json --json
python scripts\console.py eval --repo C:\path\to\repo --score C:\path\to\eval-results.json --write-score --json
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --json
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --json
python scripts\console.py history --repo C:\path\to\repo --record --json
python scripts\console.py skills --json
python scripts\console.py plugins --json
python scripts\console.py repo --repo C:\path\to\repo --json
```

`next`, `doctor`, and `run-loop` include an `adaptive` object in JSON output. It is recommendation-only:

- `adaptive.cadence` gives structured review pressure, recommended interval, next trigger, and evidence signals.
- `adaptive.human_involvement` can recommend keeping, raising, or lowering the default human-involvement level.
- `adaptive.human_involvement.approval_required` is `true` when a policy change is recommended.
- The plugin never silently changes cadence or human-involvement policy; apply those changes only after review.

`summary.next_action` includes the assistant work type:

- `action_type`: stable work-type slug such as `planning`, `review-validation`, or `history`.
- `category`: stable slug such as `planning`, `review-validation`, or `history`.
- `category_label`: user-facing label.
- `category_summary`: short explanation of what Codex is doing at that step.
- `command` / `preview_command`: the safe command to inspect before applying changes.
- `apply_command`: present only when a write, record, or plan-writing command is useful after approval.
- `approval_required`: `true` when `apply_command` should be reviewed before use.

`next`, `doctor`, and `run-loop` also include `skill_recommendations`. It is recommendation-only:

- `skill_recommendations.recommendations` lists minimal built-in or ECC-seed candidates.
- `skill_recommendations.curator` says whether the current evidence suggests baseline, repair, reduce, keep, or watch.
- `skill_recommendations.safety` records that external catalog bulk install is disabled and adapter installs require approval.

`next`, `doctor`, and `run-loop` also include `harness_contract`:

- `scope` separates what Codex may own from what it must not take over.
- `access_actions` separates visible information, allowed actions, forbidden actions, and approval-required actions.
- `definition_of_done` lists expected validation, closeout evidence, skipped-check handling, and remaining-risk reporting.
- `human_approval_points` records the default human-involvement level, always-ask triggers, and area matrix.
