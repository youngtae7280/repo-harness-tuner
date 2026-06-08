#!/usr/bin/env python3
"""Run release and fresh-clone simulation checks for Repo Harness Tuner."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

SCRIPT_FILES = [
    "scripts/console.py",
    "scripts/diagnose.py",
    "scripts/evaluate.py",
    "scripts/factory.py",
    "scripts/bootstrap.py",
    "scripts/history.py",
    "scripts/history_store.py",
    "scripts/loop.py",
    "scripts/skill_recommender.py",
    "scripts/fixture_test.py",
    "scripts/tune.py",
    "scripts/write_policy.py",
    "scripts/generate_prompt.py",
    "scripts/scan_plugins.py",
    "scripts/scan_repo_harness.py",
    "scripts/scan_skills.py",
    "scripts/worker_patterns.py",
    "scripts/release_validation.py",
]

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


def ignore_fresh_copy(directory: str, names: list[str]) -> set[str]:
    ignored = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
    return {name for name in names if name in ignored or name.endswith(".pyc")}


def copy_fresh_checkout(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=ignore_fresh_copy)


def run_command(cwd: Path, args: list[str], timeout: int = 60, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=merged_env,
    )


def check_result(name: str, ok: bool, detail: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "status": "pass" if ok else "fail",
        "detail": detail,
        "data": data or {},
    }


def command_check(name: str, cwd: Path, args: list[str], timeout: int = 60, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        result = run_command(cwd, args, timeout=timeout, env=env)
    except Exception as exc:  # pragma: no cover - defensive release check surface
        return check_result(name, False, f"command failed to run: {exc}")
    return check_result(
        name,
        result.returncode == 0,
        "command exited 0" if result.returncode == 0 else f"exit {result.returncode}",
        {
            "command": " ".join(args),
            "stdout_tail": result.stdout[-1200:],
            "stderr_tail": result.stderr[-1200:],
        },
    )


def json_command_check(
    name: str,
    cwd: Path,
    args: list[str],
    validator,
    timeout: int = 60,
) -> dict[str, Any]:
    try:
        completed = run_command(cwd, args, timeout=timeout)
    except Exception as exc:  # pragma: no cover - defensive release check surface
        return check_result(name, False, f"command failed to run: {exc}")
    data = {
        "command": " ".join(args),
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
    }
    if completed.returncode != 0:
        return check_result(name, False, f"exit {completed.returncode}", data)
    try:
        payload = json.loads(completed.stdout)
    except Exception as exc:
        return check_result(name, False, f"stdout was not valid JSON: {exc}", data)
    failures = validator(payload)
    return check_result(name, not failures, "JSON contract matched" if not failures else "; ".join(failures), {"summary": summarize_json(payload)})


def summarize_json(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    next_action = summary.get("next_action", {}) if isinstance(summary, dict) else {}
    return {
        "schema": payload.get("schema") if isinstance(payload, dict) else None,
        "status": payload.get("status") if isinstance(payload, dict) else None,
        "next_action": next_action.get("id") if isinstance(next_action, dict) else None,
        "next_action_type": next_action.get("action_type") if isinstance(next_action, dict) else None,
        "next_action_category": next_action.get("category") if isinstance(next_action, dict) else None,
        "next_action_has_apply": bool(next_action.get("apply_command")) if isinstance(next_action, dict) else False,
    }


def validate_loop_json(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if "harness_contract" not in payload:
        failures.append("missing harness_contract")
    next_action = payload.get("summary", {}).get("next_action", {})
    if not next_action.get("action_type"):
        failures.append("missing summary.next_action.action_type")
    if not next_action.get("category"):
        failures.append("missing summary.next_action.category")
    if not next_action.get("category_label"):
        failures.append("missing summary.next_action.category_label")
    preview = str(next_action.get("preview_command") or next_action.get("command") or "")
    apply_command = str(next_action.get("apply_command") or "")
    if next_action.get("command") != next_action.get("preview_command"):
        failures.append("summary.next_action.command must match preview_command")
    if command_flags(preview) & WRITE_FLAGS:
        failures.append("summary.next_action preview command contains write/install flags")
    if next_action.get("write_kind") != "none":
        if not apply_command:
            failures.append("summary.next_action missing apply_command for write action")
        elif not (command_flags(apply_command) & WRITE_FLAGS):
            failures.append("summary.next_action apply_command lacks write/install flag")
    return failures


def validate_fixture_json(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if int(payload.get("failed", 0) or 0) != 0:
        failures.append(f"fixture-test failed={payload.get('failed')}")
    if int(payload.get("journey_count", 0) or 0) < 2:
        failures.append("expected at least two user journey fixtures")
    return failures


def validate_skill_frontmatter(root: Path) -> dict[str, Any]:
    failures: list[str] = []
    skills_root = root / "skills"
    skill_files = sorted(skills_root.glob("*/SKILL.md"))
    if not skill_files:
        failures.append("no bundled SKILL.md files found")
    for path in skill_files:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if not text.startswith("---\n"):
            failures.append(f"{path.relative_to(root)} missing YAML frontmatter")
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            failures.append(f"{path.relative_to(root)} frontmatter is not closed")
            continue
        frontmatter = parts[1]
        if "name:" not in frontmatter:
            failures.append(f"{path.relative_to(root)} missing name")
        if "description:" not in frontmatter:
            failures.append(f"{path.relative_to(root)} missing description")
    return {
        "checked": len(skill_files),
        "failures": failures,
    }


def run_release_validation(source_root: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="rht-release-") as temp_dir:
        fresh_root = Path(temp_dir) / "repo-harness-tuner"
        copy_fresh_checkout(source_root, fresh_root)

        manifest_path = fresh_root / ".codex-plugin" / "plugin.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            checks.append(check_result("plugin-manifest-json", bool(manifest.get("name")), "plugin manifest parsed"))
        except Exception as exc:
            checks.append(check_result("plugin-manifest-json", False, f"plugin manifest failed to parse: {exc}"))

        skill_validation = validate_skill_frontmatter(fresh_root)
        checks.append(
            check_result(
                "bundled-skill-frontmatter",
                not skill_validation["failures"],
                "bundled skill frontmatter parsed" if not skill_validation["failures"] else "; ".join(skill_validation["failures"]),
                {"checked": skill_validation["checked"]},
            )
        )

        checks.append(command_check("py-compile", fresh_root, [sys.executable, "-m", "py_compile", *SCRIPT_FILES]))
        checks.append(
            json_command_check(
                "fixture-test-with-journeys",
                fresh_root,
                [sys.executable, "scripts/console.py", "fixture-test", "--json"],
                validate_fixture_json,
                timeout=120,
            )
        )
        loop_args = [
            sys.executable,
            "scripts/console.py",
            "next",
            "--repo",
            str(fresh_root),
            "--phase",
            "active-development",
            "--domain",
            "Codex plugin harness factory",
            "--json",
        ]
        checks.append(json_command_check("fresh-next-json", fresh_root, loop_args, validate_loop_json))
        doctor_args = loop_args.copy()
        doctor_args[2] = "doctor"
        checks.append(json_command_check("fresh-doctor-json", fresh_root, doctor_args, validate_loop_json))
        checks.append(
            command_check(
                "windows-console-ascii-smoke",
                fresh_root,
                [sys.executable, "scripts/console.py", "overview", "--repo", str(fresh_root)],
                env={"PYTHONIOENCODING": "ascii"},
            )
        )

        target_repo = Path(temp_dir) / "new-target"
        checks.append(
            json_command_check(
                "fresh-bootstrap-write-json",
                fresh_root,
                [
                    sys.executable,
                    "scripts/console.py",
                    "bootstrap",
                    "--repo",
                    str(target_repo),
                    "--phase",
                    "new-project",
                    "--write",
                    "--json",
                ],
                lambda payload: [] if (target_repo / "AGENTS.md").exists() and (target_repo / "Docs" / "AI" / "harness-profile.md").exists() else ["bootstrap did not write baseline harness files"],
            )
        )
        checks.append(
            command_check(
                "fresh-bootstrap-harness-check",
                fresh_root,
                [sys.executable, "skills/codex-harness-setup/scripts/check_harness.py", str(target_repo)],
            )
        )

    failed = [check for check in checks if check["status"] != "pass"]
    return {
        "schema": "repo-harness-tuner.release-validation.v1",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source_root": str(source_root),
        "mode": "fresh-copy-simulation",
        "count": len(checks),
        "passed": len(checks) - len(failed),
        "failed": len(failed),
        "checks": checks,
    }


def print_report(payload: dict[str, Any]) -> None:
    print("Release Validation")
    print(f"Mode: {payload['mode']}")
    print(f"Checks: {payload['count']} passed={payload['passed']} failed={payload['failed']}")
    print("")
    for check in payload["checks"]:
        print(f"- {check['status']}: {check['name']} - {check['detail']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(REPO_ROOT), help="Source checkout to copy and validate.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = run_release_validation(Path(args.repo))
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print_report(payload)
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
