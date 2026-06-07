# Fixture Golden Tests

Repo Harness Tuner uses small fixture repositories to catch regressions in project detection, harness readiness, next-action selection, evaluation planning, and write safety.

Run the suite from the plugin root:

```powershell
python scripts\console.py fixture-test
```

JSON output is available for CI or debugging:

```powershell
python scripts\console.py fixture-test --json
```

## Fixture Corpus

Fixtures live under `tests/fixtures` and are listed in `tests/fixtures/manifest.json`.

Current fixtures:

- `empty-new-project`: no project or harness markers; should recommend bootstrap.
- `vite-node-existing`: Vite/Node markers and package scripts without a harness; should recommend bootstrap.
- `unity-minimal`: Unity `Assets/`, `ProjectSettings/`, and `Packages/manifest.json` markers; should recommend bootstrap.
- `codex-plugin-minimal`: `.codex-plugin/plugin.json`, `skills/`, and Python script markers; should recommend bootstrap with plugin-specific presets.
- `harnessed-vite`: Vite/Node project with repo-local harness and team artifacts; should be fit and recommend history recording.

## Assertions

Each fixture checks:

- detected project type,
- readiness range,
- loop status,
- next recommended action,
- evaluation golden task count,
- factory team label,
- high-risk write guard behavior,
- read-only commands do not modify fixture files.

## Adding A Fixture

Keep fixtures intentionally small. Include only marker files needed by scanners and diagnosis.

Do not add:

- dependency folders such as `node_modules`,
- Unity `Library`, `Logs`, `Temp`, or build output,
- secrets, credentials, private logs, or personal data,
- large generated artifacts.

After adding a fixture, update `tests/fixtures/manifest.json` with expected assertions and run:

```powershell
python scripts\console.py fixture-test --fixture <fixture-id>
python scripts\console.py fixture-test
```
