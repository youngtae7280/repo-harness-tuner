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
