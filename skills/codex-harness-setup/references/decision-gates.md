# Decision Gates

Use this reference when deciding whether the default Codex loop is enough, how large the next work cycle should be, which harnesses are worth adding, and how strongly to enforce them.

## Contents

- [Native Capability Check](#native-capability-check)
- [Harness Overlap Test](#harness-overlap-test)
- [Cycle Sizing Gate](#cycle-sizing-gate)
- [Harness Selection Review](#harness-selection-review)
- [Human Review Budget](#human-review-budget)
- [Enforcement Ladder](#enforcement-ladder)
- [Validation Fit](#validation-fit)
- [Report Persistence Gate](#report-persistence-gate)
- [Effectiveness Review](#effectiveness-review)
- [Retirement and Demotion Rules](#retirement-and-demotion-rules)

## Native Capability Check

Before adding or keeping a harness, identify what is already covered by:

- the coding agent's default loop,
- package scripts and local commands,
- lint, type, test, build, or format tools,
- pre-commit hooks or CI,
- framework conventions,
- PR templates or team review habits.

Keep a proposed harness only if it adds one of:

- project-specific decision rule,
- source-of-truth path,
- evidence requirement,
- risk escalation trigger,
- known-failure prevention rule,
- faster or more focused check than a broad default,
- explicit permission boundary or human approval point.

If a rule only repeats generic behavior such as "plan first", "run tests", or "summarize changes", delete it or narrow it to the cases where the default loop is not enough.

## Bad-to-Good Harness Rules

Use these as rewrite patterns when a harness feels broad or repetitive:

| Bad rule | Better rule |
|---|---|
| Always run all tests. | For changes touching shared contracts, run the focused contract test first; run the full suite only before broad integration. |
| Always write a detailed plan. | Write a plan before edits only when scope is ambiguous, cross-module, high-risk, or needs human approval. |
| Always create a full report. | Persist a report only for staged/high-risk cycles, multi-agent evidence, or decisions future agents must reuse. |
| Always do a security review. | Activate security review only for auth, permissions, secrets, user data, file/URL/path handling, dependencies, CI, or logging. |
| Never skip validation. | If validation is unavailable or irrelevant, state why and provide the smallest useful alternative evidence. |

## Harness Overlap Test

For each proposed rule or file, ask:

- Is this already done by the default agent loop?
- Is this already enforced by CI, package scripts, hooks, framework conventions, or review policy?
- Does the rule tell the agent when to behave differently, or only repeat generic advice?
- Does it produce evidence a human can inspect?
- Would removing this rule materially increase risk?

Rules that fail this test should be removed, narrowed, moved into a lower enforcement level, or kept only in a project profile as a temporary note.

## Cycle Sizing Gate

Treat the user's full desired outcome as `1.0`. Do not make `1.0` the default implementation batch.

Classify the next cycle:

- **single-pass**: 0.7-1.0. Small, clear, low-risk, easy to review, easy to revert.
- **mini-cycle**: 0.2-0.4. Moderate behavior change, isolated bug fix, limited feature work.
- **staged-cycle**: 0.1-0.25. Ambiguous, cross-layer, product/architecture/UX judgment, multiple components.
- **high-risk-cycle**: 0.05-0.15. Security, permissions, payments, user data, migrations, release, public API, destructive operations, difficult rollback.

Do not optimize for finishing everything in one pass. Optimize for the largest safe, reviewable, reversible unit of progress.

Split before implementation when:

- requirements are ambiguous,
- tests or validation are weak,
- expected changes cross layers or ownership boundaries,
- security, data, permissions, release, or public APIs are involved,
- the diff would be hard for a human to review,
- rollback would be difficult.

Use larger cycles only when scope is clear, validation is available, the change is isolated, the result is easy to inspect, and rollback is simple.

## Harness Selection Review

For each selected harness, record:

- risk controlled,
- why the risk is real for this project or task,
- why native agent/tooling behavior is not enough,
- concrete evidence that will prove the harness worked,
- expected cost or overhead,
- cheaper alternative considered, if any.

For each skipped harness, record:

- why it is not needed now,
- what assumption makes it safe to skip,
- what future change would activate it.

If a selected harness has no meaningful evidence or decision impact, remove or downgrade it.

## Human Review Budget

A good cycle creates an output a human can review confidently.

Prefer cycles where:

- changed files are limited,
- one core behavior changes,
- validation evidence is clear,
- rollback is simple,
- unrelated refactors are absent,
- skipped checks are explained.

Split before implementation if the expected diff is too large, mixes unrelated concerns, or forces the human reviewer to infer evidence from logs or broad changes.

## Enforcement Ladder

Start with the lightest enforcement that can control the risk:

1. No harness.
2. Advisory note in `AGENTS.md`.
3. Checklist or profile in `docs/ai/`.
4. Script or smoke check.
5. Local hook or task-runner gate.
6. CI gate.
7. Mandatory human approval.

Do not add CI gates, new dependencies, destructive scripts, release blockers, or mandatory approvals without user approval. Promote only after repeated value is shown.

## Validation Fit

Run validation proportional to the harness edit:

- Markdown/lint checks for docs when available.
- Shell syntax checks for new shell scripts.
- Dry-run or help output for new scripts.
- Fast existing test/lint/typecheck only if harness files affect code, commands, or CI behavior.
- Broad validation only when the changed harness can affect broad execution.

If validation cannot run, distinguish environment blockers from product/harness blockers.

## Report Persistence Gate

Create persistent reports only when:

- the cycle is staged or high-risk,
- multiple agents or subagents are involved,
- QA/security/code review evidence must survive the thread,
- the decision affects future harness selection,
- the user explicitly asks for report files.

For low-risk single-pass work, use final-response summary only.

## Effectiveness Review

Review frequency:

- every task: lightweight fit check,
- every 3-5 meaningful cycles: short effectiveness review,
- weekly or per sprint: repo-level `harness-profile.md` review,
- immediately after regression, security issue, data issue, release failure, unreadable diff, or repeated agent mistake.

Record:

- which harnesses caught issues,
- which harnesses were useful but found no issues,
- which harnesses were unnecessary overhead,
- which missing harness would have reduced risk,
- what should be added, removed, shortened, promoted to automation, or demoted.

## Retirement and Demotion Rules

Retire or reduce a harness when it:

- repeatedly adds overhead without evidence value,
- duplicates a stronger tool, CI gate, framework convention, or review habit,
- becomes stale or contradicts current project structure,
- causes agents to avoid focused work,
- is too broad to change decisions,
- is used only as generic good advice.

Rewrite instead of retiring when the risk is real but the rule is vague, too broad, hard to apply, or missing a concrete evidence requirement.
