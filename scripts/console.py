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
worker_patterns = load_module("worker_patterns")
evaluate_module = load_module("evaluate")
bootstrap_module = load_module("bootstrap")
history_module = load_module("history")
tune_module = load_module("tune")
write_policy = load_module("write_policy")
factory_module = load_module("factory")


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
    if args.write_status or args.write_plan:
        guard = write_policy.write_guard("diagnose", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            payload["write_blocked"] = guard
            if args.json:
                emit_json(payload)
            else:
                print(write_policy.format_guard(guard))
            return 2
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
        guard = write_policy.write_guard("design", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            payload["write_blocked"] = guard
            if args.json:
                emit_json(payload)
            else:
                print(write_policy.format_guard(guard))
            return 2
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


def cmd_patterns(args: argparse.Namespace) -> int:
    if args.prompt:
        prompt = worker_patterns.build_worker_prompt(
            args.prompt,
            args.repo,
            args.phase,
            args.scope,
            args.human_involvement,
        )
        payload = {"pattern": worker_patterns.get_pattern(args.prompt), "prompt": prompt}
        if args.json:
            emit_json(payload)
        else:
            print(prompt)
        return 0
    payload = {"patterns": worker_patterns.list_patterns(), "count": len(worker_patterns.PATTERNS)}
    if args.json:
        emit_json(payload)
    else:
        print(f"Worker patterns: {payload['count']}")
        for pattern in payload["patterns"]:
            print(f"- {pattern['id']}: {pattern['label']} - {pattern['summary']}")
            print(f"  Visibility: {pattern['visibility']}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    if args.score:
        payload = evaluate_module.score_eval_results(Path(args.score))
        if args.json:
            emit_json(payload)
        else:
            evaluate_module.print_eval_score(payload)
        return 0
    payload = evaluate_module.build_eval_plan(Path(args.repo), args.phase, args.module, args.human_involvement, args.repo_type)
    if args.write_plan:
        guard = write_policy.write_guard("eval", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            payload["write_blocked"] = guard
            if args.json:
                emit_json(payload)
            else:
                evaluate_module.print_eval_plan(payload)
                print("")
                print(write_policy.format_guard(guard))
            return 2
        payload["plan_path"] = str(evaluate_module.write_eval_plan(Path(args.repo).resolve(), payload))
    if args.json:
        emit_json(payload)
    else:
        evaluate_module.print_eval_plan(payload)
        if args.write_plan:
            print("")
            print(f"Eval plan written: {payload['plan_path']}")
    return 0


def cmd_factory(args: argparse.Namespace) -> int:
    payload = factory_module.build_factory_plan(
        Path(args.repo),
        args.domain,
        args.phase,
        args.module,
        args.human_involvement,
        args.repo_type,
        args.team_size,
    )
    if args.write_plan:
        guard = write_policy.write_guard("factory", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            payload["write_blocked"] = guard
            if args.json:
                emit_json(payload)
            else:
                factory_module.print_factory_plan(payload)
                print("")
                print(write_policy.format_guard(guard))
            return 2
        payload["plan_path"] = str(factory_module.write_factory_plan(Path(args.repo).resolve(), payload))
    if args.json:
        emit_json(payload)
    else:
        factory_module.print_factory_plan(payload)
        if args.write_plan:
            print("")
            print(f"Factory plan written: {payload['plan_path']}")
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    plan = bootstrap_module.plan_bootstrap(
        Path(args.repo),
        args.phase,
        args.human_involvement,
        args.repo_type,
        args.module,
        args.force,
    )
    if args.write:
        guard = write_policy.write_guard("bootstrap", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            plan["write_blocked"] = guard
            if args.json:
                emit_json(plan)
            else:
                bootstrap_module.print_plan(plan, args.show_content)
                print("")
                print(write_policy.format_guard(guard))
            return 2
        plan["results"] = bootstrap_module.apply_bootstrap(plan, Path(args.repo))
    if args.json:
        emit_json(plan)
    else:
        bootstrap_module.print_plan(plan, args.show_content)
        if args.write:
            print("")
            print("Results:")
            for result in plan["results"]:
                print(f"- {result['status']}: {result['path']}")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    root = Path(args.repo)
    if args.record:
        event = history_module.build_event(
            root,
            args.phase,
            args.human_involvement,
            args.repo_type,
            args.module,
            args.note,
            args.event_type,
        )
        payload: dict[str, Any] = {"event": event}
        if args.write:
            payload["path"] = str(history_module.append_event(root, event))
        if args.json:
            emit_json(payload)
        else:
            print("History event:")
            print(f"- Type: {event['type']}")
            print(f"- Readiness: {event['readiness']}/100")
            print(f"- Worker pattern: {event['worker_label']} ({event['worker_pattern']})")
            if args.write:
                print(f"- Written: {payload['path']}")
    else:
        payload = history_module.summarize(history_module.load_history(root))
        emit_json(payload) if args.json else history_module.print_summary(root, payload)
    return 0


def cmd_tune(args: argparse.Namespace) -> int:
    payload = tune_module.build_proposals(
        Path(args.repo),
        args.phase,
        args.module,
        args.human_involvement,
        args.repo_type,
        args.force,
    )
    if args.write:
        guard = write_policy.write_guard("tune", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            payload["write_blocked"] = guard
            if args.json:
                emit_json(payload)
            else:
                tune_module.print_summary(payload, args.diff)
                print("")
                print(write_policy.format_guard(guard))
            return 2
        payload["results"] = tune_module.apply_proposals(payload, Path(args.repo), args.force)
    if args.json:
        emit_json(payload)
    else:
        tune_module.print_summary(payload, args.diff)
        if args.write:
            print("")
            print("Results:")
            for result in payload["results"]:
                print(f"- {result['status']}: {result['path']}")
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

    patterns = sub.add_parser("patterns", help="List Codex worker architecture patterns or build a worker prompt.")
    patterns.add_argument("--prompt", help="Build an assignment prompt for a specific pattern id.")
    patterns.add_argument("--repo", default=".")
    patterns.add_argument("--phase", default="active-development")
    patterns.add_argument("--scope", default="repo harness tuning")
    patterns.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    patterns.add_argument("--json", action="store_true")
    patterns.set_defaults(func=cmd_patterns)

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
    diagnose.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    diagnose.add_argument("--json", action="store_true")
    diagnose.set_defaults(func=cmd_diagnose)

    design = sub.add_parser("design", help="Generate the next harness design plan.")
    design.add_argument("--repo", default=".")
    design.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    design.add_argument("--module", action="append", help="Module human-involvement override, for example 'Ending taxonomy: 5'.")
    design.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    design.add_argument("--repo-type", default="unknown")
    design.add_argument("--write-plan", action="store_true", help="Write Docs/AI/harness-design-plan.md in the target repo.")
    design.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    design.add_argument("--json", action="store_true")
    design.set_defaults(func=cmd_design)

    eval_parser = sub.add_parser("eval", help="Create a with-harness vs baseline evaluation plan.")
    eval_parser.add_argument("--repo", default=".")
    eval_parser.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    eval_parser.add_argument("--module", action="append", help="Module human-involvement override, for example 'Ending taxonomy: 5'.")
    eval_parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    eval_parser.add_argument("--repo-type", default="unknown")
    eval_parser.add_argument("--write-plan", action="store_true", help="Write Docs/AI/harness-eval-plan.md in the target repo.")
    eval_parser.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    eval_parser.add_argument("--score", help="Score a JSON result file created from the eval result_schema.")
    eval_parser.add_argument("--json", action="store_true")
    eval_parser.set_defaults(func=cmd_eval)

    factory = sub.add_parser("factory", help="Design a Codex team/skill factory plan from repo and domain evidence.")
    factory.add_argument("--repo", default=".")
    factory.add_argument("--domain", default="current repository", help="Domain or product area, for example 'Unity tycoon game UI' or 'deep research'.")
    factory.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    factory.add_argument("--module", action="append", help="Module human-involvement override, for example 'Ending taxonomy: 5'.")
    factory.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    factory.add_argument("--repo-type", default="unknown")
    factory.add_argument("--team-size", type=int, default=3)
    factory.add_argument("--write-plan", action="store_true", help="Write Docs/AI/factory-plan.md in the target repo.")
    factory.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    factory.add_argument("--json", action="store_true")
    factory.set_defaults(func=cmd_factory)

    bootstrap = sub.add_parser("bootstrap", help="Dry-run or write a minimal repo Codex harness.")
    bootstrap.add_argument("--repo", default=".")
    bootstrap.add_argument("--phase", default="new-project", choices=sorted(diagnose_module.PHASES))
    bootstrap.add_argument("--module", action="append", help="Module human-involvement override, for example 'Ending taxonomy: 5'.")
    bootstrap.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    bootstrap.add_argument("--repo-type", default="unknown")
    bootstrap.add_argument("--write", action="store_true", help="Write files. Default is dry-run.")
    bootstrap.add_argument("--force", action="store_true", help="Overwrite existing harness files when --write is set.")
    bootstrap.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    bootstrap.add_argument("--show-content", action="store_true")
    bootstrap.add_argument("--json", action="store_true")
    bootstrap.set_defaults(func=cmd_bootstrap)

    apply_parser = sub.add_parser("apply", help="Alias for bootstrap; requires --write to modify files.")
    apply_parser.add_argument("--repo", default=".")
    apply_parser.add_argument("--phase", default="new-project", choices=sorted(diagnose_module.PHASES))
    apply_parser.add_argument("--module", action="append", help="Module human-involvement override, for example 'Ending taxonomy: 5'.")
    apply_parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    apply_parser.add_argument("--repo-type", default="unknown")
    apply_parser.add_argument("--write", action="store_true", help="Write files. Default is dry-run.")
    apply_parser.add_argument("--force", action="store_true", help="Overwrite existing harness files when --write is set.")
    apply_parser.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    apply_parser.add_argument("--show-content", action="store_true")
    apply_parser.add_argument("--json", action="store_true")
    apply_parser.set_defaults(func=cmd_bootstrap)

    history = sub.add_parser("history", help="Summarize or record harness tuning history.")
    history.add_argument("--repo", default=".")
    history.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    history.add_argument("--module", action="append", help="Module human-involvement override, for example 'Ending taxonomy: 5'.")
    history.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    history.add_argument("--repo-type", default="unknown")
    history.add_argument("--record", action="store_true", help="Build a diagnosis snapshot event.")
    history.add_argument("--write", action="store_true", help="Append the event to Docs/AI/harness-history.jsonl.")
    history.add_argument("--event-type", default="diagnosis-snapshot")
    history.add_argument("--note", default="")
    history.add_argument("--json", action="store_true")
    history.set_defaults(func=cmd_history)

    tune = sub.add_parser("tune", help="Generate dry-run harness tuning diffs.")
    tune.add_argument("--repo", default=".")
    tune.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    tune.add_argument("--module", action="append", help="Module human-involvement override, for example 'Ending taxonomy: 5'.")
    tune.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    tune.add_argument("--repo-type", default="unknown")
    tune.add_argument("--dry-run", action="store_true", help="Compatibility flag; dry-run is the default.")
    tune.add_argument("--diff", action="store_true", help="Print unified diff.")
    tune.add_argument("--write", action="store_true", help="Write proposed changes. Default is dry-run.")
    tune.add_argument("--force", action="store_true", help="Apply even when files changed since diff generation.")
    tune.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    tune.add_argument("--json", action="store_true")
    tune.set_defaults(func=cmd_tune)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
