# Harness Profile

Project type: Vite/Node frontend.

Human involvement: 3/5. Codex may infer from local patterns, but should ask before hard-to-reverse or user-visible direction changes.

Worker visibility: use a single agent for small scoped changes. Use background review for validation drift or meaningful UI risk. Use visible chats for product, roadmap, UX, release, or scope decisions.

Validation cadence: use focused checks for narrow changes and broad checks before release-facing work.

## Harness Contract

### Scope

Agent may:
- Analyze Vite/Node frontend tasks and propose the next smallest safe implementation, review, validation, or harness-tuning step.
- Edit repo files only inside the requested task and existing local patterns.
- Recommend focused worker or skill support when repo evidence justifies it.

Agent must not:
- Treat broad autonomy as permission to bypass approval boundaries.
- Deploy, release, publish, send external messages, mutate production data, or change dependencies/CI/secrets/marketplace state silently.

### Access & Actions

Can see:
- Repo-local source, docs, package scripts, `AGENTS.md`, and `Docs/AI/*`.

Can do:
- Read files, summarize evidence, propose diffs, make approved edits, and run or recommend focused validation.

Must not do:
- Delete data, add broad gates, install external components, or expand process for every small task without evidence.

Approval required:
- Dependency, release, CI, secret, credential, migration, marketplace, privacy-sensitive, destructive, or user-visible direction changes.

### Definition of Done

Required evidence:
- Changed files are named.
- The reason for each meaningful change is summarized.
- Focused validation is run, or a skipped check is explained.
- Remaining risk and approval needs are stated.

### Human Approval Points

- Default human involvement: 3/5.
- Ask before product, roadmap, UX, release, dependency, CI, secret, migration, destructive, privacy-sensitive, or hard-to-reverse changes.
- Human involvement 5 means no file edits without explicit approval.
