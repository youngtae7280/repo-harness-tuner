# Team Orchestration
<!-- repo-harness-tuner:generated:factory -->

Domain: Codex plugin harness tuner
Pattern: Producer Reviewer (`producer-reviewer`)
Repo evidence: codex-plugin evidence: .codex-plugin/plugin.json, skills/, python-scripts, AGENTS.md, .codex-plugin\plugin.json. Validation hints: python scripts/console.py release-check, python scripts/console.py fixture-test, python <plugin-creator>/scripts/validate_plugin.py .

## Default Flow
1. Main thread analyzes the request, repo state, and human-involvement level.
2. Main thread chooses whether a single-agent path is enough.
3. If worker help is useful, assign bounded scopes using `patterns --prompt <pattern-id>` or the role purposes in `Docs/AI/agent-team.md`.
4. Background workers return concise findings only; visible chats are used for decisions the user should inspect.
5. Main thread merges findings, applies approved changes, runs validation, and records history when useful.

## Harness Contract

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
- Worker pattern: single-agent with single thread visibility
- Always ask before:
  - destructive filesystem or data operations
  - release, deployment, dependency, CI, secret, credential, migration, marketplace, install/uninstall, or privacy-sensitive changes
  - product, roadmap, UX, narrative, customer-facing, or scope decisions not answered by a repo source of truth
  - file edits at human involvement 5 unless the exact edit was already approved

Area matrix:
- Small docs/copy edits: human involvement 2/5, single-agent, validation: docs review or skipped with reason
- Core behavior or shared contracts: human involvement 3/5, single-agent or background review, validation: focused regression plus broad check when shared
- Product, roadmap, UX, or narrative direction: human involvement 4/5, visible chat, validation: decision record or concise report
- Dependencies, release, data, secrets, or destructive operations: human involvement 5/5, visible chat + approval, validation: explicit approval and rollback evidence
- Static review, test review, security review: human involvement 3/5, background/read-only, validation: findings summary with file references

## Visibility Policy
- main thread owns final decisions, writes, and closeout
- use visible chat for approval, product direction, scope, release, or user-inspectable QA evidence
- use background/read-only workers for independent review, validation, and source checks
- persist only concise artifacts that future Codex sessions should reuse

## Role Order
- 1. `harness-designer`: Map project-specific agent behavior, human involvement, and worker policy. Ground decisions in .codex-plugin/plugin.json, skills/, python-scripts.
- 2. `plugin-builder`: Update plugin manifests, CLI scripts, skills, and generated artifacts. Ground decisions in .codex-plugin/plugin.json, skills/, python-scripts.
- 3. `validation-reviewer`: Check plugin validation, skill validation, cachebuster, and smoke evidence. Ground decisions in .codex-plugin/plugin.json, skills/, python-scripts.

## Stop Conditions
- Human involvement 5 without explicit approval.
- Destructive filesystem or data operations.
- Dependency, release, CI, secret, credential, migration, or privacy-sensitive changes.
- Product, roadmap, UX, narrative, or scope choices not answered by a repo source of truth.

## Durable Artifacts
- Persist only decisions, evidence, or role/skill guidance that future Codex sessions should reuse.
- Prefer updating `Docs/AI/agent-team.md`, `Docs/AI/skills/*.md`, or `Docs/AI/harness-history.jsonl` over adding broad reports.
