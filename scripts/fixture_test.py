#!/usr/bin/env python3
"""Run fixture-based golden tests for Repo Harness Tuner."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import tempfile
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
    haystack = "\n".join(actual).replace("\\", "/").lower()
    for item in expected:
        needle = str(item).replace("\\", "/").lower()
        if needle not in haystack:
            failures.append(f"{label}: expected to contain {item!r}")


WRITE_FLAGS = {
    "--write",
    "--write-plan",
    "--write-recommended",
    "--write-artifacts",
    "--write-codex-skills",
    "--write-score",
    "--install",
    "--install-codex-skills",
}


def command_flags(command: str) -> set[str]:
    return set(re.findall(r"--[A-Za-z0-9-]+", command or ""))


def assert_preview_apply_split(failures: list[str], next_action: dict[str, Any]) -> None:
    preview = str(next_action.get("preview_command") or next_action.get("command") or "")
    apply_command = str(next_action.get("apply_command") or "")
    preview_flags = command_flags(preview)
    apply_flags = command_flags(apply_command)
    if next_action.get("command") != next_action.get("preview_command"):
        failures.append("next_action command must match preview_command")
    if preview_flags & WRITE_FLAGS:
        failures.append(f"next_action preview command contains write/install flag(s): {sorted(preview_flags & WRITE_FLAGS)}")
    if next_action.get("write_kind") != "none":
        if not apply_command:
            failures.append("next_action with write_kind must include apply_command")
        elif not (apply_flags & WRITE_FLAGS):
            failures.append("next_action apply_command must contain an explicit write/install flag")


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
    if next_action.get("action_type") != next_action.get("category"):
        failures.append("next_action action_type and category diverged")
    if "next_action_category" in expected:
        assert_equal(failures, "next_action_category", next_action.get("category"), expected.get("next_action_category"))
    assert_preview_apply_split(failures, next_action)
    assert_equal(failures, "eval_tasks", summary["eval_tasks"], expected.get("eval_tasks"))
    assert_equal(failures, "factory_label", factory_payload["team_factory"]["label"], expected.get("factory_label"))
    factory_quality = factory_payload.get("factory_quality", {})
    artifact_summary = factory_payload.get("artifact_inventory", {}).get("summary", {})
    evidence_refs = [str(item) for item in factory_payload.get("repo_evidence", {}).get("evidence_refs", [])]
    history_feedback = diagnosis.get("history_feedback", {})
    signal_types = [str(signal.get("type")) for signal in history_feedback.get("signals", []) if isinstance(signal, dict)]
    adaptive = loop_payload.get("adaptive", {})
    adaptive_cadence = adaptive.get("cadence", {}) if isinstance(adaptive, dict) else {}
    adaptive_involvement = adaptive.get("human_involvement", {}) if isinstance(adaptive, dict) else {}
    skill_payload = loop_payload.get("skill_recommendations", {})
    skill_summary = skill_payload.get("summary", {}) if isinstance(skill_payload, dict) else {}
    skill_recommendations = skill_payload.get("recommendations", []) if isinstance(skill_payload, dict) else []
    skill_sources = sorted({str(item.get("source")) for item in skill_recommendations if isinstance(item, dict)})
    skill_capabilities = sorted({str(item.get("capability")) for item in skill_recommendations if isinstance(item, dict)})
    skill_curator = skill_payload.get("curator", {}) if isinstance(skill_payload, dict) else {}
    harness_contract = loop_payload.get("harness_contract", {})
    required_contract_sections = ["scope", "access_actions", "definition_of_done", "human_approval_points"]
    missing_contract_sections = [section for section in required_contract_sections if section not in harness_contract]
    if missing_contract_sections:
        failures.append(f"harness_contract: missing sections {missing_contract_sections}")
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
    if "history_signals_min" in expected:
        assert_minimum(failures, "history_signals", len(signal_types), int(expected["history_signals_min"]))
    if "eval_score_records_min" in expected:
        assert_minimum(failures, "eval_score_records", int(history_feedback.get("eval_score_records", 0) or 0), int(expected["eval_score_records_min"]))
    if "review_pressure" in expected:
        assert_equal(failures, "review_pressure", history_feedback.get("review_pressure", "normal"), expected["review_pressure"])
    if "closed_loop_signal_contains" in expected:
        assert_contains_all(failures, "closed_loop_signals", signal_types, list(expected["closed_loop_signal_contains"]))
    if "adaptive_cadence_severity" in expected:
        assert_equal(
            failures,
            "adaptive_cadence_severity",
            adaptive_cadence.get("severity"),
            expected["adaptive_cadence_severity"],
        )
    if "adaptive_human_involvement_direction" in expected:
        assert_equal(
            failures,
            "adaptive_human_involvement_direction",
            adaptive_involvement.get("direction"),
            expected["adaptive_human_involvement_direction"],
        )
    if "adaptive_human_involvement_recommended" in expected:
        assert_equal(
            failures,
            "adaptive_human_involvement_recommended",
            adaptive_involvement.get("recommended_default"),
            expected["adaptive_human_involvement_recommended"],
        )
    if "adaptive_human_involvement_approval_required" in expected:
        assert_equal(
            failures,
            "adaptive_human_involvement_approval_required",
            bool(adaptive_involvement.get("approval_required")),
            bool(expected["adaptive_human_involvement_approval_required"]),
        )
    if "skill_recommendations_min" in expected:
        assert_minimum(
            failures,
            "skill_recommendations",
            int(skill_summary.get("recommendation_count", 0) or 0),
            int(expected["skill_recommendations_min"]),
        )
    if "skill_recommendation_source_contains" in expected:
        assert_contains_all(
            failures,
            "skill_recommendation_sources",
            skill_sources,
            list(expected["skill_recommendation_source_contains"]),
        )
    if "skill_recommendation_capability_contains" in expected:
        assert_contains_all(
            failures,
            "skill_recommendation_capabilities",
            skill_capabilities,
            list(expected["skill_recommendation_capability_contains"]),
        )
    if "skill_curator_action" in expected:
        assert_equal(failures, "skill_curator_action", skill_curator.get("action"), expected["skill_curator_action"])
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
            "next_action_category": next_action.get("category"),
            "eval_tasks": summary["eval_tasks"],
            "factory_label": factory_payload["team_factory"]["label"],
            "factory_evidence_refs": factory_quality.get("evidence_ref_count", 0),
            "factory_generic_output": factory_quality.get("generic_output", False),
            "factory_skills_with_evidence": factory_quality.get("skills_with_evidence", 0),
            "factory_conflicts": artifact_summary.get("conflict_count", 0),
            "factory_stale": artifact_summary.get("stale_count", 0),
            "history_signals": len(signal_types),
            "eval_score_records": history_feedback.get("eval_score_records", 0),
            "review_pressure": history_feedback.get("review_pressure", "normal"),
            "adaptive_cadence_severity": adaptive_cadence.get("severity", "normal"),
            "adaptive_human_involvement_direction": adaptive_involvement.get("direction", "keep"),
            "adaptive_human_involvement_recommended": adaptive_involvement.get("recommended_default"),
            "skill_recommendations": skill_summary.get("recommendation_count", 0),
            "skill_recommendation_sources": skill_sources,
            "skill_recommendation_capabilities": skill_capabilities,
            "skill_curator_action": skill_curator.get("action"),
            "harness_contract_sections": sorted(section for section in required_contract_sections if section in harness_contract),
            "diagnosis_findings": len(diagnosis["readiness"]["findings"]),
            "harness_files": len(repo_scan.get("files", [])),
            "eval_mode": eval_payload.get("evaluation_mode", ""),
        },
    }


def copy_fixture(fixtures_root: Path, fixture_path: str, workspace: Path) -> Path:
    source = fixtures_root / fixture_path
    destination = workspace / fixture_path.replace("/", "-").replace("\\", "-")
    shutil.copytree(source, destination)
    return destination


def run_user_journey_fixtures(fixtures_root: Path) -> list[dict[str, Any]]:
    journeys: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="rht-journey-") as temp_dir:
        workspace = Path(temp_dir)

        fresh_root = copy_fixture(fixtures_root, "vite-node-existing", workspace)
        failures: list[str] = []
        first = loop_module.build_loop_plan(fresh_root, "active-development", "Vite frontend app")
        first_action = first["summary"]["next_action"]
        assert_equal(failures, "first_next_action", first_action["id"], "bootstrap")
        assert_equal(failures, "first_next_action_category", first_action.get("category"), "planning")
        recommended = loop_module.apply_recommended(first, fresh_root)
        guard = recommended.get("auto_apply_guard", {})
        if recommended.get("blocked"):
            failures.append(f"bootstrap recommended write was blocked: {guard.get('reason', 'unknown reason')}")
        if not guard.get("allowed"):
            failures.append("bootstrap auto-apply guard did not allow managed harness files")
        written_paths = sorted(str(item.get("path", "")).replace("\\", "/") for item in recommended.get("results", []))
        assert_contains_all(
            failures,
            "bootstrap_written_paths",
            written_paths,
            ["AGENTS.md", "Docs/AI/harness-profile.md", "Docs/AI/validation.md", "Docs/AI/ambiguity-profile.md"],
        )
        second = loop_module.build_loop_plan(fresh_root, "active-development", "Vite frontend app")
        if second["summary"]["next_action"]["id"] == "bootstrap":
            failures.append("second next action should move past bootstrap after applying the managed write")
        if int(second["summary"].get("readiness", 0) or 0) < 90:
            failures.append(f"second readiness expected at least 90, got {second['summary'].get('readiness')}")
        journeys.append(
            {
                "id": "fresh-next-bootstrap-journey",
                "status": "pass" if not failures else "fail",
                "failures": failures,
                "observed": {
                    "first_next_action": first_action["id"],
                    "first_next_action_category": first_action.get("category"),
                    "written_paths": written_paths,
                    "second_next_action": second["summary"]["next_action"]["id"],
                    "second_next_action_category": second["summary"]["next_action"].get("category"),
                    "second_readiness": second["summary"].get("readiness"),
                },
            }
        )

        history_root = copy_fixture(fixtures_root, "harnessed-vite", workspace)
        failures = []
        first = loop_module.build_loop_plan(history_root, "active-development", "Vite frontend app")
        first_action = first["summary"]["next_action"]
        assert_equal(failures, "first_next_action", first_action["id"], "record-history")
        assert_equal(failures, "first_next_action_category", first_action.get("category"), "history")
        recommended = loop_module.apply_recommended(first, history_root)
        guard = recommended.get("auto_apply_guard", {})
        if recommended.get("blocked"):
            failures.append(f"history recommended write was blocked: {guard.get('reason', 'unknown reason')}")
        if not guard.get("allowed"):
            failures.append("history auto-apply guard did not allow harness history")
        written_paths = sorted(str(item.get("path", "")).replace("\\", "/") for item in recommended.get("results", []))
        assert_contains_all(failures, "history_written_paths", written_paths, ["Docs/AI/harness-history.jsonl"])
        history_path = history_root / "Docs" / "AI" / "harness-history.jsonl"
        if not history_path.exists() or not history_path.read_text(encoding="utf-8-sig").strip():
            failures.append("history file was not written with a record")
        second = loop_module.build_loop_plan(history_root, "active-development", "Vite frontend app")
        if second["summary"]["next_action"]["id"] == "record-history":
            failures.append("second next action should move past record-history after writing the baseline")
        journeys.append(
            {
                "id": "fit-next-history-journey",
                "status": "pass" if not failures else "fail",
                "failures": failures,
                "observed": {
                    "first_next_action": first_action["id"],
                    "first_next_action_category": first_action.get("category"),
                    "written_paths": written_paths,
                    "second_next_action": second["summary"]["next_action"]["id"],
                    "second_next_action_category": second["summary"]["next_action"].get("category"),
                    "history_entries": second["summary"].get("history_entries"),
                },
            }
        )
    return journeys


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
    journeys = [] if selected_set else run_user_journey_fixtures(fixtures_root)
    failed = [result for result in results if result["status"] != "pass"]
    journey_failed = [result for result in journeys if result["status"] != "pass"]
    return {
        "schema": "repo-harness-tuner.fixture-test.v1",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "fixtures_root": str(fixtures_root.resolve()),
        "count": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed) + len(journey_failed),
        "results": results,
        "journey_count": len(journeys),
        "journey_passed": len(journeys) - len(journey_failed),
        "journey_failed": len(journey_failed),
        "journeys": journeys,
    }


def print_report(payload: dict[str, Any]) -> None:
    print("Fixture Golden Tests")
    print(f"Fixtures: {payload['count']}")
    print(f"Passed: {payload['passed']}")
    print(f"Failed: {payload['failed']}")
    if payload.get("journey_count"):
        print(f"Journeys: {payload['journey_count']} passed={payload['journey_passed']} failed={payload['journey_failed']}")
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
                f"conflicts={observed.get('factory_conflicts', 0)} "
                f"signals={observed.get('history_signals', 0)} "
                f"pressure={observed.get('review_pressure', 'normal')} "
                f"adaptive={observed.get('adaptive_cadence_severity', 'normal')}/"
                f"{observed.get('adaptive_human_involvement_direction', 'keep')} "
                f"skills={observed.get('skill_recommendations', 0)}/"
                f"{observed.get('skill_curator_action', 'baseline')}"
            )
        for failure in result.get("failures", []):
            print(f"  failure: {failure}")
    for result in payload.get("journeys", []):
        observed = result.get("observed", {})
        print(f"- {result['status']}: {result['id']}")
        if observed:
            print(
                "  "
                f"first={observed.get('first_next_action')}:{observed.get('first_next_action_category')} "
                f"second={observed.get('second_next_action')}:{observed.get('second_next_action_category')}"
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
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print_report(payload)
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
