# Contributor Handoff

Use this guide when continuing Repo Harness Tuner work from a different PC using only GitHub as the source of truth.

## Repository

- GitHub: https://github.com/youngtae7280/repo-harness-tuner
- Default branch: `main`
- Current roadmap: [ROADMAP.md](ROADMAP.md)
- Current milestone: v1.0.0 stable public release, after the v0.8.0 closed-loop release.
- Next implementation target: `v1.0.0 - Stable Public Release`

## Clone On A New PC

For the smoothest Codex personal-plugin install flow, clone into the user plugin directory:

```powershell
git clone https://github.com/youngtae7280/repo-harness-tuner.git $HOME\plugins\repo-harness-tuner
cd $HOME\plugins\repo-harness-tuner
```

On Unix-like systems:

```bash
git clone https://github.com/youngtae7280/repo-harness-tuner.git ~/plugins/repo-harness-tuner
cd ~/plugins/repo-harness-tuner
```

The plugin can still be edited from another location, but the default personal marketplace entry expects `~/plugins/repo-harness-tuner`.

## Install In Codex On A New PC

Create or update the personal marketplace file at `~/.agents/plugins/marketplace.json`.

```json
{
  "name": "personal",
  "interface": {
    "displayName": "Personal"
  },
  "plugins": [
    {
      "name": "repo-harness-tuner",
      "source": {
        "source": "local",
        "path": "./plugins/repo-harness-tuner"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

Then install or refresh the plugin:

```powershell
codex plugin add repo-harness-tuner@personal
```

If the Windows Store app shim blocks `codex.exe`, use the Codex CLI path shown in the Codex config under `%USERPROFILE%\.codex\config.toml`, or install from the Codex app plugin UI using the personal marketplace.

Start a new Codex thread after installing so the plugin skills are loaded into the session.

## Work Without Installing The Plugin

The CLI scripts can run directly from the cloned repository:

```powershell
python scripts\console.py doctor --repo . --phase active-development --domain "Codex plugin harness factory"
python scripts\console.py run-loop --repo . --phase active-development --domain "Codex plugin harness factory"
python scripts\console.py fixture-test
```

This is enough for development, CI checks, and fixture-test work.

## Validation

Run these before pushing changes:

```powershell
python -m py_compile scripts\console.py scripts\diagnose.py scripts\evaluate.py scripts\factory.py scripts\bootstrap.py scripts\history.py scripts\history_store.py scripts\loop.py scripts\fixture_test.py scripts\tune.py scripts\write_policy.py scripts\generate_prompt.py scripts\scan_plugins.py scripts\scan_repo_harness.py scripts\scan_skills.py scripts\worker_patterns.py
python scripts\console.py fixture-test
python %USERPROFILE%\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\repo-harness-tuner
python %USERPROFILE%\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
python skills\codex-harness-setup\scripts\check_harness.py .
```

On Unix-like systems, replace `%USERPROFILE%\.codex` with `$HOME/.codex`.

GitHub Actions also runs the broad smoke suite on push and pull request:

```text
.github/workflows/validate.yml
```

## Fixture Tests And Next Work

The v0.3.0 fixture golden-test suite is implemented. Use this command before pushing changes:

```powershell
python scripts\console.py fixture-test
```

The closed v0.3.0 milestone remains useful as historical context:

- Issue #2: add fixture repository corpus.
- Issue #3: implement fixture golden-test runner.
- Issue #4: add fixture tests to CI.
- Issue #5: document fixture authoring and release criteria.
- Issue #6: release checklist.

The v0.5.0 factory output quality milestone is implemented. It added repo evidence extraction, repo-specific skill drafts, stale/conflict artifact detection, safer unmanaged replacement, factory quality fixture assertions, and updated docs.

The v0.8.0 stronger closed-loop milestone is implemented. It added durable eval score records, eval/history feedback into diagnose/tune/factory/run-loop, closed-loop fixture scenarios, and a bounded low-risk auto-apply guard for recommended writes.

Start with the GitHub `v1.0.0 - Stable Public Release` milestone. The expected work is:

1. Stabilize CLI names, JSON schemas, exit codes, and write-safety behavior.
2. Finish first-time install, upgrade, reinstall, and troubleshooting docs.
3. Define versioning and breaking-change policy.
4. Keep CI coverage for py_compile, fixture tests, plugin validation, skill validation, harness checks, eval-score persistence, and broad CLI smoke tests.
5. Confirm a fresh clone on a different PC can run `doctor`, `run-loop`, `fixture-test`, and plugin install from docs only.

Agreed development order after the 2026-06-08 audit review:

1. Do `#18` first. Freeze the user-facing CLI contract before doing a large README/onboarding rewrite. Cover command aliases, stable JSON fields, exit codes, write flags, `--confirm-write` behavior, optional vs required next actions, and Windows console-safe output.
2. Then do `#19`. Use the audit report's README recommendations, but keep README slim: one request or one command first, what happens next, safety model, adaptive loop, human-involvement summary, and links to detailed docs.
3. Use `Docs/versioning.md` for `#20`, then do `#21` and `#22`: CI/release validation matrix and fresh-clone continuation verification.
4. Keep PowerShell-safe commands in docs. Prefer explicit script file lists over `scripts/*.py` in Windows instructions.
5. Track the Windows CP949 `UnicodeEncodeError` seen in `overview` as a `#18` compatibility issue, because it is part of the public CLI contract rather than only an onboarding problem.
6. Treat "one-command assistant" as a v1.0 documentation/user-experience commitment around `doctor` and `run-loop`; do not add a new automation surface before the CLI contract and fresh-clone flow are stable.
7. v1.1 structured adaptive recommendations are implemented in `doctor`/`run-loop`. They recommend cadence and human-involvement changes from closed-loop evidence, but do not run a scheduler or silently change policy.

The `#18`, `#19`, and `#20` documentation entry points are:

- `Docs/cli-contracts.md` for stable command names, JSON envelopes, exit codes, write-safety behavior, and console compatibility.
- `Docs/install.md` for first-time install, refresh, validation, and troubleshooting.
- `Docs/commands.md` for the full command reference moved out of the README.
- `Docs/versioning.md` for version format, breaking-change classification, deprecation policy, changelog rules, and release checklist.
- `README.md` / `README_KO.md` for slim one-request onboarding and the product-level safety/adaptive-loop explanation.

Post-v1.0 product direction:

- Keep the first user action to one request in Codex or one `run-loop` command in CLI.
- Keep structured adaptive cadence recommendations in `adaptive.cadence` before considering any scheduler-like automation.
- Keep human-involvement adjustment suggestions in `adaptive.human_involvement`; require explicit approval before changing repo-local policy.

## Local-Only State

These are machine-specific and should not be treated as source of truth:

- `~/.agents/plugins/marketplace.json`
- `~/.codex/config.toml`
- `~/.codex/plugins/cache/...`
- Codex app session state and installed-plugin cache

The durable source of truth is the GitHub repository plus GitHub issues/milestones.

## Release Handoff

For a release change:

1. Classify the change with `Docs/versioning.md`.
2. Update `CHANGELOG.md`.
3. Update `.codex-plugin/plugin.json` base version.
4. Run the plugin-creator cachebuster helper.
5. Run local validation.
6. Commit and push.
7. Confirm GitHub Actions passes on `main`.
8. Create and push the version tag.
9. Confirm GitHub Actions passes on the tag.
10. Refresh the local Codex install with `codex plugin add repo-harness-tuner@personal`.
