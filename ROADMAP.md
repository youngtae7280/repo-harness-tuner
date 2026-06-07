# Repo Harness Tuner Roadmap

Repo Harness Tuner is moving toward a stable 1.0 release in staged milestones. The product goal stays fixed:

- **Factory**: generate project-specific Codex teams, role prompts, skill plans, and orchestration artifacts.
- **Engine**: analyze, diagnose, design, tune, evaluate, and continuously improve repo-local Codex harnesses.

For machine-to-machine continuation, use [HANDOFF.md](HANDOFF.md).

## v0.3.0 - Fixture Golden Tests

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

Goal: make generated team and skill artifacts more specific to repo evidence.

Scope:

- Use repo evidence in generated skill triggers and role prompts.
- Reduce generic skill output when concrete project markers are available.
- Detect generated skill conflicts, stale generated artifacts, and missing update paths.
- Improve `factory --write-codex-skills` output quality and validation guidance.

## v0.8.0 - Stronger Closed Loop

Goal: make evaluation and history directly influence future diagnosis, tuning, and factory design.

Scope:

- Feed `eval --score` results into diagnosis pressure and tuning proposals.
- Promote repeated fixture failures into concrete harness recommendations.
- Improve history summaries so repeated drift, overhead, and human-involvement gaps change the next action.
- Add safer auto-apply options for low-risk recurring harness fixes.

## v1.0.0 - Stable Public Release

Goal: make the plugin reliable enough for other users to install, understand, and repeat across projects.

Scope:

- Stabilize CLI names and output schemas.
- Finish installation, upgrade, reinstall, and troubleshooting docs.
- Define versioning and breaking-change policy.
- Keep CI coverage for fixture tests, plugin validation, skill validation, and smoke tests.
- Ensure first-time users can start with `doctor` or `run-loop` without reading the whole manual.

## Current Priority

The next implementation milestone is **v0.3.0 - Fixture Golden Tests**. Avoid expanding workspace discovery, GUI work, or deeper automation until the fixture suite exists, because the fixture suite is the safety net for every later milestone.
