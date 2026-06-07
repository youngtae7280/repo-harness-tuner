#!/usr/bin/env python3
"""Run fixture-based golden tests for Repo Harness Tuner."""
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"


def load_local_module(name: str):
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


loop_module = load_local_module("loop")
scan_repo_harness = load_local_module("scan_repo_harness")
diagnose_module = load_local_module("diagnose")
factory_module = load_local_module("factory")
evaluate_module = load_local_module("evaluate")
write_policy = load_local_module("write_policy")


def load_manifest(fixtures_root: Path) -> dict[str, Any]:
    manifest_path = fixtures_root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing fixture manifest: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError("Fixture manifest must contain a non-empty fixtures array.")
    return payload


def tree_snapshot(root: Path) -> dict[str, tuple[int, int]]:
    snapshot: dict[str, tuple[int, int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            stat = path.stat()
            snapshot[str(path.relative_to(root))] = (stat.st_size, stat.st_mtime_ns)
    return snapshot


def assert_equal(failures: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


def assert_range(failures: list[str], label: str, actual: int, minimum: int, maximum: int) -> None:
    if actual < minimum or actual > maximum:
        failures.append(f"{label}: expected {minimum}-{maximum}, got {actual}")


def assert_minimum(failures: list[str], label: str, actual: int, minimum: int) -> None:
    if actual < minimum:
        failures.append(f"{label}: expected at least {minimum}, got {actual}")


def assert_contains_all(failures: list[str], label: str, actual: list[str], expected: list[str]) -> None:
    haystack = "\n".join(actual).lower()
    for item in expected:
        if str(item).lower() not in haystack:
            failures.append(f"{label}: expected to contain {item!r}")


def run_fixture(fixtures_root: Path, fixture: dict[str, Any]) -> dict[str, Any]:
    fixture_id = str(fixture["id"])
    root = (fixtures_root / str(fixture["path"])).resolve()
    phase = str(fixture.get("phase") or "active-development")
    domain = str(fixture.get("domain") or fixture_id)
    expected = fixture.get("expected", {})
    if not isinstance(expected, dict):
        raise ValueError(f"Fixture {fixture_id} expected field must be an object.")
    if not root.exists():
        return {
            "id": fixture_id,
            "path": str(root),
            "status": "fail",
            "failures": [f"Fixture path does not exist: {root}"],
        }

    before = tree_snapshot(root)
    repo_scan = scan_repo_harness.scan(root)
    diagnosis = diagnose_module.diagnose(root, repo_scan, phase, None, None, "unknown")
    factory_payload = factory_module.build_factory_plan(root, domain, phase, None, None, "unknown", 3)
    eval_payload = evaluate_module.build_eval_plan(root, phase, None, None, "unknown")
    loop_payload = loop_module.build_loop_plan(root, phase, domain)
    after = tree_snapshot(root)

    summary = loop_payload["summary"]
    next_action = summary["next_action"]
    failures: list[str] = []
    assert_equal(failures, "project_type", summary["project_type"], expected.get("project_type"))
    assert_equal(failures, "status", loop_payload["status"], expected.get("status"))
    assert_equal(failures, "next_action", next_action["id"], expected.get("next_action"))
    assert_equal(failures, "eval_tasks", summary["eval_tasks"], expected.get("eval_tasks"))
    assert_equal(failures, "factory_label", factory_payload["team_factory"]["label"], expected.get("factory_label"))
    factory_quality = factory_payload.get("factory_quality", {})
    artifact_summary = factory_payload.get("artifact_inventory", {}).get("summary", {})
    evidence_refs = [str(item) for item in factory_payload.get("repo_evidence", {}).get("evidence_refs", [])]
    if "factory_evidence_min" in expected:
        assert_minimum(failures, "factory_evidence_refs", int(factory_quality.get("evidence_ref_count", 0)), int(expected["factory_evidence_min"]))
    if "factory_skills_with_evidence_min" in expected:
        assert_minimum(failures, "factory_skills_with_evidence", int(factory_quality.get("skills_with_evidence", 0)), int(expected["factory_skills_with_evidence_min"]))
    if "factory_conflicts_min" in expected:
        assert_minimum(failures, "factory_conflicts", int(artifact_summary.get("conflict_count", 0)), int(expected["factory_conflicts_min"]))
    if "factory_stale_min" in expected:
        assert_minimum(failures, "factory_stale", int(artifact_summary.get("stale_count", 0)), int(expected["factory_stale_min"]))
    if "factory_generic_output" in expected:
        assert_equal(failures, "factory_generic_output", bool(factory_quality.get("generic_output", False)), bool(expected["factory_generic_output"]))
    if "factory_evidence_contains" in expected:
        assert_contains_all(failures, "factory_evidence_refs", evidence_refs, list(expected["factory_evidence_contains"]))
    assert_range(
        failures,
        "readiness",
        int(summary["readiness"]),
        int(expected.get("readiness_min", 0)),
        int(expected.get("readiness_max", 100)),
    )
    if before != after:
        failures.append("read-only commands changed fixture files")

    high_risk_guard = write_policy.write_guard("fixture-test", "high-risk", None, False)
    if not high_risk_guard or high_risk_guard.get("required_flag") != "--confirm-write":
        failures.append("high-risk write guard did not require --confirm-write")
    new_project_guard = write_policy.write_guard("fixture-test", "new-project", None, False)
    if new_project_guard is not None:
        failures.append("new-project default write guard unexpectedly blocked writes")

    return {
        "id": fixture_id,
        "path": str(root),
        "phase": phase,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "observed": {
            "project_type": summary["project_type"],
            "readiness": summary["readiness"],
            "loop_status": loop_payload["status"],
            "next_action": next_action["id"],
            "eval_tasks": summary["eval_tasks"],
            "factory_label": factory_payload["team_factory"]["label"],
            "factory_evidence_refs": factory_quality.get("evidence_ref_count", 0),
            "factory_generic_output": factory_quality.get("generic_output", False),
            "factory_skills_with_evidence": factory_quality.get("skills_with_evidence", 0),
            "factory_conflicts": artifact_summary.get("conflict_count", 0),
            "factory_stale": artifact_summary.get("stale_count", 0),
            "diagnosis_findings": len(diagnosis["readiness"]["findings"]),
            "harness_files": len(repo_scan.get("files", [])),
            "eval_mode": eval_payload.get("evaluation_mode", ""),
        },
    }


def run_fixtures(fixtures_root: Path, selected: list[str] | None = None) -> dict[str, Any]:
    manifest = load_manifest(fixtures_root)
    selected_set = set(selected or [])
    fixtures = []
    for fixture in manifest["fixtures"]:
        fixture_id = str(fixture["id"])
        if selected_set and fixture_id not in selected_set:
            continue
        fixtures.append(fixture)
    if selected_set:
        found = {str(fixture["id"]) for fixture in fixtures}
        missing = sorted(selected_set - found)
        if missing:
            raise ValueError(f"Unknown fixture id(s): {', '.join(missing)}")

    results = [run_fixture(fixtures_root, fixture) for fixture in fixtures]
    failed = [result for result in results if result["status"] != "pass"]
    return {
        "schema": "repo-harness-tuner.fixture-test.v1",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "fixtures_root": str(fixtures_root.resolve()),
        "count": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }


def print_report(payload: dict[str, Any]) -> None:
    print("Fixture Golden Tests")
    print(f"Fixtures: {payload['count']}")
    print(f"Passed: {payload['passed']}")
    print(f"Failed: {payload['failed']}")
    print("")
    for result in payload["results"]:
        observed = result.get("observed", {})
        print(f"- {result['status']}: {result['id']}")
        if observed:
            print(
                "  "
                f"{observed['project_type']} readiness={observed['readiness']} "
                f"next={observed['next_action']} eval_tasks={observed['eval_tasks']} "
                f"factory_evidence={observed.get('factory_evidence_refs', 0)} "
                f"conflicts={observed.get('factory_conflicts', 0)}"
            )
        for failure in result.get("failures", []):
            print(f"  failure: {failure}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-root", default=str(DEFAULT_FIXTURES_ROOT))
    parser.add_argument("--fixture", action="append", help="Run one fixture id. Can be repeated.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = run_fixtures(Path(args.fixtures_root), args.fixture)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_report(payload)
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
