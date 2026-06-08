# cli-smoke-validation
<!-- repo-harness-tuner:generated:factory -->

Status: planned
Domain: Codex plugin harness tuner
Team: Codex Plugin Team

This is a repo-local planning artifact, not an installed Codex skill. Treat it as guidance for future Harness Tuner work unless a separate approved install flow creates a real `SKILL.md`.

## Purpose
Define focused CLI smoke tests for factory, install, tune, and eval flows.

## Trigger
Use when work needs define focused CLI smoke tests for factory, install, tune, and eval flows with repo evidence such as .codex-plugin/plugin.json, skills/, python-scripts, AGENTS.md.

## Related Roles
harness-designer, plugin-builder, validation-reviewer

## Harness Contract
- Scope: stay inside this skill's trigger, domain, and current user request.
- Access & Actions: inspect repo evidence and produce bounded findings; do not expand tools, installs, CI, or release gates without approval.
- Definition of Done: provide concise findings, relevant file references, validation evidence or skipped-check reason, and remaining risk.
- Human Approval Points: escalate product direction, release, dependency, secret, privacy-sensitive, destructive, or external-send decisions.

## Repo Evidence
- `.codex-plugin/plugin.json`
- `skills/`
- `python-scripts`
- `AGENTS.md`
- `.codex-plugin\plugin.json`
- `.mcp.json`

## Validation
- `python scripts/console.py release-check`
- `python scripts/console.py fixture-test`
- `python <plugin-creator>/scripts/validate_plugin.py .`
- `python <skill-creator>/scripts/quick_validate.py skills/<skill-name>`

## Boundaries
- do not replace repo-specific validation with broad boilerplate
- do not expand this skill beyond the detected project/domain markers
- ask or escalate before release, dependency, secret, destructive, or user-visible direction changes

## Workflow
1. Inspect the repo source of truth before adding process.
2. Keep scope bounded to the current task and domain.
3. Produce concise evidence that the main thread can merge.
4. Escalate to visible user review for product direction, release, destructive operations, dependencies, secrets, or privacy-sensitive changes.

## Evidence
- concise findings or decision summary
- file references when relevant
- validation command, skipped-check reason, or manual evidence

## Tuning
Use `repo-harness-tuner diagnose`, `history`, and `eval --score` to decide whether this skill should be kept, revised, or retired.
