# Review Checklists

Use these checklists only when the corresponding risk is active. Do not paste every checklist into every task.

## Contents

- Native Capability Review
- Harness Selection Review
- Cycle Sizing Review
- TDD and Test Review
- Security Review
- Code Review
- UI Review
- Data Review
- Release Review
- Harness Effectiveness Review

## Native Capability Review

- Is the proposed rule already handled by the agent, toolchain, CI, or framework?
- Does the harness add a project-specific decision, source of truth, evidence requirement, or escalation trigger?
- Is there a cheaper existing command or review habit that controls the same risk?
- Would this rule help future agents, or only restate good practice?
- Should the rule be deleted, narrowed, or moved into a project profile?

## Harness Selection Review

For selected harnesses:
- What risk does this harness control?
- Why is this risk real for this project or task?
- What concrete evidence proves this harness was used correctly?
- What is the expected cost or overhead?
- Is there a cheaper harness that controls the same risk?

For skipped harnesses:
- Why is this harness not needed now?
- What assumption makes it safe to skip?
- What future change would activate it?

## Cycle Sizing Review

- Can a human review the expected diff confidently?
- Is the change reversible?
- Are requirements clear enough to implement now?
- Are tests or other evidence strong enough to support a larger cycle?
- Does the task cross modules, trust boundaries, persistence, release, or public APIs?
- Should the first cycle stop at analysis, reproduction, or harness setup instead of implementation?

## TDD and Test Review

- Is there a failing test, reproduction, fixture, or smoke path for the behavior?
- Does the test fail for the right reason before the fix, when practical?
- Is the test focused enough to be useful for agent iteration?
- Are edge cases covered in proportion to risk?
- Were broad tests avoided when focused tests were enough?
- Was skipped test-first work justified with an alternate validation path?

## Security Review

- Does the change touch a trust boundary?
- Are secrets and personal data kept out of code, logs, prompts, fixtures, screenshots, and reports?
- Are auth and permission checks explicit and preserved?
- Are untrusted inputs validated before use?
- Are file paths, URLs, shell commands, serialized data, and uploads/downloads handled safely?
- Are dependencies, CI, and config changes justified and reviewed?
- Are error messages safe but still useful?
- Is any human approval needed before merge or deploy?

## Code Review

- Is the change limited to the requested scope?
- Is the diff small enough to review?
- Is the solution simpler than the problem requires, not simpler than safety permits?
- Are contracts, public APIs, and backward compatibility preserved?
- Are failure modes and edge cases handled?
- Are tests meaningful rather than merely increasing coverage?
- Did the change avoid duplicating existing utilities or patterns?
- Are observability and diagnostics adequate for the risk?
- Is any generated, migration, or production-sensitive file changed intentionally?

## UI Review

- Does the capture prove the acceptance criteria?
- Are loading, empty, error, and permission states considered when relevant?
- Are keyboard, focus, and screen reader concerns considered when relevant?
- Are mobile/responsive breakpoints checked when relevant?
- Is the visual change isolated from unrelated styling churn?
- If capture failed, was the blocker environmental or product-related?

## Data Review

- Is the operation reversible, idempotent, or safely retryable?
- Are before/after invariants defined?
- Is the migration/backfill tested against fixture or staging-like data?
- Is there an approval gate for destructive operations?
- Are rollback and monitoring expectations recorded?
- Are data assumptions explicitly documented?

## Release Review

- Are versioning, changelog, build artifact, signing, and publishing steps known?
- Is rollback documented?
- Are environment-specific settings separated from code?
- Are smoke checks defined for the released artifact?
- Is the release gate advisory, local, CI, or human approval?

## Harness Effectiveness Review

- Which harness caught an issue?
- Which harness was useful but found no issue?
- Which harness created overhead without evidence value?
- Which missing harness would have reduced risk?
- Which stale rule should be removed?
- Should any advisory rule be promoted to a script/CI gate?
- Should any enforced rule be demoted or retired?
