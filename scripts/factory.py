#!/usr/bin/env python3
"""Design Codex agent-team and skill factory plans from repo/domain evidence."""
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
worker_patterns = load_local_module("worker_patterns")
write_policy = load_local_module("write_policy")


DOMAIN_PRESETS: dict[str, dict[str, Any]] = {
    "research": {
        "keywords": ["research", "deep research", "academic", "market", "investigate"],
        "label": "Research Team",
        "roles": [
            ("research-analyst", "Map the question space, source types, and unknowns."),
            ("source-reviewer", "Check source quality, contradictions, and missing evidence."),
            ("synthesis-writer", "Merge findings into concise decisions and next questions."),
        ],
        "skills": [
            ("source-triage", "Classify sources by authority, recency, and relevance."),
            ("cross-validation", "Compare claims across independent evidence."),
            ("synthesis-briefing", "Produce a concise decision-ready research brief."),
        ],
        "preferred_pattern": "fanout-review",
    },
    "website": {
        "keywords": ["website", "web app", "frontend", "react", "next", "vite", "landing"],
        "label": "Website Development Team",
        "roles": [
            ("product-designer", "Translate user intent into screen states and UX constraints."),
            ("frontend-builder", "Implement UI with existing framework and design patterns."),
            ("visual-qa-reviewer", "Check responsive layout, interaction evidence, and polish."),
        ],
        "skills": [
            ("screen-state-design", "Define expected screens, empty/loading/error states, and controls."),
            ("frontend-implementation", "Implement UI changes using local components and scripts."),
            ("browser-evidence-review", "Collect visual or browser evidence for user-facing changes."),
        ],
        "preferred_pattern": "producer-reviewer",
    },
    "game": {
        "keywords": ["game", "unity", "godot", "unreal", "gameplay", "ui hud"],
        "label": "Game Development Team",
        "roles": [
            ("gameplay-designer", "Define player-facing behavior, risk, and acceptance evidence."),
            ("implementation-builder", "Apply scoped code, scene, prefab, or asset-adjacent changes."),
            ("playtest-reviewer", "Review validation, screenshots, editor gaps, and regressions."),
        ],
        "skills": [
            ("gameplay-scope", "Separate gameplay intent, UI evidence, and asset risk."),
            ("engine-change-plan", "Plan engine/editor-safe implementation and validation."),
            ("playtest-evidence", "Record playtest, editor, or unavailable validation evidence."),
        ],
        "preferred_pattern": "producer-reviewer",
    },
    "documentation": {
        "keywords": ["documentation", "docs", "api docs", "readme", "technical writing"],
        "label": "Documentation Team",
        "roles": [
            ("source-analyzer", "Find source-of-truth files and existing terminology."),
            ("doc-writer", "Draft scoped documentation that preserves project voice."),
            ("completeness-reviewer", "Check examples, links, gaps, and over-process risk."),
        ],
        "skills": [
            ("source-map", "Map doc claims back to authoritative project sources."),
            ("docs-drafting", "Write concise docs for the target audience and task."),
            ("docs-review", "Review clarity, completeness, and stale-source risk."),
        ],
        "preferred_pattern": "producer-reviewer",
    },
    "data": {
        "keywords": ["data", "etl", "pipeline", "analytics", "schema", "migration"],
        "label": "Data Pipeline Team",
        "roles": [
            ("data-modeler", "Identify schema, ownership, privacy, and rollback risk."),
            ("pipeline-builder", "Plan or implement scoped pipeline changes."),
            ("validation-reviewer", "Check dry-run, sample data, rollback, and monitoring evidence."),
        ],
        "skills": [
            ("data-risk-profile", "Identify privacy, migration, data-loss, and rollback triggers."),
            ("pipeline-design", "Design pipeline steps and validation boundaries."),
            ("data-validation", "Define dry-run, sample, and rollback evidence."),
        ],
        "preferred_pattern": "visible-decision-thread",
    },
    "generic": {
        "keywords": [],
        "label": "General Project Team",
        "roles": [
            ("domain-analyst", "Map project goals, source-of-truth files, and unknowns."),
            ("implementation-builder", "Make scoped changes using local patterns."),
            ("quality-reviewer", "Review correctness, validation evidence, and remaining risk."),
        ],
        "skills": [
            ("domain-analysis", "Analyze repo/domain context before designing a team."),
            ("scoped-implementation", "Implement bounded changes with local conventions."),
            ("quality-review", "Review output against objective acceptance evidence."),
        ],
        "preferred_pattern": "supervisor-cycle",
    },
}


def classify_domain(domain: str, project_type: str) -> str:
    text = f"{domain} {project_type}".lower()
    for key, preset in DOMAIN_PRESETS.items():
        if key == "generic":
            continue
        if any(keyword in text for keyword in preset["keywords"]):
            return key
    if project_type in {"unity", "godot"}:
        return "game"
    if project_type in {"vite-node", "node"}:
        return "website"
    if project_type == "docs-only":
        return "documentation"
    return "generic"


def choose_pattern(preset: dict[str, Any], diagnosis: dict[str, Any], team_size: int) -> dict[str, Any]:
    human_involvement = int(diagnosis["human_involvement"])
    readiness = int(diagnosis["readiness"]["score"])
    if human_involvement >= 5:
        return worker_patterns.get_pattern("visible-decision-thread")
    if team_size >= 5 or readiness < 60:
        return worker_patterns.get_pattern("supervisor-cycle")
    return worker_patterns.get_pattern(str(preset["preferred_pattern"]))


def build_roles(preset: dict[str, Any], team_size: int) -> list[dict[str, Any]]:
    base_roles = preset["roles"]
    selected = base_roles[: max(1, min(team_size, len(base_roles)))]
    roles = []
    for index, (role_id, purpose) in enumerate(selected, start=1):
        roles.append(
            {
                "id": role_id,
                "order": index,
                "purpose": purpose,
                "visibility": "visible chat" if index == 1 and "decision" in purpose.lower() else "background/read-only by default",
                "outputs": ["concise findings", "file references when relevant", "validation or skipped-check reason"],
            }
        )
    return roles


def build_skills(preset: dict[str, Any], roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    skills = []
    for skill_id, purpose in preset["skills"]:
        skills.append(
            {
                "id": skill_id,
                "purpose": purpose,
                "target_file": f"Docs/AI/skills/{skill_id}.md",
                "status": "planned",
                "trigger": f"Use when work needs {purpose[0].lower() + purpose[1:]}",
            }
        )
    if roles:
        skills.append(
            {
                "id": "team-orchestration",
                "purpose": "Coordinate role order, handoffs, review gates, and merge evidence.",
                "target_file": "Docs/AI/team-orchestration.md",
                "status": "planned",
                "trigger": "Use when more than one Codex worker or visible decision point is needed.",
            }
        )
    return skills


def build_factory_plan(
    root: Path,
    domain: str,
    phase: str,
    modules: list[str] | None = None,
    human_involvement: int | None = None,
    repo_type: str | None = None,
    team_size: int = 3,
) -> dict[str, Any]:
    repo_scan = scan_repo_harness.scan(root)
    diagnosis = diagnose_module.diagnose(root, repo_scan, phase, modules, human_involvement, repo_type)
    project_type = str(diagnosis["harness_design"]["project_type"])
    domain_key = classify_domain(domain, project_type)
    preset = DOMAIN_PRESETS[domain_key]
    roles = build_roles(preset, team_size)
    skills = build_skills(preset, roles)
    pattern = choose_pattern(preset, diagnosis, team_size)
    return {
        "schema": "repo-harness-tuner.factory.v1",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "repo": str(root.resolve()),
        "domain": domain,
        "phase": phase,
        "project_type": project_type,
        "factory_goal": "Generate project-specific Codex worker teams and skill plans while the harness engine keeps them right-sized over time.",
        "harness_engine": {
            "readiness": diagnosis["readiness"],
            "history_feedback": diagnosis.get("history_feedback", {}),
            "human_involvement": diagnosis["human_involvement"],
            "next_review_trigger": diagnosis["harness_design"]["next_review_trigger"],
        },
        "team_factory": {
            "domain_key": domain_key,
            "label": preset["label"],
            "architecture_pattern": pattern,
            "roles": roles,
            "skills": skills,
            "orchestration": [
                "main thread owns final decisions, writes, and closeout",
                "use visible chat for approval, product direction, scope, release, or user-inspectable QA evidence",
                "use background/read-only workers for independent review, validation, and source checks",
                "persist only concise artifacts that future Codex sessions should reuse",
            ],
            "planned_outputs": [
                "Docs/AI/agent-team.md",
                "Docs/AI/skills/*.md",
                "Docs/AI/team-orchestration.md",
                "Docs/AI/harness-eval-plan.md",
            ],
            "next_steps": [
                "review this factory plan with the current human-involvement level",
                "generate repo-local team and skill docs before creating executable automation",
                "calibrate with eval golden tasks before treating the generated team as stable",
                "feed eval and history results back into diagnose/tune",
            ],
        },
    }


def write_factory_plan(root: Path, payload: dict[str, Any]) -> Path:
    docs_ai = root / "Docs" / "AI"
    docs_ai.mkdir(parents=True, exist_ok=True)
    path = docs_ai / "factory-plan.md"
    team = payload["team_factory"]
    engine = payload["harness_engine"]
    lines = [
        "# Factory Plan",
        "",
        f"Updated: {payload['created_at']}",
        f"Domain: {payload['domain']}",
        f"Project type: {payload['project_type']}",
        f"Phase: {payload['phase']}",
        f"Goal: {payload['factory_goal']}",
        f"Harness readiness: {engine['readiness']['score']}/{engine['readiness']['max_score']}",
        f"Human involvement: {engine['human_involvement']}/5",
        f"Next review trigger: {engine['next_review_trigger']}",
        "",
        "## Team Architecture",
        f"- Label: {team['label']}",
        f"- Pattern: {team['architecture_pattern']['label']} (`{team['architecture_pattern']['id']}`)",
        f"- Visibility: {team['architecture_pattern']['visibility']}",
        f"- Coordination: {team['architecture_pattern']['coordination']}",
        "",
        "## Roles",
    ]
    for role in team["roles"]:
        lines.append(f"- `{role['id']}`: {role['purpose']}")
    lines.extend(["", "## Planned Skills"])
    for skill in team["skills"]:
        lines.append(f"- `{skill['id']}` -> `{skill['target_file']}`: {skill['purpose']}")
    lines.extend(["", "## Orchestration"])
    lines.extend(f"- {item}" for item in team["orchestration"])
    lines.extend(["", "## Planned Outputs"])
    lines.extend(f"- `{item}`" for item in team["planned_outputs"])
    lines.extend(["", "## Next Steps"])
    lines.extend(f"- {item}" for item in team["next_steps"])
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def print_factory_plan(payload: dict[str, Any]) -> None:
    team = payload["team_factory"]
    engine = payload["harness_engine"]
    print(f"Factory goal: {payload['factory_goal']}")
    print(f"Repo: {payload['repo']}")
    print(f"Domain: {payload['domain']}")
    print(f"Project type: {payload['project_type']}")
    print(f"Readiness: {engine['readiness']['score']}/{engine['readiness']['max_score']}")
    print(f"Human involvement: {engine['human_involvement']}/5")
    print("")
    print("Team architecture:")
    print(f"- {team['label']}")
    print(f"- Pattern: {team['architecture_pattern']['label']} ({team['architecture_pattern']['id']})")
    print(f"- Visibility: {team['architecture_pattern']['visibility']}")
    print("")
    print("Roles:")
    for role in team["roles"]:
        print(f"- {role['id']}: {role['purpose']}")
    print("")
    print("Planned skills:")
    for skill in team["skills"]:
        print(f"- {skill['id']}: {skill['purpose']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--domain", default="current repository")
    parser.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    parser.add_argument("--module", action="append")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--repo-type", default="unknown")
    parser.add_argument("--team-size", type=int, default=3)
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo)
    payload = build_factory_plan(root, args.domain, args.phase, args.module, args.human_involvement, args.repo_type, args.team_size)
    if args.write_plan:
        guard = write_policy.write_guard("factory", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            payload["write_blocked"] = guard
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print_factory_plan(payload)
                print("")
                print(write_policy.format_guard(guard))
            return 2
        payload["plan_path"] = str(write_factory_plan(root.resolve(), payload))
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_factory_plan(payload)
        if args.write_plan:
            print("")
            print(f"Factory plan written: {payload['plan_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
