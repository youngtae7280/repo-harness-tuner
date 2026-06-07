# Human Involvement Profile

This file defines when Codex should ask before editing and when it may infer from repo context.

Default human involvement: 3/5

| Human involvement | Behavior | Ask before | Agent may decide |
| --- | --- | --- | --- |
| 1 | Mostly autonomous | Protected areas, destructive operations, secrets, release, dependencies | Small implementation details from local patterns |
| 2 | Proceed with assumptions | User-visible direction changes, unclear ownership, protected areas | Routine refactors, docs/copy edits, focused validation |
| 3 | Balanced default | Hard-to-reverse or user-visible direction changes | Ordinary implementation choices with clear repo precedent |
| 4 | Ask focused questions | File edits when source of truth is unclear; product/UX/scope tradeoffs | Read-only inspection and diagnosis |
| 5 | Explicit approval | Any file edit unless the user already approved the exact change | Read-only inspection only |

## Always Ask Before
- Destructive filesystem or data operations.
- Dependency, release, CI, secret, credential, migration, or privacy-sensitive changes.
- Product, roadmap, UX, narrative, or scope choices not answered by an existing source of truth.
- Overwriting existing harness files with generated content.

## Safe To Decide
- Formatting, wording, or small docs improvements that preserve meaning.
- Following clearly established local code and documentation patterns.
- Choosing focused validation from `Docs/AI/validation.md`.
