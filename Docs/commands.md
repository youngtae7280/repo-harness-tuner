# Command Reference

Run these from the Repo Harness Tuner plugin directory unless noted otherwise.

For the stability contract behind these commands, see `Docs/cli-contracts.md`.

## Read-Only First

```powershell
python scripts\console.py overview --repo C:\path\to\repo
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "technical documentation"
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "technical documentation"
python scripts\console.py recommend-skills --repo C:\path\to\repo --phase active-development --domain "technical documentation"
python scripts\console.py fixture-test
```

## Plans And History

```powershell
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "technical documentation" --write-plan
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "technical documentation" --record-history --note "after first feature"
python scripts\console.py history --repo C:\path\to\repo
python scripts\console.py history --repo C:\path\to\repo --record --write --note "after first feature"
```

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

## JSON Output

```powershell
python scripts\console.py overview --repo C:\path\to\repo --json
python scripts\console.py doctor --repo C:\path\to\repo --phase prototype --json
python scripts\console.py run-loop --repo C:\path\to\repo --phase prototype --json
python scripts\console.py fixture-test --json
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

`doctor` and `run-loop` include an `adaptive` object in JSON output. It is recommendation-only:

- `adaptive.cadence` gives structured review pressure, recommended interval, next trigger, and evidence signals.
- `adaptive.human_involvement` can recommend keeping, raising, or lowering the default human-involvement level.
- `adaptive.human_involvement.approval_required` is `true` when a policy change is recommended.
- The plugin never silently changes cadence or human-involvement policy; apply those changes only after review.

`doctor` and `run-loop` also include `skill_recommendations`. It is recommendation-only:

- `skill_recommendations.recommendations` lists minimal built-in or ECC-seed candidates.
- `skill_recommendations.curator` says whether the current evidence suggests baseline, repair, reduce, keep, or watch.
- `skill_recommendations.safety` records that external catalog bulk install is disabled and adapter installs require approval.
