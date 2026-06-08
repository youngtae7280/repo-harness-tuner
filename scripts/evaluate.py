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
write_policy = load_local_module("write_policy")
history_store = load_local_module("history_store")


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
    elif project_type == "codex-plugin":
        common.append(
            {
                "id": "plugin-contract-validation",
                "prompt": "Tune the harness for a Codex plugin change that edits plugin.json, SKILL.md, or CLI factory behavior.",
                "purpose": "Checks whether plugin metadata, skill validation, cachebuster, and CLI smoke evidence are represented.",
                "assertions": [
                    "Requires plugin manifest validation when plugin.json changes.",
                    "Requires skill quick validation when bundled SKILL.md files change.",
                    "Includes focused CLI smoke tests for factory or install behavior changes.",
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


def normalize_status(value: Any) -> str:
    normalized = str(value or "n/a").strip().lower()
    if normalized in {"pass", "passed", "ok", "true", "yes", "y", "1"}:
        return "pass"
    if normalized in {"fail", "failed", "no", "false", "x", "0"}:
        return "fail"
    return "n/a"


def normalize_results_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return [item for item in payload["results"] if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("tasks"), list):
        return [item for item in payload["tasks"] if isinstance(item, dict)]
    if isinstance(payload, dict) and "task_id" in payload:
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def score_eval_results(result_path: Path) -> dict[str, Any]:
    raw = json.loads(result_path.read_text(encoding="utf-8-sig"))
    results = normalize_results_payload(raw)
    scored_tasks: list[dict[str, Any]] = []
    totals = {
        "tasks": len(results),
        "assertions": 0,
        "baseline_pass": 0,
        "with_harness_pass": 0,
        "improved": 0,
        "regressed": 0,
        "unchanged_pass": 0,
        "unchanged_fail": 0,
        "not_applicable": 0,
    }

    for index, result in enumerate(results, start=1):
        assertions = result.get("assertions", [])
        if not isinstance(assertions, list):
            assertions = []
        task_stats = {
            "assertions": 0,
            "baseline_pass": 0,
            "with_harness_pass": 0,
            "improved": 0,
            "regressed": 0,
            "unchanged_pass": 0,
            "unchanged_fail": 0,
            "not_applicable": 0,
        }
        scored_assertions = []
        for assertion in assertions:
            if isinstance(assertion, str):
                assertion = {"text": assertion}
            if not isinstance(assertion, dict):
                continue
            baseline = normalize_status(assertion.get("baseline"))
            with_harness = normalize_status(assertion.get("with_harness", assertion.get("harness")))
            task_stats["assertions"] += 1
            totals["assertions"] += 1
            if baseline == "pass":
                task_stats["baseline_pass"] += 1
                totals["baseline_pass"] += 1
            if with_harness == "pass":
                task_stats["with_harness_pass"] += 1
                totals["with_harness_pass"] += 1
            if baseline == "n/a" or with_harness == "n/a":
                task_stats["not_applicable"] += 1
                totals["not_applicable"] += 1
                outcome = "n/a"
            elif baseline != "pass" and with_harness == "pass":
                task_stats["improved"] += 1
                totals["improved"] += 1
                outcome = "improved"
            elif baseline == "pass" and with_harness != "pass":
                task_stats["regressed"] += 1
                totals["regressed"] += 1
                outcome = "regressed"
            elif baseline == "pass" and with_harness == "pass":
                task_stats["unchanged_pass"] += 1
                totals["unchanged_pass"] += 1
                outcome = "unchanged-pass"
            else:
                task_stats["unchanged_fail"] += 1
                totals["unchanged_fail"] += 1
                outcome = "unchanged-fail"
            scored_assertions.append(
                {
                    "text": assertion.get("text", assertion.get("assertion", "")),
                    "baseline": baseline,
                    "with_harness": with_harness,
                    "outcome": outcome,
                    "evidence": assertion.get("evidence", ""),
                }
            )

        if task_stats["regressed"]:
            recommendation = "revise"
        elif task_stats["improved"] and not task_stats["unchanged_fail"]:
            recommendation = "keep"
        elif task_stats["unchanged_fail"]:
            recommendation = "revise"
        else:
            recommendation = str(result.get("decision") or "keep")
        scored_tasks.append(
            {
                "task_id": result.get("task_id", result.get("id", f"task-{index}")),
                "baseline_summary": result.get("baseline_summary", ""),
                "with_harness_summary": result.get("with_harness_summary", ""),
                "stats": task_stats,
                "assertions": scored_assertions,
                "recommended_decision": recommendation,
                "recorded_decision": result.get("decision", ""),
            }
        )

    if totals["regressed"]:
        recommendation = "revise the harness before promoting this change"
    elif totals["improved"] and not totals["unchanged_fail"]:
        recommendation = "keep or promote this harness change"
    elif totals["unchanged_fail"]:
        recommendation = "revise the harness; it did not fix known failures"
    else:
        recommendation = "keep the harness stable and gather more evidence"

    return {
        "schema": "repo-harness-tuner.eval-score.v1",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "evaluation_mode": "score",
        "result_file": str(result_path.resolve()),
        "totals": totals,
        "net_improvement": totals["improved"] - totals["regressed"],
        "recommendation": recommendation,
        "tasks": scored_tasks,
    }


def append_eval_score(root: Path, payload: dict[str, Any], note: str = "") -> Path:
    path = history_store.eval_results_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(payload)
    record["repo"] = str(root.resolve())
    if note:
        record["note"] = note
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def print_eval_score(payload: dict[str, Any]) -> None:
    totals = payload["totals"]
    print("Eval mode: score")
    print(f"Result file: {payload['result_file']}")
    print(f"Tasks: {totals['tasks']}")
    print(f"Assertions: {totals['assertions']}")
    print(f"Baseline pass: {totals['baseline_pass']}")
    print(f"With harness pass: {totals['with_harness_pass']}")
    print(f"Improved: {totals['improved']}")
    print(f"Regressed: {totals['regressed']}")
    print(f"Net improvement: {payload['net_improvement']}")
    print(f"Recommendation: {payload['recommendation']}")
    print("")
    print("Tasks:")
    for task in payload["tasks"]:
        stats = task["stats"]
        print(
            f"- {task['task_id']}: {task['recommended_decision']} "
            f"(improved {stats['improved']}, regressed {stats['regressed']}, unchanged fail {stats['unchanged_fail']})"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    parser.add_argument("--module", action="append")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--repo-type", default="unknown")
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    parser.add_argument("--score", help="Score a JSON result file created from the eval result_schema.")
    parser.add_argument("--write-score", action="store_true", help="Append eval score results to Docs/AI/harness-eval-results.jsonl.")
    parser.add_argument("--note", default="", help="Optional note stored with --write-score.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo)
    if args.score:
        payload = score_eval_results(Path(args.score))
        if args.write_score:
            guard = write_policy.write_guard("eval", args.phase, args.human_involvement, args.confirm_write)
            if guard:
                payload["write_blocked"] = guard
                if args.json:
                    print(json.dumps(payload, indent=2, ensure_ascii=True))
                else:
                    print_eval_score(payload)
                    print("")
                    print(write_policy.format_guard(guard))
                return 2
            payload["score_path"] = str(append_eval_score(root.resolve(), payload, args.note))
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=True))
        else:
            print_eval_score(payload)
            if args.write_score:
                print("")
                print(f"Eval score written: {payload['score_path']}")
        return 0

    payload = build_eval_plan(root, args.phase, args.module, args.human_involvement, args.repo_type)
    if args.write_plan:
        guard = write_policy.write_guard("eval", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            payload["write_blocked"] = guard
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=True))
            else:
                print_eval_plan(payload)
                print("")
                print(write_policy.format_guard(guard))
            return 2
        payload["plan_path"] = str(write_eval_plan(root.resolve(), payload))
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print_eval_plan(payload)
        if args.write_plan:
            print("")
            print(f"Eval plan written: {payload['plan_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
