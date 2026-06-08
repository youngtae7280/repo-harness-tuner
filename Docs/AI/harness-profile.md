# Harness Profile

Project type: Codex plugin project (`codex-plugin`)
Phase: `active-development`
Human involvement: 3/5
Recommended cadence: Run a lightweight fit check every task, a short harness review every 3-5 meaningful cycles, and a full review after missed regressions.
Next review trigger: after the next harness change or repeated agent miss

## Primary Risks
- plugin manifest and marketplace metadata drift
- skill frontmatter or trigger wording becoming invalid
- CLI smoke coverage missing generated factory and install flows
- Windows console compatibility for public CLI output

## Baseline Harness
- `AGENTS.md`: short entrypoint for Codex behavior.
- `Docs/AI/harness-profile.md`: cycle sizing, worker pattern, and review cadence.
- `Docs/AI/validation.md`: focused and broad validation guidance.
- `Docs/AI/ambiguity-profile.md`: human-involvement and ask-before-edit rules.

## Cycle Budget Policy
- Default work command budget: up to 3 cycles, stopping earlier when done.
- Small docs, copy, or single-file fixes: 1-2 cycles.
- Normal feature, harness, or multi-file improvements: up to 3 cycles.
- Shared contracts, CLI behavior, plugin metadata, validation-flow, or factory/engine changes: up to 5 cycles.
- Release, CI, install, marketplace, dependency, destructive, or hard-to-reverse changes: one read/preview cycle, then ask before apply.
- At the budget limit, close out with changed/proposed files, validation evidence or skipped-check reason, remaining risks, and next safe options.

## Worker Pattern
- Selected pattern: Single Agent (`single-agent`).
- Visibility: single visible thread by default.
- Coordination: one main thread owns the task board, sequencing, and final acceptance.

Selection reasons:
- current harness is fit enough for a single-thread loop
- escalate to a supervisor cycle only after repeated agent misses, high-risk release work, or multi-file harness restructuring

## Usually Skip
- New CI gates, release blockers, dependencies, or destructive scripts unless repeated evidence justifies them and the user approves.
- Persistent reports for tiny changes.
- Visible specialist chats when only final findings matter.

<!-- repo-harness-tuner:start:harness-contract -->
## Harness Tuner Harness Contract

### Scope

Agent may:
- analyze the Codex plugin project repo and diagnose Codex workflow or harness gaps
- propose the next smallest safe action for planning, implementation support, review, validation, or harness tuning
- edit repo files only when the user requested the work and the command path has an explicit write flag
- recommend minimal skill/worker support when repo evidence justifies it

Agent must not:
- treat 'do everything automatically' as permission to bypass approval boundaries
- deploy, release, publish, send external messages, process payments, or mutate production data
- silently change human-involvement policy, cadence policy, dependencies, CI, secrets, credentials, marketplace entries, or install state

### Access & Actions

Can see:
- repo-local source files and project documentation relevant to the current request
- `AGENTS.md` and `Docs/AI/*` harness files
- native validation commands, CI hints, recent reports, harness history, and eval score records when present

Can do:
- read files and summarize evidence
- create reviewable plans, dry-run diffs, and repo-local harness docs under `AGENTS.md` or `Docs/AI/*`
- run or recommend the nearest focused validation command and record skipped-check reasons
- record concise harness history or eval scores only through explicit write flags

Must not do:
- delete data or files outside the documented bounded write path
- enable external hooks, MCP servers, slash commands, native agents, or marketplace changes through recommendation commands
- broaden validation, reporting, or worker process for every small task without evidence

Approval required:
- dependency, release, CI, secret, credential, migration, marketplace, install/uninstall, privacy-sensitive, or destructive changes
- customer/user-facing sends, production data changes, deployment, publishing, payments, or policy changes
- overwriting unmanaged files or applying generated artifacts outside the reviewed target files

### Definition of Done

Required evidence:
- changed files or proposed files are named
- the reason for each meaningful change is summarized
- focused validation was run, or an unavailable/not-relevant check is explicitly skipped with a reason
- cycle budget used or remaining is stated for multi-cycle work
- remaining risks, approval needs, and next review trigger are stated

Validation hints:
- after AGENTS.md or Docs/AI/* changes: python "C:\Users\ytkim\plugins\repo-harness-tuner\skills\codex-harness-setup\scripts\check_harness.py" "C:\Users\ytkim\plugins\repo-harness-tuner"
- after diagnosis or design changes: python "C:\Users\ytkim\plugins\repo-harness-tuner\scripts\console.py" diagnose --repo "C:\Users\ytkim\plugins\repo-harness-tuner" --phase active-development
- when no native validation command is detected: record manual or unavailable validation explicitly

Closeout should include:
- summarize what changed and why
- report validation evidence and skipped checks
- call out unresolved risks or follow-up recommendations
- record harness history when the result should influence future tuning

### Human Approval Points

- Default human involvement: 3/5 (Infer from repo context, but ask before hard-to-reverse or user-visible direction changes.)
- Default work budget: up to 3 cycles; use up to 5 only for shared contracts, CLI behavior, plugin metadata, validation-flow, or factory/engine changes.
- Worker pattern: single-agent with single thread visibility
- Always ask before:
  - destructive filesystem or data operations
  - release, deployment, dependency, CI, secret, credential, migration, marketplace, install/uninstall, or privacy-sensitive changes
  - product, roadmap, UX, narrative, customer-facing, or scope decisions not answered by a repo source of truth
  - file edits at human involvement 5 unless the exact edit was already approved
  - applying release, CI, install, marketplace, dependency, destructive, or hard-to-reverse changes after the first read/preview cycle

Area matrix:
- Small docs/copy edits: human involvement 2/5, single-agent, validation: docs review or skipped with reason
- Core behavior or shared contracts: human involvement 3/5, single-agent or background review, validation: focused regression plus broad check when shared
- Product, roadmap, UX, or narrative direction: human involvement 4/5, visible chat, validation: decision record or concise report
- Dependencies, release, data, secrets, or destructive operations: human involvement 5/5, visible chat + approval, validation: explicit approval and rollback evidence
- Static review, test review, security review: human involvement 3/5, background/read-only, validation: findings summary with file references
<!-- repo-harness-tuner:end:harness-contract -->
