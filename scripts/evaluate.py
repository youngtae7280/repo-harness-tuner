#!/usr/bin/env python3
"""Create a harness evaluation plan for with-harness vs baseline testing."""
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


def load_local_module(name: str):
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scan_repo_harness = load_local_module("scan_repo_harness")
diagnose_module = load_local_module("diagnose")


def golden_tasks(project_type: str, phase: str) -> list[dict[str, Any]]:
    common = [
        {
            "id": "harness-diagnosis",
            "prompt": "Diagnose this repo's Codex harness and recommend the next smallest useful improvement without editing files.",
            "purpose": "Checks whether the harness guides audit-only work without over-editing.",
            "assertions": [
                "Identifies existing agent instruction files and validation docs.",
                "Separates missing, stale, and excessive harness rules.",
                "Recommends no file edits when the harness is already fit.",
            ],
        },
        {
            "id": "validation-drift",
            "prompt": "Inspect package or project validation commands and update the harness guidance only if it is stale.",
            "purpose": "Checks whether validation guidance stays tied to native project commands.",
            "assertions": [
                "Names focused and broad validation separately.",
                "Avoids requiring full validation for every small task.",
                "Records skipped or unavailable validation with a reason.",
            ],
        },
    ]
    if project_type in {"vite-node", "node"}:
        common.append(
            {
                "id": "frontend-risk-scope",
                "prompt": "Tune the harness for a small user-facing UI change that may need browser evidence.",
                "purpose": "Checks whether UI evidence is requested only when the change justifies it.",
                "assertions": [
                    "Mentions browser or visual evidence for meaningful UI changes.",
                    "Keeps docs/copy edits lightweight.",
                    "Chooses a focused npm script when possible.",
                ],
            }
        )
    elif project_type in {"unity", "godot"}:
        common.append(
            {
                "id": "game-asset-risk",
                "prompt": "Tune the harness for a gameplay or UI change that may touch serialized assets.",
                "purpose": "Checks whether game-specific asset/editor risks are represented.",
                "assertions": [
                    "Calls out asset or scene/prefab/resource review risk.",
                    "Records editor validation availability or gaps.",
                    "Avoids adding release gates without approval.",
                ],
            }
        )
    elif project_type == "python":
        common.append(
            {
                "id": "python-env-validation",
                "prompt": "Tune the harness for a Python change where environment and test command assumptions matter.",
                "purpose": "Checks whether environment assumptions are explicit.",
                "assertions": [
                    "Separates environment setup from validation commands.",
                    "Chooses focused tests before broad suites.",
                    "Avoids inventing unavailable tooling.",
                ],
            }
        )
    if phase in {"pre-release", "high-risk"}:
        common.append(
            {
                "id": "approval-gate",
                "prompt": "Tune the harness before a high-risk release, migration, dependency, or destructive operation.",
                "purpose": "Checks whether explicit approval and rollback evidence are required.",
                "assertions": [
                    "Requires explicit approval before high-risk edits.",
                    "Names rollback or dry-run evidence.",
                    "Uses visible decision points for user-facing tradeoffs.",
                ],
            }
        )
    return common


def build_eval_plan(
    root: Path,
    phase: str,
    modules: list[str] | None = None,
    human_involvement: int | None = None,
    repo_type: str | None = None,
) -> dict[str, Any]:
    repo_scan = scan_repo_harness.scan(root)
    diagnosis = diagnose_module.diagnose(root, repo_scan, phase, modules, human_involvement, repo_type)
    design = diagnosis["harness_design"]
    project_type = str(design["project_type"])
    tasks = golden_tasks(project_type, phase)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return {
        "schema": "repo-harness-tuner.eval.v1",
        "created_at": timestamp,
        "repo": str(root.resolve()),
        "phase": phase,
        "project_type": project_type,
        "harness_readiness": diagnosis["readiness"]["score"],
        "human_involvement": diagnosis["human_involvement"],
        "worker_pattern": design["worker_architecture"],
        "evaluation_mode": "plan-only",
        "golden_tasks": tasks,
        "runbook": [
            "Run each golden task once as a baseline without explicitly invoking repo-harness-tuner.",
            "Run the same task with repo-harness-tuner and the embedded codex-harness-setup workflow.",
            "Record outputs under a dated evaluation folder or paste concise summaries into the result table.",
            "Score each assertion as pass, fail, or n/a with evidence.",
            "Only promote harness changes that improve correctness, reviewability, or overhead without overfitting to one prompt.",
        ],
        "result_schema": {
            "task_id": "golden task id",
            "baseline_summary": "what happened without the tuner",
            "with_harness_summary": "what happened with the tuner",
            "assertions": [{"text": "assertion", "baseline": "pass|fail|n/a", "with_harness": "pass|fail|n/a", "evidence": "short evidence"}],
            "decision": "keep|revise|reject",
        },
    }


def write_eval_plan(root: Path, payload: dict[str, Any]) -> Path:
    docs_ai = root / "Docs" / "AI"
    docs_ai.mkdir(parents=True, exist_ok=True)
    path = docs_ai / "harness-eval-plan.md"
    lines = [
        "# Harness Evaluation Plan",
        "",
        f"Updated: {payload['created_at']}",
        f"Phase: {payload['phase']}",
        f"Project type: {payload['project_type']}",
        f"Harness readiness: {payload['harness_readiness']}/100",
        f"Human involvement: {payload['human_involvement']}/5",
        f"Worker pattern: {payload['worker_pattern'].get('label', payload['worker_pattern']['pattern'])} ({payload['worker_pattern']['pattern']})",
        "",
        "## Runbook",
    ]
    for item in payload["runbook"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Golden Tasks")
    for task in payload["golden_tasks"]:
        lines.append(f"### {task['id']}")
        lines.append(f"Prompt: {task['prompt']}")
        lines.append(f"Purpose: {task['purpose']}")
        lines.append("")
        lines.append("Assertions:")
        for assertion in task["assertions"]:
            lines.append(f"- {assertion}")
        lines.append("")
    lines.append("## Result Template")
    lines.append("```json")
    lines.append(json.dumps(payload["result_schema"], indent=2, ensure_ascii=False))
    lines.append("```")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def print_eval_plan(payload: dict[str, Any]) -> None:
    print(f"Eval mode: {payload['evaluation_mode']}")
    print(f"Repo: {payload['repo']}")
    print(f"Phase: {payload['phase']}")
    print(f"Project type: {payload['project_type']}")
    print(f"Harness readiness: {payload['harness_readiness']}/100")
    worker = payload["worker_pattern"]
    print(f"Worker pattern: {worker.get('label', worker['pattern'])} ({worker['pattern']})")
    print("")
    print("Golden tasks:")
    for task in payload["golden_tasks"]:
        print(f"- {task['id']}: {task['purpose']}")
    print("")
    print("Runbook:")
    for item in payload["runbook"]:
        print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    parser.add_argument("--module", action="append")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--repo-type", default="unknown")
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo)
    payload = build_eval_plan(root, args.phase, args.module, args.human_involvement, args.repo_type)
    if args.write_plan:
        payload["plan_path"] = str(write_eval_plan(root.resolve(), payload))
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_eval_plan(payload)
        if args.write_plan:
            print("")
            print(f"Eval plan written: {payload['plan_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
