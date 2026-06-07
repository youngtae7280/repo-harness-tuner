#!/usr/bin/env python3
"""Turn harness diagnosis into dry-run diffs or explicit file updates."""
from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import re
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
bootstrap_module = load_local_module("bootstrap")


MANAGED_START = "<!-- repo-harness-tuner:start:{name} -->"
MANAGED_END = "<!-- repo-harness-tuner:end:{name} -->"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def find_existing(root: Path, rels: list[str]) -> tuple[str, Path] | tuple[None, None]:
    for rel in rels:
        path = root / rel
        if path.exists():
            return rel, path
    return None, None


def normalize_newline(text: str) -> str:
    return text.rstrip() + "\n"


def managed_block(name: str, title: str, lines: list[str]) -> str:
    start = MANAGED_START.format(name=name)
    end = MANAGED_END.format(name=name)
    body = [start, f"## {title}", "", *lines, end]
    return "\n".join(body).rstrip() + "\n"


def upsert_managed_block(text: str, name: str, title: str, lines: list[str]) -> str:
    block = managed_block(name, title, lines)
    start = re.escape(MANAGED_START.format(name=name))
    end = re.escape(MANAGED_END.format(name=name))
    pattern = re.compile(f"{start}.*?{end}\\s*", re.DOTALL)
    text = normalize_newline(text)
    if pattern.search(text):
        return pattern.sub(block, text)
    return text.rstrip() + "\n\n" + block


def package_script_lines(repo_scan: dict[str, Any]) -> list[str]:
    scripts = repo_scan.get("package_scripts", {})
    if not isinstance(scripts, dict) or not scripts:
        return ["- Validation commands unknown: no package scripts detected; use manual only validation until project commands exist."]
    lines = []
    for name, command in scripts.items():
        lines.append(f"- `npm run {name}`: `{command}`")
    return lines


def validation_patch_lines(diagnosis: dict[str, Any], repo_scan: dict[str, Any]) -> list[str]:
    drift = diagnosis.get("drift", [])
    drift_names = {item.get("item") for item in drift if item.get("type") == "validation-script-drift"}
    script_lines = package_script_lines(repo_scan)
    if drift_names:
        script_lines = [line for line in script_lines if any(f"`npm run {name}`" in line for name in drift_names)]
    return [
        "Use these repo-detected validation commands when they match the change scope:",
        "",
        *script_lines,
        "",
        "Selection policy:",
        "- Prefer the closest focused check for narrow changes.",
        "- Run broad build/QA only for shared contracts, release-facing changes, or broad refactors.",
        "- If validation is unavailable or not relevant, record the skipped check and reason.",
    ]


def involvement_patch_lines(diagnosis: dict[str, Any]) -> list[str]:
    involvement = diagnosis["human_involvement"]
    worker = diagnosis["harness_design"]["worker_architecture"]
    return [
        f"Default human involvement: {involvement}/5.",
        f"Default worker pattern: {worker.get('label', worker['pattern'])} (`{worker['pattern']}`).",
        f"Default visibility: {worker['default_visibility']}.",
        "",
        "Ask before:",
        "- Any destructive filesystem or data operation.",
        "- Dependency, release, CI, secret, credential, migration, or privacy-sensitive changes.",
        "- Product, roadmap, UX, narrative, or scope choices not answered by an existing source of truth.",
        "- File edits when human involvement is 5 unless the user already approved the exact change.",
        "",
        "Agent may decide:",
        "- Routine implementation choices with clear repo precedent.",
        "- Focused validation selection from `Docs/AI/validation.md`.",
        "- Small docs/copy edits that preserve meaning.",
    ]


def harness_profile_patch_lines(diagnosis: dict[str, Any]) -> list[str]:
    design = diagnosis["harness_design"]
    worker = design["worker_architecture"]
    lines = [
        f"Phase: `{diagnosis['phase']}`.",
        f"Readiness: {diagnosis['readiness']['score']}/{diagnosis['readiness']['max_score']}.",
        f"Next review trigger: {design['next_review_trigger']}.",
        f"Selected worker pattern: {worker.get('label', worker['pattern'])} (`{worker['pattern']}`).",
        f"Coordination: {worker['coordination']}.",
        "",
        "Primary risks:",
    ]
    lines.extend(f"- {item}" for item in design["primary_risks"])
    if worker.get("selection_reasons"):
        lines.extend(["", "Pattern selection:"])
        lines.extend(f"- {item}" for item in worker["selection_reasons"])
    return lines


def agents_patch_lines(diagnosis: dict[str, Any]) -> list[str]:
    worker = diagnosis["harness_design"]["worker_architecture"]
    return [
        "Before editing harness-sensitive files, read `Docs/AI/harness-profile.md`, `Docs/AI/validation.md`, and `Docs/AI/ambiguity-profile.md` when present.",
        "Treat any `Ask before` rule in `Docs/AI/ambiguity-profile.md` as a stop condition before file edits.",
        f"Default human involvement is {diagnosis['human_involvement']}/5.",
        f"Default worker pattern is {worker.get('label', worker['pattern'])} (`{worker['pattern']}`) with {worker['default_visibility']}.",
        "Do not add CI gates, release blockers, dependencies, destructive scripts, or mandatory approvals without explicit user approval.",
    ]


def propose_existing_file(root: Path, rel: str, text: str, block_name: str, title: str, lines: list[str]) -> dict[str, Any] | None:
    proposed = upsert_managed_block(text, block_name, title, lines)
    if proposed == normalize_newline(text):
        return None
    return {
        "path": rel,
        "action": "update",
        "reason": f"add or update {title}",
        "before": normalize_newline(text),
        "after": proposed,
    }


def build_proposals(
    root: Path,
    phase: str,
    modules: list[str] | None = None,
    human_involvement: int | None = None,
    repo_type: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    repo_scan = scan_repo_harness.scan(root)
    diagnosis = diagnose_module.diagnose(root, repo_scan, phase, modules, human_involvement, repo_type)
    bootstrap_files = bootstrap_module.generate_files(root, phase, human_involvement, repo_type, modules)
    proposals: list[dict[str, Any]] = []
    notes: list[str] = []

    def ensure_or_update(
        rels: list[str],
        fallback_rel: str,
        bootstrap_rel: str,
        block_name: str,
        title: str,
        lines: list[str],
        reason: str,
    ) -> None:
        existing_rel, existing_path = find_existing(root, rels)
        if existing_path is None:
            proposals.append(
                {
                    "path": fallback_rel,
                    "action": "create",
                    "reason": reason,
                    "before": "",
                    "after": bootstrap_files[bootstrap_rel],
                }
            )
            return
        proposal = propose_existing_file(root, str(existing_rel), read_text(existing_path), block_name, title, lines)
        if proposal:
            proposals.append(proposal)

    missing = set(repo_scan.get("missing_recommended", []))
    has_drift = bool(diagnosis.get("drift"))
    has_involvement_gaps = bool(diagnosis.get("human_involvement_enforcement"))
    has_overhead = bool(diagnosis.get("process_overhead"))
    needs_profile = "Docs/AI/harness-profile.md" in missing or any(
        finding["status"] == "gap" and finding["title"] in {"Harness profile", "Worker visibility", "Human involvement policy"}
        for finding in diagnosis["readiness"]["findings"]
    )
    needs_validation = "Docs/AI/validation.md" in missing or has_drift or any(
        finding["status"] == "gap" and finding["title"] in {"Validation guide", "Script coverage"}
        for finding in diagnosis["readiness"]["findings"]
    )
    needs_involvement = "Docs/AI/ambiguity-profile.md" in missing or has_involvement_gaps
    needs_agents = "AGENTS.md" in missing or has_involvement_gaps or needs_profile

    if needs_agents:
        ensure_or_update(
            ["AGENTS.md"],
            "AGENTS.md",
            "AGENTS.md",
            "agents-core",
            "Repo Harness Tuner Core Rules",
            agents_patch_lines(diagnosis),
            "AGENTS.md is missing or needs links to harness policy",
        )
    if needs_profile:
        ensure_or_update(
            ["Docs/AI/harness-profile.md", "docs/ai/harness-profile.md"],
            "Docs/AI/harness-profile.md",
            "Docs/AI/harness-profile.md",
            "harness-profile",
            "Repo Harness Tuner Design",
            harness_profile_patch_lines(diagnosis),
            "harness profile is missing or lacks worker/human-involvement policy",
        )
    if needs_validation:
        ensure_or_update(
            ["Docs/AI/validation.md", "docs/ai/validation.md"],
            "Docs/AI/validation.md",
            "Docs/AI/validation.md",
            "validation",
            "Repo Harness Tuner Validation Update",
            validation_patch_lines(diagnosis, repo_scan),
            "validation guide is missing or stale",
        )
    if needs_involvement:
        ensure_or_update(
            ["Docs/AI/ambiguity-profile.md", "docs/ai/ambiguity-profile.md"],
            "Docs/AI/ambiguity-profile.md",
            "Docs/AI/ambiguity-profile.md",
            "human-involvement",
            "Repo Harness Tuner Human Involvement Rules",
            involvement_patch_lines(diagnosis),
            "human-involvement ask/decide policy is missing or unenforced",
        )
    if has_overhead:
        notes.append(
            "Overbroad process rules were detected. No automatic removal diff was generated; review the reported lines and demote broad rules manually."
        )
    if not proposals and not notes:
        notes.append("No harness diff recommended; current harness appears fit for the selected phase.")

    return {
        "schema": "repo-harness-tuner.tune.v1",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "repo": str(root.resolve()),
        "phase": phase,
        "force": force,
        "readiness": diagnosis["readiness"],
        "diagnosis": {
            "drift_count": len(diagnosis.get("drift", [])),
            "process_overhead_count": len(diagnosis.get("process_overhead", [])),
            "human_involvement_gap_count": len(diagnosis.get("human_involvement_enforcement", [])),
        },
        "proposals": proposals,
        "notes": notes,
    }


def unified_diff(proposal: dict[str, Any]) -> str:
    before = proposal["before"].splitlines(keepends=True)
    after = proposal["after"].splitlines(keepends=True)
    fromfile = f"a/{proposal['path']}" if proposal["before"] else "/dev/null"
    tofile = f"b/{proposal['path']}"
    return "".join(difflib.unified_diff(before, after, fromfile=fromfile, tofile=tofile, lineterm="\n"))


def build_diff(payload: dict[str, Any]) -> str:
    chunks = [unified_diff(proposal) for proposal in payload["proposals"]]
    return "\n".join(chunk for chunk in chunks if chunk)


def apply_proposals(payload: dict[str, Any], root: Path, force: bool = False) -> list[dict[str, str]]:
    results = []
    for proposal in payload["proposals"]:
        path = root / proposal["path"]
        if path.exists() and proposal["action"] == "create" and not force:
            results.append({"path": proposal["path"], "status": "skipped-existing"})
            continue
        if path.exists() and proposal["action"] == "update":
            current = normalize_newline(read_text(path))
            if current != proposal["before"] and not force:
                results.append({"path": proposal["path"], "status": "skipped-changed"})
                continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(proposal["after"], encoding="utf-8")
        results.append({"path": proposal["path"], "status": proposal["action"]})
    return results


def print_summary(payload: dict[str, Any], show_diff: bool = False) -> None:
    readiness = payload["readiness"]
    print(f"Repo: {payload['repo']}")
    print(f"Phase: {payload['phase']}")
    print(f"Readiness: {readiness['score']}/{readiness['max_score']}")
    print(f"Proposals: {len(payload['proposals'])}")
    for proposal in payload["proposals"]:
        print(f"- {proposal['action']}: {proposal['path']} - {proposal['reason']}")
    for note in payload["notes"]:
        print(f"- note: {note}")
    if show_diff:
        diff = build_diff(payload)
        print("")
        print(diff.rstrip() if diff else "No diff.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    parser.add_argument("--module", action="append")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--repo-type", default="unknown")
    parser.add_argument("--dry-run", action="store_true", help="Compatibility flag; dry-run is the default.")
    parser.add_argument("--diff", action="store_true", help="Print unified diff.")
    parser.add_argument("--write", action="store_true", help="Write proposed changes. Default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Apply even when files changed since diff generation.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo)
    payload = build_proposals(root, args.phase, args.module, args.human_involvement, args.repo_type, args.force)
    if args.write:
        payload["results"] = apply_proposals(payload, root, args.force)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_summary(payload, args.diff)
        if args.write:
            print("")
            print("Results:")
            for result in payload["results"]:
                print(f"- {result['status']}: {result['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
