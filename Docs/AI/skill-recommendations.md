# Skill Recommendations
<!-- repo-harness-tuner:generated:skill-recommendation -->

Updated: 2026-06-08 06:36:52 UTC
Domain: Codex plugin harness tuner
Phase: active-development
Project type: codex-plugin
Curator action: watch
Curator reason: Stored history/eval exists (1 history, 0 eval), but no pressure signal justifies a broad skill install.

## Safety
- Read-only by default.
- Installs require `--install --confirm-install`.
- External catalogs are adapter-only; no bulk ECC install, hooks, MCP servers, commands, or agents are installed.
- Human-involvement policy changes are never silently applied.

## Recommendations
- `factory-plugin-contract-review` (factory): Harness curation
  - Component: `plugin-contract-review` via repo-local planning artifact
  - Reason: revise, keep, or retire skill guidance based on history and eval evidence; project type is codex-plugin; keyword(s): harness, agent, skill
  - Install strategy: `codex-adapter-skill`
- `ecc-code-reviewer` (ecc): Code review
  - Component: `code-reviewer` via agent/command
  - Reason: review code quality, regressions, and maintainability before Codex merges changes; project type is codex-plugin
  - Install strategy: `codex-adapter-skill`
- `factory-cli-smoke-validation` (factory): Build failure repair
  - Component: `cli-smoke-validation` via repo-local planning artifact
  - Reason: repair build or validation failures with the nearest native command; project type is codex-plugin
  - Install strategy: `codex-adapter-skill`

## Command Flow
- Run preview first, write this plan only after review, and install adapter skills only after explicit approval.
- Preview candidates: `python scripts/console.py recommend-skills --repo C:\Users\ytkim\plugins\repo-harness-tuner --phase active-development --domain "Codex plugin harness tuner" --source builtin,ecc --limit 3`
- Write this plan: `python scripts/console.py recommend-skills --repo C:\Users\ytkim\plugins\repo-harness-tuner --phase active-development --domain "Codex plugin harness tuner" --source builtin,ecc --limit 3 --write-plan`
- Confirmed install after approval: `python scripts/console.py recommend-skills --repo C:\Users\ytkim\plugins\repo-harness-tuner --phase active-development --domain "Codex plugin harness tuner" --source builtin,ecc --limit 3 --install --confirm-install`
