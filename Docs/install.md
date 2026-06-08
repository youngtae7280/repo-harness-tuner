# Install, Refresh, And Troubleshooting

Use this guide to install or refresh Repo Harness Tuner from a fresh clone.

## Requirements

- Git
- Python 3.11 or newer
- Codex app or Codex CLI
- Optional: GitHub CLI for issue, milestone, and PR work

Validator scripts from local Codex system skills may require PyYAML:

```powershell
python -m pip install --user PyYAML
```

## Clone

For the smoothest personal-plugin flow, clone into the default local plugin directory:

```powershell
git clone https://github.com/youngtae7280/repo-harness-tuner.git $HOME\plugins\repo-harness-tuner
cd $HOME\plugins\repo-harness-tuner
```

You can edit the repo from another location, but the default personal marketplace entry expects `$HOME\plugins\repo-harness-tuner`.

## Personal Marketplace Entry

Create or update `$HOME\.agents\plugins\marketplace.json`:

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

The `source.path` is relative to the marketplace root under the user home directory.

## Install In Codex

Install or refresh the plugin:

```powershell
codex plugin add repo-harness-tuner@personal
```

If the Windows Store app shim blocks `codex.exe` with `Access is denied`, read the real CLI path from `%USERPROFILE%\.codex\config.toml`. Look for `CODEX_CLI_PATH`, then run:

```powershell
& "C:\path\from\CODEX_CLI_PATH\codex.exe" plugin add repo-harness-tuner@personal
```

Start a new Codex thread after installing or refreshing so the plugin skills are loaded.

## Work Without Installing

The CLI scripts can run directly from the cloned repository:

```powershell
python scripts\console.py next --repo . --phase active-development --domain "Codex plugin harness factory"
python scripts\console.py doctor --repo . --phase active-development --domain "Codex plugin harness factory"
python scripts\console.py run-loop --repo . --phase active-development --domain "Codex plugin harness factory"
python scripts\console.py recommend-skills --repo . --phase active-development --domain "Codex plugin harness factory"
python scripts\console.py fixture-test
```

This is enough for development, CI checks, and fixture-test work.

## Skill Recommendation Installs

`recommend-skills` is read-only by default. It may recommend built-in factory candidates or ECC seed catalog candidates, but it does not install ECC itself.

Confirmed installs use small Codex adapter skills only:

```powershell
python scripts\console.py recommend-skills --repo C:\path\to\repo --install --confirm-install
```

This never bulk-installs external hooks, MCP servers, slash commands, native agents, marketplace entries, or human-involvement policy changes.

## Refresh After Local Changes

When plugin metadata or skills changed and Codex must see the update:

```powershell
python %USERPROFILE%\.codex\skills\.system\plugin-creator\scripts\update_plugin_cachebuster.py .
codex plugin add repo-harness-tuner@personal
```

Use the real `CODEX_CLI_PATH` command if the default `codex` shim is blocked.

Open a new Codex thread after reinstalling.

## Local Validation

Run these before pushing:

```powershell
python -m py_compile scripts\console.py scripts\diagnose.py scripts\evaluate.py scripts\factory.py scripts\bootstrap.py scripts\history.py scripts\history_store.py scripts\loop.py scripts\skill_recommender.py scripts\fixture_test.py scripts\tune.py scripts\write_policy.py scripts\generate_prompt.py scripts\scan_plugins.py scripts\scan_repo_harness.py scripts\scan_skills.py scripts\worker_patterns.py
python scripts\console.py fixture-test
python %USERPROFILE%\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\repo-harness-tuner
python %USERPROFILE%\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\codex-harness-setup
python %USERPROFILE%\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
python skills\codex-harness-setup\scripts\check_harness.py .
```

In Windows PowerShell, prefer explicit file lists. `scripts/*.py` is not expanded before Python receives it.

## Troubleshooting

### `codex.exe` Access Is Denied

Use the `CODEX_CLI_PATH` value in `%USERPROFILE%\.codex\config.toml` instead of the Windows Store shim.

### `ModuleNotFoundError: No module named 'yaml'`

Install PyYAML for the validator scripts:

```powershell
python -m pip install --user PyYAML
```

### Plugin Installed But Skill Does Not Appear

Start a new Codex thread. Plugin skills are loaded at thread start.

### Marketplace Entry Points At The Wrong Path

Confirm `$HOME\.agents\plugins\marketplace.json` points to:

```text
./plugins/repo-harness-tuner
```

Then confirm the repo exists at:

```text
$HOME\plugins\repo-harness-tuner
```

### Text Output Crashes In Windows Console

This should be treated as a CLI compatibility bug. As a temporary local workaround:

```powershell
$env:PYTHONIOENCODING = "utf-8"
python scripts\console.py overview --repo .
```

Report or fix the command so default PowerShell users do not need the workaround.

## First Commands After Install

Use read-only commands first:

```powershell
python scripts\console.py next --repo C:\path\to\repo --phase active-development --domain "your project"
python scripts\console.py doctor --repo C:\path\to\repo --phase active-development --domain "your project"
python scripts\console.py run-loop --repo C:\path\to\repo --phase active-development --domain "your project"
```

Use write flags only after reviewing the dry-run or plan:

```powershell
python scripts\console.py bootstrap --repo C:\path\to\repo --phase new-project --write
python scripts\console.py tune --repo C:\path\to\repo --phase active-development --write
```
