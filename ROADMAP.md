# Repo Harness Tuner Roadmap

Repo Harness Tuner is moving toward a stable 1.0 release in staged milestones. The product goal stays fixed:

- **Factory**: generate project-specific Codex teams, role prompts, skill plans, and orchestration artifacts.
- **Engine**: analyze, diagnose, design, tune, evaluate, and continuously improve repo-local Codex harnesses.

For machine-to-machine continuation, use [HANDOFF.md](HANDOFF.md).

## v0.3.0 - Fixture Golden Tests

Status: released.

Goal: make the harness engine measurably testable across representative project shapes.

Scope:

- Add fixture repositories for:
  - empty/new project,
  - existing Vite/Node project,
  - Unity project,
  - Codex plugin project,
  - project with existing harness/skills.
- Add a fixture runner that executes `doctor`, `run-loop`, `diagnose`, `factory`, `eval`, and safe write-guard checks against those fixtures.
- Add expected-result assertions for project type, readiness band, next action, golden task count, and write safety behavior.
- Add CI coverage for the fixture runner.
- Document how to add a new fixture and expected assertions.

Done when:

- `python scripts/console.py fixture-test` or an equivalent command runs all fixture golden tests locally.
- GitHub Actions runs the fixture suite on every push and pull request.
- The fixture suite catches regressions in project detection, bootstrap recommendation, evaluation planning, and human-involvement write guards.
- The changelog has a v0.3.0 entry with the fixture coverage listed.

## v0.5.0 - Factory Output Quality

Status: next.

Goal: make generated team and skill artifacts more specific to repo evidence.

Scope:

- Use repo evidence in generated skill triggers and role prompts.
- Reduce generic skill output when concrete project markers are available.
- Detect generated skill conflicts, stale generated artifacts, and missing update paths.
- Improve `factory --write-codex-skills` output quality and validation guidance.

Done when:

- Factory output includes concrete repo evidence such as detected project type, key scripts, harness files, validation commands, existing generated artifacts, and relevant source markers.
- Generated skill drafts include repo-specific triggers, boundaries, validation guidance, and anti-generic checks instead of broad reusable boilerplate.
- `factory` reports stale generated artifacts, conflicting planned skill ids, existing installed/generated skill overlap, and a recommended update path.
- `factory --write-artifacts` and `factory --write-codex-skills` update their generated outputs without silently overwriting unrelated user-authored content.
- Fixture coverage includes at least one assertion that guards against generic factory output for a project with concrete markers.
- README, README_KO, and the skill instructions explain when to use factory planning, repo-local artifacts, Codex skill drafts, and confirmed skill install.

## v0.8.0 - Stronger Closed Loop

Goal: make evaluation and history directly influence future diagnosis, tuning, and factory design.

Scope:

- Feed `eval --score` results into diagnosis pressure and tuning proposals.
- Promote repeated fixture failures into concrete harness recommendations.
- Improve history summaries so repeated drift, overhead, and human-involvement gaps change the next action.
- Add safer auto-apply options for low-risk recurring harness fixes.

Done when:

- `eval --score` can write or import a durable result record that future `diagnose`, `tune`, and `factory` runs can read.
- Repeated history signals change diagnosis pressure, selected next action, worker pattern recommendation, or factory plan content in a test-covered way.
- Fixture tests cover at least one history-informed diagnosis path and one eval-score-informed recommendation path.
- Low-risk auto-apply is limited to managed sections or newly created harness docs, and it refuses deletion, dependency changes, CI changes, install/uninstall, marketplace edits, and broad rewrites.
- `run-loop` explains when it used history/eval evidence and when it ignored stale or insufficient evidence.

## v1.0.0 - Stable Public Release

Goal: make the plugin reliable enough for other users to install, understand, and repeat across projects.

Scope:

- Stabilize CLI names and output schemas.
- Finish installation, upgrade, reinstall, and troubleshooting docs.
- Define versioning and breaking-change policy.
- Keep CI coverage for fixture tests, plugin validation, skill validation, and smoke tests.
- Ensure first-time users can start with `doctor` or `run-loop` without reading the whole manual.

Done when:

- A fresh clone on a new PC can install or run the plugin from the documented steps without relying on local-only state.
- First-time usage docs cover empty projects, existing projects, Codex plugin projects, and projects that already have harness files.
- CLI command names, JSON schemas, exit codes, and write-safety behavior are documented and treated as stable unless a breaking-change note is added.
- CI validates script compilation, fixture tests, plugin manifest validation, skill validation, harness checks, and broad CLI smoke tests.
- `doctor`, `run-loop`, `factory`, `eval`, `bootstrap`, and `tune` have examples that show read-only mode first and explicit write flags second.
- The changelog, tag, plugin manifest version, GitHub release state, and local reinstall flow are aligned for the v1.0.0 release.

## Current Priority

The next implementation milestone is **v0.5.0 - Factory Output Quality**. Use the v0.3.0 fixture suite as the regression safety net for every later milestone.
