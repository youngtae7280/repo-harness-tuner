#!/usr/bin/env python3
"""Bootstrap or dry-run repo-local Codex harness files."""
from __future__ import annotations

import argparse
import importlib.util
import json
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


def package_scripts_text(repo_scan: dict[str, Any]) -> list[str]:
    if repo_scan.get("project_type") == "codex-plugin":
        return [
            "- Focused Python script check: `python -m py_compile scripts\\console.py scripts\\factory.py scripts\\diagnose.py`.",
            "- Broad script check: `python -m py_compile scripts\\console.py scripts\\diagnose.py scripts\\evaluate.py scripts\\factory.py scripts\\bootstrap.py scripts\\history.py scripts\\history_store.py scripts\\tune.py scripts\\write_policy.py scripts\\generate_prompt.py scripts\\scan_plugins.py scripts\\scan_repo_harness.py scripts\\scan_skills.py scripts\\worker_patterns.py`.",
            "- Skill validation on Windows: `python %USERPROFILE%\\.codex\\skills\\.system\\skill-creator\\scripts\\quick_validate.py skills\\repo-harness-tuner`.",
            "- Plugin validation on Windows: `python %USERPROFILE%\\.codex\\skills\\.system\\plugin-creator\\scripts\\validate_plugin.py .`.",
            "- Use the equivalent `$HOME/.codex/skills/.system/...` paths on Unix-like machines.",
            "- GitHub Actions broad check: `.github/workflows/validate.yml`.",
        ]
    scripts = repo_scan.get("package_scripts", {})
    if not isinstance(scripts, dict) or not scripts:
        return ["- Validation commands unknown: no package scripts detected; use manual only validation until project commands exist."]
    lines = []
    for name, command in scripts.items():
        lines.append(f"- `npm run {name}`: `{command}`")
    return lines


def generate_files(
    root: Path,
    phase: str,
    human_involvement: int | None = None,
    repo_type: str | None = None,
    modules: list[str] | None = None,
) -> dict[str, str]:
    repo_scan = scan_repo_harness.scan(root)
    diagnosis = diagnose_module.diagnose(root, repo_scan, phase, modules, human_involvement, repo_type)
    design = diagnosis["harness_design"]
    worker = design["worker_architecture"]
    involvement = diagnosis["human_involvement"]
    scripts = package_scripts_text(repo_scan)
    history_feedback = diagnosis.get("history_feedback", {})
    history_lines: list[str] = []
    if history_feedback.get("signals"):
        history_lines = [
            "",
            "## History Feedback",
            f"- Review pressure: {history_feedback.get('review_pressure', 'normal')}.",
            *[f"- {signal['type']}: {signal['detail']}" for signal in history_feedback["signals"]],
        ]
        if history_feedback.get("recommendations"):
            history_lines.extend(["", "History-informed tuning:"])
            history_lines.extend(f"- {item}" for item in history_feedback["recommendations"])

    agents = "\n".join(
        [
            "# Agent Instructions",
            "",
            "## Start Here",
            "- Read `README.md` when present, then `Docs/AI/harness-profile.md`, `Docs/AI/validation.md`, and `Docs/AI/ambiguity-profile.md`.",
            "- Keep changes scoped to the request and existing project patterns.",
            "- Prefer the smallest reversible edit that improves correctness, reviewability, or evidence.",
            "",
            "## Human Involvement",
            f"- Default human involvement: {involvement}/5.",
            "- Any `Ask before` rule in `Docs/AI/ambiguity-profile.md` is a stop condition before file edits.",
            "- Ask before destructive operations, dependency/release changes, secrets, migrations, or hard-to-reverse user-facing direction changes.",
            "",
            "## Worker Visibility",
            f"- Default worker pattern: {worker.get('label', worker['pattern'])} (`{worker['pattern']}`).",
            f"- Default visibility: {worker['default_visibility']}.",
            "- Use visible chats for approval, product, roadmap, UX, release, or scope decisions.",
            "- Use background/read-only review for focused code, test, security, validation, or harness audits.",
            "",
            "## Validation",
            "- Use `Docs/AI/validation.md` to choose focused checks.",
            "- Do not require full validation for every small task; explain skipped checks when validation is unavailable or not relevant.",
            "",
        ]
    )

    harness_profile = "\n".join(
        [
            "# Harness Profile",
            "",
            f"Project type: {design['project_label']} (`{design['project_type']}`)",
            f"Phase: `{phase}`",
            f"Human involvement: {involvement}/5",
            f"Recommended cadence: {diagnosis['cadence']}",
            f"Next review trigger: {design['next_review_trigger']}",
            "",
            "## Primary Risks",
            *[f"- {item}" for item in design["primary_risks"]],
            "",
            "## Baseline Harness",
            "- `AGENTS.md`: short entrypoint for Codex behavior.",
            "- `Docs/AI/harness-profile.md`: cycle sizing, worker pattern, and review cadence.",
            "- `Docs/AI/validation.md`: focused and broad validation guidance.",
            "- `Docs/AI/ambiguity-profile.md`: human-involvement and ask-before-edit rules.",
            "",
            "## Worker Pattern",
            f"- Selected pattern: {worker.get('label', worker['pattern'])} (`{worker['pattern']}`).",
            f"- Visibility: {worker['default_visibility']}.",
            f"- Coordination: {worker['coordination']}.",
            "",
            "Selection reasons:",
            *[f"- {item}" for item in worker.get("selection_reasons", [])],
            *history_lines,
            "",
            "## Usually Skip",
            "- New CI gates, release blockers, dependencies, or destructive scripts unless repeated evidence justifies them and the user approves.",
            "- Persistent reports for tiny changes.",
            "- Visible specialist chats when only final findings matter.",
            "",
        ]
    )

    validation = "\n".join(
        [
            "# Validation Guide",
            "",
            "Use the cheapest check that gives meaningful evidence for the change.",
            "",
            "## Detected Commands",
            *scripts,
            "",
            "## Selection Policy",
            "- Docs-only or prompt-only changes: review the changed text; skip code validation with a reason.",
            "- Narrow behavior changes: run the closest focused check.",
            "- Shared contracts, build config, release-facing changes, or broad refactors: run focused checks plus the broad build/QA command when available.",
            "- If a required tool is unavailable, record what was skipped and why.",
            "",
        ]
    )

    ambiguity = "\n".join(
        [
            "# Human Involvement Profile",
            "",
            "This file defines when Codex should ask before editing and when it may infer from repo context.",
            "",
            f"Default human involvement: {involvement}/5",
            "",
            "| Human involvement | Behavior | Ask before | Agent may decide |",
            "| --- | --- | --- | --- |",
            "| 1 | Mostly autonomous | Protected areas, destructive operations, secrets, release, dependencies | Small implementation details from local patterns |",
            "| 2 | Proceed with assumptions | User-visible direction changes, unclear ownership, protected areas | Routine refactors, docs/copy edits, focused validation |",
            "| 3 | Balanced default | Hard-to-reverse or user-visible direction changes | Ordinary implementation choices with clear repo precedent |",
            "| 4 | Ask focused questions | File edits when source of truth is unclear; product/UX/scope tradeoffs | Read-only inspection and diagnosis |",
            "| 5 | Explicit approval | Any file edit unless the user already approved the exact change | Read-only inspection only |",
            "",
            "## Always Ask Before",
            "- Destructive filesystem or data operations.",
            "- Dependency, release, CI, secret, credential, migration, or privacy-sensitive changes.",
            "- Product, roadmap, UX, narrative, or scope choices not answered by an existing source of truth.",
            "- Overwriting existing harness files with generated content.",
            "",
            "## Safe To Decide",
            "- Formatting, wording, or small docs improvements that preserve meaning.",
            "- Following clearly established local code and documentation patterns.",
            "- Choosing focused validation from `Docs/AI/validation.md`.",
            "",
        ]
    )

    return {
        "AGENTS.md": agents,
        "Docs/AI/harness-profile.md": harness_profile,
        "Docs/AI/validation.md": validation,
        "Docs/AI/ambiguity-profile.md": ambiguity,
    }


def plan_bootstrap(
    root: Path,
    phase: str,
    human_involvement: int | None = None,
    repo_type: str | None = None,
    modules: list[str] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    files = generate_files(root, phase, human_involvement, repo_type, modules)
    actions = []
    for rel, content in files.items():
        path = root / rel
        exists = path.exists()
        action = "overwrite" if exists and force else "skip" if exists else "create"
        actions.append(
            {
                "path": rel,
                "exists": exists,
                "action": action,
                "bytes": len(content.encode("utf-8")),
                "content": content,
            }
        )
    return {"repo": str(root.resolve()), "phase": phase, "force": force, "actions": actions}


def apply_bootstrap(plan: dict[str, Any], root: Path) -> list[dict[str, str]]:
    results = []
    for item in plan["actions"]:
        if item["action"] == "skip":
            results.append({"path": item["path"], "status": "skipped"})
            continue
        path = root / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item["content"], encoding="utf-8")
        results.append({"path": item["path"], "status": item["action"]})
    return results


def print_plan(plan: dict[str, Any], show_content: bool = False) -> None:
    print(f"Repo: {plan['repo']}")
    print(f"Phase: {plan['phase']}")
    print(f"Force overwrite: {plan['force']}")
    print("")
    print("Bootstrap actions:")
    for item in plan["actions"]:
        print(f"- {item['action']}: {item['path']} ({item['bytes']} bytes)")
        if show_content:
            print("```")
            print(item["content"].rstrip())
            print("```")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--phase", default="new-project", choices=sorted(diagnose_module.PHASES))
    parser.add_argument("--module", action="append")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--repo-type", default="unknown")
    parser.add_argument("--write", action="store_true", help="Write files. Default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing harness files when --write is set.")
    parser.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    parser.add_argument("--show-content", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo)
    plan = plan_bootstrap(root, args.phase, args.human_involvement, args.repo_type, args.module, args.force)
    if args.write:
        guard = write_policy.write_guard("bootstrap", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            plan["write_blocked"] = guard
            if args.json:
                print(json.dumps(plan, indent=2, ensure_ascii=True))
            else:
                print_plan(plan, args.show_content)
                print("")
                print(write_policy.format_guard(guard))
            return 2
        plan["results"] = apply_bootstrap(plan, root)
    if args.json:
        print(json.dumps(plan, indent=2, ensure_ascii=True))
    else:
        print_plan(plan, args.show_content)
        if args.write:
            print("")
            print("Results:")
            for result in plan["results"]:
                print(f"- {result['status']}: {result['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
