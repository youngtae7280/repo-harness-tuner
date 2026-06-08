# Validation Guide

Use the cheapest check that gives meaningful evidence for the change.

## Detected Commands
- Focused Python script check: `python -m py_compile scripts\console.py scripts\factory.py scripts\diagnose.py scripts\loop.py scripts\skill_recommender.py scripts\fixture_test.py`.
- Fixture golden test check: `python scripts\console.py fixture-test`.
- Broad script check: `python -m py_compile scripts\console.py scripts\diagnose.py scripts\evaluate.py scripts\factory.py scripts\bootstrap.py scripts\history.py scripts\history_store.py scripts\loop.py scripts\skill_recommender.py scripts\fixture_test.py scripts\tune.py scripts\write_policy.py scripts\generate_prompt.py scripts\scan_plugins.py scripts\scan_repo_harness.py scripts\scan_skills.py scripts\worker_patterns.py`.
- Skill validation on Windows: `python %USERPROFILE%\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\repo-harness-tuner`.
- Plugin validation on Windows: `python %USERPROFILE%\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .`.
- Use the equivalent `$HOME/.codex/skills/.system/...` paths on Unix-like machines.
- GitHub Actions broad check: `.github/workflows/validate.yml`.

## Windows Notes
- In Windows PowerShell, prefer explicit file lists for `py_compile`; `scripts/*.py` is not expanded by PowerShell before Python receives it.
- Public CLI text output should not crash under the default Windows console encoding. When touching CLI printing, run at least one representative command in a normal PowerShell session, such as `python scripts\console.py overview --repo .`.
- `PYTHONIOENCODING=utf-8` is an acceptable local workaround, but v1.0 CLI behavior should be safe without requiring users to know that workaround.

## Selection Policy
- Docs-only or prompt-only changes: review the changed text; skip code validation with a reason.
- Narrow behavior changes: run the closest focused check.
- Shared contracts, build config, release-facing changes, or broad refactors: run focused checks plus the broad build/QA command when available.
- If a required tool is unavailable, record what was skipped and why.
