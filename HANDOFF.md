# Contributor Handoff

Use this guide when continuing Repo Harness Tuner work from a different PC using only GitHub as the source of truth.

## Repository

- GitHub: https://github.com/youngtae7280/repo-harness-tuner
- Default branch: `main`
- Current roadmap: [ROADMAP.md](ROADMAP.md)
- Current milestone: https://github.com/youngtae7280/repo-harness-tuner/milestone/1
- Next implementation target: `v0.3.0 - Fixture Golden Tests`

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
```

This is enough for development, CI checks, and fixture-test work.

## Validation

Run these before pushing changes:

```powershell
python -m py_compile scripts\console.py scripts\diagnose.py scripts\evaluate.py scripts\factory.py scripts\bootstrap.py scripts\history.py scripts\history_store.py scripts\loop.py scripts\tune.py scripts\write_policy.py scripts\generate_prompt.py scripts\scan_plugins.py scripts\scan_repo_harness.py scripts\scan_skills.py scripts\worker_patterns.py
python %USERPROFILE%\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\repo-harness-tuner
python %USERPROFILE%\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
python skills\codex-harness-setup\scripts\check_harness.py .
```

On Unix-like systems, replace `%USERPROFILE%\.codex` with `$HOME/.codex`.

GitHub Actions also runs the broad smoke suite on push and pull request:

```text
.github/workflows/validate.yml
```

## Continue v0.3.0 Work

Use the GitHub milestone as the active task board:

- Issue #2: add fixture repository corpus.
- Issue #3: implement fixture golden-test runner.
- Issue #4: add fixture tests to CI.
- Issue #5: document fixture authoring and release criteria.
- Issue #6: release checklist.

Recommended order:

1. Build the fixture corpus.
2. Implement the runner.
3. Add CI coverage.
4. Document fixture authoring.
5. Release v0.3.0 after local and GitHub validation pass.

## Local-Only State

These are machine-specific and should not be treated as source of truth:

- `~/.agents/plugins/marketplace.json`
- `~/.codex/config.toml`
- `~/.codex/plugins/cache/...`
- Codex app session state and installed-plugin cache

The durable source of truth is the GitHub repository plus GitHub issues/milestones.

## Release Handoff

For a release change:

1. Update `CHANGELOG.md`.
2. Update `.codex-plugin/plugin.json` base version.
3. Run the plugin-creator cachebuster helper.
4. Run local validation.
5. Commit and push.
6. Confirm GitHub Actions passes on `main`.
7. Create and push the version tag.
8. Confirm GitHub Actions passes on the tag.
9. Refresh the local Codex install with `codex plugin add repo-harness-tuner@personal`.
