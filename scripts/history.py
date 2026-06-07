#!/usr/bin/env python3
"""Record and summarize repo harness tuning history."""
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
history_store = load_local_module("history_store")


history_path = history_store.history_path
load_history = history_store.load_history
summarize = history_store.summarize


def build_event(
    root: Path,
    phase: str,
    human_involvement: int | None = None,
    repo_type: str | None = None,
    modules: list[str] | None = None,
    note: str | None = None,
    event_type: str = "diagnosis-snapshot",
) -> dict[str, Any]:
    repo_scan = scan_repo_harness.scan(root)
    diagnosis = diagnose_module.diagnose(root, repo_scan, phase, modules, human_involvement, repo_type)
    worker = diagnosis["harness_design"]["worker_architecture"]
    return {
        "schema": "repo-harness-tuner.history.v1",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "type": event_type,
        "repo": str(root.resolve()),
        "phase": phase,
        "project_type": diagnosis["harness_design"]["project_type"],
        "readiness": diagnosis["readiness"]["score"],
        "human_involvement": diagnosis["human_involvement"],
        "worker_pattern": worker["pattern"],
        "worker_label": worker.get("label", worker["pattern"]),
        "recommendation_count": len(diagnosis["readiness"].get("recommendations", [])),
        "drift_count": len(diagnosis["drift"]),
        "process_overhead_count": len(diagnosis["process_overhead"]),
        "human_involvement_gap_count": len(diagnosis["human_involvement_enforcement"]),
        "next_review_trigger": diagnosis["harness_design"]["next_review_trigger"],
        "target_actions": [
            {"path": item["path"], "action": item["action"], "reason": item["reason"]}
            for item in diagnosis["harness_design"]["target_files"]
        ],
        "note": note or "",
    }


def append_event(root: Path, event: dict[str, Any]) -> Path:
    path = history_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def print_summary(root: Path, payload: dict[str, Any]) -> None:
    print(f"History: {history_path(root)}")
    print(f"Entries: {payload['count']}")
    if payload["parse_errors"]:
        print(f"Parse errors: {payload['parse_errors']}")
    if payload["readiness_latest"] is not None:
        print(f"Readiness latest: {payload['readiness_latest']}/100")
        print(f"Readiness range: {payload['readiness_min']}..{payload['readiness_max']}")
    if payload["by_worker_pattern"]:
        print("Worker patterns:")
        for key, value in payload["by_worker_pattern"].items():
            print(f"- {key}: {value}")
    latest = payload.get("latest")
    if latest:
        print("")
        print("Latest:")
        print(f"- {latest['created_at']} {latest['type']} {latest['readiness']}/100")
        print(f"- Pattern: {latest['worker_label']} ({latest['worker_pattern']})")
        if latest.get("note"):
            print(f"- Note: {latest['note']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    parser.add_argument("--module", action="append")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--repo-type", default="unknown")
    parser.add_argument("--record", action="store_true", help="Build a diagnosis snapshot event.")
    parser.add_argument("--write", action="store_true", help="Append the event to Docs/AI/harness-history.jsonl.")
    parser.add_argument("--event-type", default="diagnosis-snapshot")
    parser.add_argument("--note", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo)
    if args.record:
        event = build_event(root, args.phase, args.human_involvement, args.repo_type, args.module, args.note, args.event_type)
        payload: dict[str, Any] = {"event": event}
        if args.write:
            payload["path"] = str(append_event(root, event))
    else:
        payload = summarize(load_history(root))

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.record:
        print("History event:")
        print(f"- Type: {payload['event']['type']}")
        print(f"- Readiness: {payload['event']['readiness']}/100")
        print(f"- Worker pattern: {payload['event']['worker_label']} ({payload['event']['worker_pattern']})")
        if args.write:
            print(f"- Written: {payload['path']}")
    else:
        print_summary(root, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
