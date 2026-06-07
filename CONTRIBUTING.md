# Contributing

Thanks for improving Repo Harness Tuner. This plugin combines a team/skill generation factory with an adaptive repo harness engine. Prefer focused changes that make Codex harnesses easier to generate, design, evaluate, and maintain.

## Development Setup

Use Python 3.9+ from the plugin root.

```powershell
python scripts\console.py patterns
python scripts\console.py diagnose --repo C:\path\to\repo --phase active-development
python scripts\console.py factory --repo C:\path\to\repo --domain "project domain" --phase active-development
python scripts\console.py factory --repo C:\path\to\repo --domain "project domain" --write-artifacts
python scripts\console.py factory --repo C:\path\to\repo --domain "project domain" --write-codex-skills
python scripts\console.py factory --repo C:\path\to\repo --domain "project domain" --install-codex-skills --confirm-install --skill-install-root C:\path\to\skills
python scripts\console.py eval --repo C:\path\to\repo --phase active-development
```

## Validation

Before opening a PR or sharing a change, run:

```powershell
$env:PYTHONPYCACHEPREFIX = Join-Path $env:TEMP 'repo-harness-tuner-pycache'
python -m py_compile scripts\console.py scripts\diagnose.py scripts\evaluate.py scripts\factory.py scripts\bootstrap.py scripts\history.py scripts\history_store.py scripts\tune.py scripts\write_policy.py scripts\generate_prompt.py scripts\scan_plugins.py scripts\scan_repo_harness.py scripts\scan_skills.py scripts\worker_patterns.py
python C:\Users\<you>\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\path\to\repo-harness-tuner\skills\repo-harness-tuner
python C:\Users\<you>\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py C:\path\to\repo-harness-tuner
```

When validating outside the original development machine, use the equivalent local paths for `skill-creator` and `plugin-creator`.

## Design Rules

- Keep file writes opt-in. Commands that can change target repositories should default to dry-run.
- Require `--confirm-write` for file-writing commands when human involvement is 4 or 5.
- Require `--confirm-install` before writing generated skill drafts outside the target repository.
- Do not overwrite existing harness files or installed generated skills unless the user passes an explicit overwrite flag.
- Prefer advisory repo-local docs before scripts, hooks, CI gates, or release blockers.
- Add new process only when it reduces real risk, improves reviewability, improves evidence, or records a project-specific decision.
- Keep user-facing concepts centered on human involvement, worker patterns, validation, and evaluation. Internal ambiguity terms should stay internal or compatibility-only.
- Keep the factory and engine connected: generated teams/skills should have evaluation hooks, history feedback, and tuning paths.

## Release Flow

1. Update `CHANGELOG.md`.
2. Run validation.
3. Update the plugin cachebuster with `plugin-creator`.
4. Commit and push.
5. Create a version tag when the change is ready to share.
