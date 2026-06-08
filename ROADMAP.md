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

Status: released.

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

Status: released.

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

Status: implemented for CLI contracts, onboarding docs, install docs, and validation docs; release tagging and independent fresh-clone verification remain release checklist work.

Goal: make the plugin reliable enough for other users to install, understand, and repeat across projects.

Scope:

- Stabilize CLI names and output schemas.
- Finish installation, upgrade, reinstall, and troubleshooting docs.
- Define versioning and breaking-change policy in `Docs/versioning.md`.
- Make the README a one-request/one-command onboarding path instead of a full command manual.
- Keep CI coverage for fixture tests, plugin validation, skill validation, and smoke tests.
- Ensure first-time users can start with `doctor` or `run-loop` without reading the whole manual.

Done when:

- A fresh clone on a new PC can install or run the plugin from the documented steps without relying on local-only state.
- First-time usage docs cover empty projects, existing projects, Codex plugin projects, and projects that already have harness files.
- README explains the product as a one-request assistant: start with `run-loop` or `doctor`, let the plugin recommend the next step, and keep writes behind explicit approval.
- CLI command names, JSON schemas, exit codes, and write-safety behavior are documented and treated as stable unless a `Docs/versioning.md` breaking-change note is added.
- CI validates script compilation, fixture tests, plugin manifest validation, skill validation, harness checks, and broad CLI smoke tests.
- `doctor`, `run-loop`, `factory`, `eval`, `bootstrap`, and `tune` have examples that show read-only mode first and explicit write flags second.
- The changelog, tag, plugin manifest version, GitHub release state, and local reinstall flow are aligned for the v1.0.0 release.

## v1.1.0 - Adaptive Assistant Experience

Status: implemented for structured recommendations; scheduler-style automation remains future work.

Goal: make the one-request assistant feel more continuous while preserving explicit approval for writes and policy changes.

Scope:

- Add a clearer assistant-mode entry point if `doctor`/`run-loop` are not enough for first-time users.
- Emit structured adaptive cadence recommendations, not only prose next-review triggers.
- Propose human-involvement changes from history, eval, repeated misses, and user feedback.
- Keep automatic human-involvement changes approval-based; do not silently lower or raise the user's default policy.
- Explore scheduler/automation handoff docs or commands after release validation and fresh-clone verification are stable.

Done when:

- A user can start with one request or one command and receive a clear follow-up path for diagnosis, tuning, validation, and history recording.
- Repeated closed-loop signals produce a structured recommendation such as "shorten review interval" or "raise human involvement for release flow".
- Applying cadence or human-involvement changes remains explicit, reviewable, and documented in repo-local harness files.
- Fixture tests cover closed-loop adaptive cadence and human-involvement recommendations.

## v1.2.0 - Skill/Agent Recommendation

Status: implemented for minimal capability recommendations.

Goal: recommend only the smallest useful skill/agent capability set from repo evidence.

Scope:

- Rank repo-fit capabilities such as code review, TDD, security, docs, build repair, frontend UI, release checks, and harness curation.
- Decide whether built-in factory output is enough before suggesting an external catalog candidate.
- Cap recommendations at 1-3 and suppress low-evidence external suggestions.
- Include recommendations in `doctor` and `run-loop`.

Done when:

- `recommend-skills` emits a read-only recommendation plan with capabilities, reasons, evidence, and safety boundaries.
- Fixture tests cover recommendation count/source/capability and curator behavior.

## v1.3.0 - External Catalog Adapter

Status: implemented with ECC as an adapter-only seed catalog.

Goal: support ECC-style skill/agent candidates without turning this plugin into an ECC bulk installer.

Scope:

- Add ECC seed candidates for code review, TDD, security, build repair, E2E/front-end evidence, test coverage, and docs.
- Support optional `--catalog-root` discovery for a local ECC checkout.
- Keep native ECC hooks, MCP servers, slash commands, agents, marketplace edits, and external repo mutation outside the automatic path.

Done when:

- `--source ecc` can recommend specific ECC seed candidates.
- Missing local ECC checkout still works as a seed catalog plan without pretending native ECC is installed.

## v1.4.0 - Approved Install Flow

Status: implemented for Codex adapter skill installs.

Goal: make installation explicit, reviewable, and reversible.

Scope:

- Add `recommend-skills --write-plan` for `Docs/AI/skill-recommendations.md`.
- Add `recommend-skills --install --confirm-install` for generated Codex adapter skills.
- Preserve existing installed skills unless `--force` is used; require `--replace-unmanaged` for non-generated targets.
- Keep human-involvement 4/5 guarded by `--confirm-write`.

Done when:

- Install attempts without `--confirm-install` refuse with exit code 2.
- Confirmed installs write only small adapter `SKILL.md` folders under the selected skill root.

## v1.5.0 - Continuous Harness Curator

Status: implemented for history/eval-informed recommendation mode.

Goal: use history and eval evidence to decide whether to add, repair, keep, watch, or reduce skill guidance.

Scope:

- Add `skill_recommendations.curator` with baseline, repair, reduce, keep, and watch actions.
- Feed eval regressions, unchanged failures, readiness regression, process overhead, and human-involvement gaps into skill recommendation pressure.
- Make `run-loop` show skill recommendations and optionally write only the recommendation plan through `--write-recommended`.

Done when:

- Closed-loop fixture scenarios recommend repair-oriented skill candidates.
- Process-overhead signals can steer the curator toward reduction instead of more installs.
- No curator action silently installs skills or changes policy.

## Current Priority

The next implementation priority is **release validation and fresh-clone verification**. Use the v0.3.0 fixture suite, v0.5.0 factory quality assertions, v0.8.0 closed-loop history/eval fixtures, and v1.2-v1.5 recommendation assertions as the regression safety net.

Current working agreement:

1. Keep README slim: one request or one command first, then safety and links.
2. Keep `doctor` and `run-loop` as the one-command assistant surface.
3. Keep `recommend-skills` / `catalog` as adapter-only; do not bulk-install ECC.
4. Keep cadence, human-involvement, and install changes approval-based.
5. Finish release validation, fresh-clone verification, cachebuster refresh, and GitHub release/tag alignment before calling the public release done.

Implemented documentation anchors for this pass:

- `Docs/cli-contracts.md`: `#18` CLI contract scope.
- `Docs/install.md`: `#19` install, refresh, and troubleshooting flow.
- `Docs/commands.md`: full command reference split out of README.
- `Docs/versioning.md`: `#20` versioning, breaking-change classification, deprecation, changelog, and release checklist policy.
- `README.md` / `README_KO.md`: slim one-request onboarding, safety model, adaptive-loop explanation, and links to detailed docs.
- `doctor` / `run-loop`: v1.1 structured `adaptive` recommendations for cadence and human-involvement policy suggestions.
- `recommend-skills` / `catalog`: v1.2-v1.5 minimal skill recommendation, ECC seed adapter, approved install flow, and continuous curator scope.
