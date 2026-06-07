#!/usr/bin/env python3
"""Unified CLI for Repo Harness Tuner."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


def load_module(name: str):
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scan_skills = load_module("scan_skills")
scan_plugins = load_module("scan_plugins")
scan_repo_harness = load_module("scan_repo_harness")
generate_prompt = load_module("generate_prompt")
diagnose_module = load_module("diagnose")


def emit_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def print_skills(payload: dict[str, Any]) -> None:
    print(f"Skills found: {payload['count']}")
    for skill in payload["skills"]:
        description = skill.get("description", "")
        short = description[:96] + ("..." if len(description) > 96 else "")
        print(f"- {skill['name']}: {short}")
        print(f"  {skill['path']}")


def print_plugins(payload: dict[str, Any]) -> None:
    print(f"Plugins found: {payload['count']}")
    for plugin in payload["plugins"]:
        flags = []
        if plugin.get("has_skills"):
            flags.append("skills")
        if plugin.get("has_apps"):
            flags.append("apps")
        if plugin.get("has_mcp"):
            flags.append("mcp")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        print(f"- {plugin['name']} {plugin.get('version', '')}{suffix}")
        print(f"  {plugin['path']}")
    marketplace = payload["marketplace"]
    print(f"Marketplace: {marketplace['path']} exists={marketplace['exists']}")


def print_repo(payload: dict[str, Any]) -> None:
    print(f"Repo: {payload['root']}")
    print(f"Project type: {payload.get('project_type', 'unknown')}")
    markers = payload.get("project_markers", [])
    if markers:
        print("Project markers:")
        for marker in markers:
            print(f"- {marker}")
    print("Harness files:")
    if payload["files"]:
        for file in payload["files"]:
            print(f"- {file['path']} ({file['lines']} lines)")
    else:
        print("- none")
    if payload["missing_recommended"]:
        print("Missing recommended:")
        for rel in payload["missing_recommended"]:
            print(f"- {rel}")
    scripts = payload["package_scripts"]
    if scripts:
        print("Package scripts:")
        for name, command in scripts.items():
            print(f"- {name}: {command}")
    print(f"Docs/Reports entries: {payload['docs_reports_count']}")


def cmd_skills(args: argparse.Namespace) -> int:
    payload = {"skills": scan_skills.scan()}
    payload["count"] = len(payload["skills"])
    emit_json(payload) if args.json else print_skills(payload)
    return 0


def cmd_plugins(args: argparse.Namespace) -> int:
    payload = {"plugins": scan_plugins.scan_plugins(), "marketplace": scan_plugins.scan_marketplace()}
    payload["count"] = len(payload["plugins"])
    emit_json(payload) if args.json else print_plugins(payload)
    return 0


def cmd_repo(args: argparse.Namespace) -> int:
    payload = scan_repo_harness.scan(Path(args.repo))
    emit_json(payload) if args.json else print_repo(payload)
    return 0


def cmd_overview(args: argparse.Namespace) -> int:
    payload = {
        "skills": scan_skills.scan(),
        "plugins": scan_plugins.scan_plugins(),
        "marketplace": scan_plugins.scan_marketplace(),
        "repo": scan_repo_harness.scan(Path(args.repo)),
    }
    payload["counts"] = {
        "skills": len(payload["skills"]),
        "plugins": len(payload["plugins"]),
        "repo_harness_files": len(payload["repo"]["files"]),
    }
    if args.json:
        emit_json(payload)
    else:
        print("Repo Harness Tuner Overview")
        print("")
        print_skills({"skills": payload["skills"], "count": payload["counts"]["skills"]})
        print("")
        print_plugins({"plugins": payload["plugins"], "marketplace": payload["marketplace"], "count": payload["counts"]["plugins"]})
        print("")
        print_repo(payload["repo"])
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    prompt = generate_prompt.build_prompt(args)
    if args.json:
        emit_json({"prompt": prompt})
    else:
        print(prompt)
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    repo_scan = scan_repo_harness.scan(Path(args.repo))
    payload = diagnose_module.diagnose(Path(args.repo), repo_scan, args.phase, args.module, args.human_involvement, args.repo_type)
    if args.emit_prompt:
        payload["tuning_prompt"] = diagnose_module.build_tuning_prompt(payload, args.repo_type, args.module)
    if args.write_status:
        payload["status_path"] = str(diagnose_module.write_status(Path(args.repo).resolve(), payload))
    if args.write_plan:
        payload["plan_path"] = str(diagnose_module.write_design_plan(Path(args.repo).resolve(), payload))
    if args.json:
        emit_json(payload)
    else:
        diagnose_module.print_diagnosis(payload)
        if args.emit_prompt:
            print("")
            print("Tuning prompt:")
            print(payload["tuning_prompt"])
        if args.write_status:
            print("")
            print(f"Status written: {payload['status_path']}")
        if args.write_plan:
            print("")
            print(f"Design plan written: {payload['plan_path']}")
    return 0


def cmd_design(args: argparse.Namespace) -> int:
    repo_scan = scan_repo_harness.scan(Path(args.repo))
    payload = diagnose_module.diagnose(Path(args.repo), repo_scan, args.phase, args.module, args.human_involvement, args.repo_type)
    design = payload["harness_design"]
    if args.write_plan:
        payload["plan_path"] = str(diagnose_module.write_design_plan(Path(args.repo).resolve(), payload))
        design = dict(design)
        design["plan_path"] = payload["plan_path"]
    if args.json:
        emit_json({"harness_design": design})
    else:
        diagnose_module.print_harness_design(design)
        if args.write_plan:
            print("")
            print(f"Design plan written: {payload['plan_path']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    skills = sub.add_parser("skills", help="List installed skills.")
    skills.add_argument("--json", action="store_true")
    skills.set_defaults(func=cmd_skills)

    plugins = sub.add_parser("plugins", help="List installed plugins.")
    plugins.add_argument("--json", action="store_true")
    plugins.set_defaults(func=cmd_plugins)

    repo = sub.add_parser("repo", help="Scan a repository harness.")
    repo.add_argument("--repo", default=".")
    repo.add_argument("--json", action="store_true")
    repo.set_defaults(func=cmd_repo)

    overview = sub.add_parser("overview", help="Show skills, plugins, and repo harness.")
    overview.add_argument("--repo", default=".")
    overview.add_argument("--json", action="store_true")
    overview.set_defaults(func=cmd_overview)

    prompt = sub.add_parser("prompt", help="Generate a codex-harness-setup prompt.")
    prompt.add_argument("--mode", default="Setup", choices=["Audit only", "Setup", "Targeted upgrade", "Recovery", "Ambiguity profiling"])
    prompt.add_argument("--repo-type", default="unknown")
    prompt.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    prompt.add_argument("--default-ambiguity", type=int, default=3, choices=[1, 2, 3, 4, 5], help="Compatibility fallback when --human-involvement is not set.")
    prompt.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    prompt.add_argument("--module", action="append")
    prompt.add_argument("--visible-policy", default="product decisions, roadmap changes, QA evidence, user-facing specialist work")
    prompt.add_argument("--background-policy", default="read-only audits, code review, test review, security review, static scans")
    prompt.add_argument("--json", action="store_true")
    prompt.set_defaults(func=cmd_prompt)

    diagnose = sub.add_parser("diagnose", help="Score and tune repo harness readiness.")
    diagnose.add_argument("--repo", default=".")
    diagnose.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    diagnose.add_argument("--module", action="append", help="Module human-involvement override, for example 'Ending taxonomy: 5'.")
    diagnose.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    diagnose.add_argument("--repo-type", default="unknown")
    diagnose.add_argument("--emit-prompt", action="store_true", help="Append a codex-harness-setup prompt based on the diagnosis.")
    diagnose.add_argument("--write-status", action="store_true", help="Write Docs/AI/harness-status.md in the target repo.")
    diagnose.add_argument("--write-plan", action="store_true", help="Write Docs/AI/harness-design-plan.md in the target repo.")
    diagnose.add_argument("--json", action="store_true")
    diagnose.set_defaults(func=cmd_diagnose)

    design = sub.add_parser("design", help="Generate the next harness design plan.")
    design.add_argument("--repo", default=".")
    design.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    design.add_argument("--module", action="append", help="Module human-involvement override, for example 'Ending taxonomy: 5'.")
    design.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    design.add_argument("--repo-type", default="unknown")
    design.add_argument("--write-plan", action="store_true", help="Write Docs/AI/harness-design-plan.md in the target repo.")
    design.add_argument("--json", action="store_true")
    design.set_defaults(func=cmd_design)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
