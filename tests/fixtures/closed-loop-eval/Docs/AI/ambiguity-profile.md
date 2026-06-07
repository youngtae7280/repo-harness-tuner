# Human Involvement Profile

| Level | Policy | Ask before | Proceed when |
| --- | --- | --- | --- |
| 1 | Maximum autonomy | Protected areas only | Routine local precedent is clear |
| 2 | Proceed with assumptions | User-visible direction changes | Existing patterns answer the choice |
| 3 | Infer from repo context | Hard-to-reverse or user-visible direction changes | Existing source of truth answers the question |
| 4 | Ask focused questions | Ambiguous scope, ownership, or UX tradeoff | A named source of truth answers it |
| 5 | Explicit approval | File edits, destructive operations, release or secret changes | User approved the exact change |

<!-- repo-harness-tuner:start:human-involvement -->
## Repo Harness Tuner Human Involvement Rules

Default human involvement: 3/5.
Default worker pattern: Visible Decision Thread (`visible-decision-thread`).
Default visibility: visible chat.

Ask before:
- Any destructive filesystem or data operation.
- Dependency, release, CI, secret, credential, migration, or privacy-sensitive changes.
- Product, roadmap, UX, narrative, or scope choices not answered by an existing source of truth.
- File edits when human involvement is 5 unless the user already approved the exact change.

Agent may decide:
- Routine implementation choices with clear repo precedent.
- Focused validation selection from `Docs/AI/validation.md`.
- Small docs/copy edits that preserve meaning.
<!-- repo-harness-tuner:end:human-involvement -->
