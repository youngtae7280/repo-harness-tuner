#!/usr/bin/env python3
"""Design Codex agent-team and skill factory plans from repo/domain evidence."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
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

GENERATED_MARKER = "<!-- repo-harness-tuner:generated:factory -->"


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
    "codex-plugin": {
        "keywords": ["codex", "plugin", "skill", "harness", "agent scaffold"],
        "label": "Codex Plugin Team",
        "roles": [
            ("harness-designer", "Map project-specific agent behavior, human involvement, and worker policy."),
            ("plugin-builder", "Update plugin manifests, CLI scripts, skills, and generated artifacts."),
            ("validation-reviewer", "Check plugin validation, skill validation, cachebuster, and smoke evidence."),
        ],
        "skills": [
            ("plugin-contract-review", "Review plugin.json, marketplace expectations, and cachebuster requirements."),
            ("skill-trigger-design", "Design valid SKILL.md frontmatter, trigger wording, and bounded workflows."),
            ("cli-smoke-validation", "Define focused CLI smoke tests for factory, install, tune, and eval flows."),
        ],
        "preferred_pattern": "producer-reviewer",
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


def short_list(items: list[str], limit: int = 6) -> list[str]:
    return items[:limit]


def path_exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def collect_source_markers(root: Path, project_type: str) -> list[str]:
    markers: list[str] = []
    candidates_by_type = {
        "codex-plugin": [
            ".codex-plugin/plugin.json",
            ".mcp.json",
            ".app.json",
            "skills",
            "scripts",
        ],
        "vite-node": [
            "package.json",
            "vite.config.ts",
            "vite.config.js",
            "src",
        ],
        "node": [
            "package.json",
            "src",
            "lib",
        ],
        "unity": [
            "Assets",
            "ProjectSettings/ProjectVersion.txt",
            "Packages/manifest.json",
        ],
        "godot": [
            "project.godot",
            "scenes",
            "scripts",
        ],
        "python": [
            "pyproject.toml",
            "requirements.txt",
            "scripts",
            "src",
        ],
        "docs-only": [
            "README.md",
            "Docs",
            "docs",
        ],
    }
    for rel in candidates_by_type.get(project_type, ["README.md", "Docs", "docs", "src", "scripts"]):
        if path_exists(root, rel):
            markers.append(rel)
    if (root / "skills").exists():
        skill_files = sorted((root / "skills").glob("*/SKILL.md"))
        markers.extend(str(path.relative_to(root)).replace("\\", "/") for path in skill_files[:4])
    if (root / "scripts").exists():
        script_files = sorted((root / "scripts").glob("*.py"))
        markers.extend(str(path.relative_to(root)).replace("\\", "/") for path in script_files[:4])
    if (root / "src").exists():
        source_files = sorted(path for path in (root / "src").rglob("*") if path.is_file())
        markers.extend(str(path.relative_to(root)).replace("\\", "/") for path in source_files[:4])
    return short_list(dedupe(markers), 10)


def build_validation_commands(root: Path, project_type: str, package_scripts: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    for name in ["typecheck", "test", "build", "lint", "check", "validate"]:
        if name in package_scripts:
            commands.append(f"npm run {name}")
    if project_type == "codex-plugin":
        commands.extend(
            [
                "python -m py_compile scripts/*.py",
                "python <plugin-creator>/scripts/validate_plugin.py .",
                "python <skill-creator>/scripts/quick_validate.py skills/<skill-name>",
            ]
        )
    if project_type == "python":
        if (root / "pyproject.toml").exists():
            commands.append("python -m py_compile scripts/*.py")
        elif (root / "scripts").exists():
            commands.append("python -m py_compile scripts/*.py")
    if project_type == "unity":
        commands.append("Record Unity Editor/build validation when available.")
    if not commands:
        commands.append("Use project-specific validation from Docs/AI/validation.md when available.")
    return short_list(dedupe(commands), 8)


def collect_artifact_inventory(root: Path, planned_skill_ids: list[str] | None = None) -> dict[str, Any]:
    planned = {normalize_skill_name(skill_id) for skill_id in (planned_skill_ids or [])}
    docs_ai = root / "Docs" / "AI"
    artifact_paths = [
        "Docs/AI/factory-plan.md",
        "Docs/AI/agent-team.md",
        "Docs/AI/team-orchestration.md",
    ]
    for path in sorted((docs_ai / "skills").glob("*.md")) if (docs_ai / "skills").exists() else []:
        artifact_paths.append(str(path.relative_to(root)).replace("\\", "/"))
    for path in sorted((docs_ai / "codex-skills").glob("*/SKILL.md")) if (docs_ai / "codex-skills").exists() else []:
        artifact_paths.append(str(path.relative_to(root)).replace("\\", "/"))

    artifacts: list[dict[str, Any]] = []
    conflicts: list[dict[str, str]] = []
    stale: list[dict[str, str]] = []
    for rel in dedupe(artifact_paths):
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace") if path.suffix.lower() == ".md" else ""
        generated = GENERATED_MARKER in text
        artifact_id = path.parent.name if rel.endswith("/SKILL.md") else path.stem
        if "/skills/" in rel and rel.endswith(".md"):
            artifact_id = path.stem
        normalized_id = normalize_skill_name(artifact_id)
        status = "generated-existing" if generated else "unmanaged-existing"
        item = {
            "path": rel,
            "id": normalized_id,
            "status": status,
            "generated_marker": generated,
            "size_bytes": path.stat().st_size,
        }
        artifacts.append(item)
        if normalized_id in planned:
            conflicts.append(
                {
                    "type": "planned-skill-overlap",
                    "id": normalized_id,
                    "path": rel,
                    "update_path": "review existing content; use --force for generated files or --replace-unmanaged with --force for user-authored files",
                }
            )
        if not generated and rel.startswith("Docs/AI/"):
            stale.append(
                {
                    "type": "unmanaged-factory-artifact",
                    "path": rel,
                    "update_path": "preserve by default; review before replacing unmanaged content",
                }
            )

    installed_overlaps: list[dict[str, str]] = []
    install_root = default_skill_install_root()
    if install_root.exists():
        for skill_id in sorted(planned):
            candidate = install_root / skill_id
            if candidate.exists():
                installed_overlaps.append(
                    {
                        "id": skill_id,
                        "path": str(candidate),
                        "update_path": "review installed skill before using --force during confirmed install",
                    }
                )

    return {
        "artifacts": artifacts,
        "conflicts": conflicts,
        "stale": stale,
        "installed_overlaps": installed_overlaps,
        "summary": {
            "artifact_count": len(artifacts),
            "conflict_count": len(conflicts),
            "stale_count": len(stale),
            "installed_overlap_count": len(installed_overlaps),
        },
    }


def collect_repo_evidence(root: Path, repo_scan: dict[str, Any], project_type: str) -> dict[str, Any]:
    package_scripts = repo_scan.get("package_scripts", {})
    scripts = package_scripts if isinstance(package_scripts, dict) else {}
    harness_files = [str(item.get("path")) for item in repo_scan.get("files", []) if item.get("path")]
    project_markers = [str(item) for item in repo_scan.get("project_markers", [])]
    source_markers = collect_source_markers(root, project_type)
    validation_commands = build_validation_commands(root, project_type, scripts)
    refs = dedupe(project_markers + short_list(list(scripts), 5) + short_list(harness_files, 6) + source_markers)
    quality_signals = []
    if project_markers:
        quality_signals.append("project markers detected")
    if scripts:
        quality_signals.append("package scripts detected")
    if harness_files:
        quality_signals.append("harness files detected")
    if source_markers:
        quality_signals.append("source markers detected")
    if not quality_signals:
        quality_signals.append("minimal repo evidence available")
    return {
        "project_markers": project_markers,
        "package_scripts": [{"name": name, "command": str(command)} for name, command in scripts.items()],
        "harness_files": harness_files,
        "source_markers": source_markers,
        "validation_commands": validation_commands,
        "evidence_refs": refs,
        "quality_signals": quality_signals,
        "summary": summarize_evidence(project_type, refs, validation_commands),
    }


def summarize_evidence(project_type: str, refs: list[str], validation_commands: list[str]) -> str:
    if not refs:
        return f"{project_type} project with limited concrete markers; keep generated output conservative."
    ref_text = ", ".join(short_list(refs, 5))
    validation_text = ", ".join(short_list(validation_commands, 3))
    return f"{project_type} evidence: {ref_text}. Validation hints: {validation_text}."


def evidence_trigger_suffix(evidence: dict[str, Any]) -> str:
    refs = evidence.get("evidence_refs", [])
    if not refs:
        return "the repo has few concrete markers and needs conservative discovery first"
    return "repo evidence such as " + ", ".join(short_list([str(item) for item in refs], 4))


def role_purpose_with_evidence(purpose: str, evidence: dict[str, Any]) -> str:
    refs = evidence.get("evidence_refs", [])
    if not refs:
        return purpose
    return f"{purpose} Ground decisions in {', '.join(short_list([str(item) for item in refs], 3))}."


def skill_trigger_with_evidence(purpose: str, evidence: dict[str, Any]) -> str:
    base = (purpose[0].lower() + purpose[1:]).rstrip(".")
    return f"Use when work needs {base} with {evidence_trigger_suffix(evidence)}."


def dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def classify_domain(domain: str, project_type: str) -> str:
    if project_type == "codex-plugin":
        return "codex-plugin"
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


def build_roles(preset: dict[str, Any], team_size: int, evidence: dict[str, Any]) -> list[dict[str, Any]]:
    base_roles = preset["roles"]
    selected = base_roles[: max(1, min(team_size, len(base_roles)))]
    roles = []
    for index, (role_id, purpose) in enumerate(selected, start=1):
        roles.append(
            {
                "id": role_id,
                "order": index,
                "purpose": role_purpose_with_evidence(purpose, evidence),
                "visibility": "visible chat" if index == 1 and "decision" in purpose.lower() else "background/read-only by default",
                "evidence_refs": short_list([str(item) for item in evidence.get("evidence_refs", [])], 5),
                "outputs": [
                    "concise findings",
                    "repo evidence references when relevant",
                    "validation command or skipped-check reason",
                ],
            }
        )
    return roles


def build_skills(preset: dict[str, Any], roles: list[dict[str, Any]], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    skills = []
    for skill_id, purpose in preset["skills"]:
        validation_commands = [str(item) for item in evidence.get("validation_commands", [])]
        skills.append(
            {
                "id": skill_id,
                "purpose": purpose,
                "target_file": f"Docs/AI/skills/{skill_id}.md",
                "status": "planned",
                "trigger": skill_trigger_with_evidence(purpose, evidence),
                "evidence_refs": short_list([str(item) for item in evidence.get("evidence_refs", [])], 6),
                "validation": short_list(validation_commands, 4),
                "boundaries": [
                    "do not replace repo-specific validation with broad boilerplate",
                    "do not expand this skill beyond the detected project/domain markers",
                    "ask or escalate before release, dependency, secret, destructive, or user-visible direction changes",
                ],
            }
        )
    if roles:
        skills.append(
            {
                "id": "team-orchestration",
                "purpose": "Coordinate role order, handoffs, review gates, and merge evidence.",
                "target_file": "Docs/AI/team-orchestration.md",
                "status": "planned",
                "trigger": f"Use when more than one Codex worker or visible decision point is needed and {evidence_trigger_suffix(evidence)}.",
                "evidence_refs": short_list([str(item) for item in evidence.get("evidence_refs", [])], 6),
                "validation": short_list([str(item) for item in evidence.get("validation_commands", [])], 4),
                "boundaries": [
                    "do not spawn workers for small single-file changes",
                    "do not persist reports unless future Codex sessions need them",
                    "keep final writes and closeout owned by the main thread",
                ],
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
    evidence = collect_repo_evidence(root.resolve(), repo_scan, project_type)
    roles = build_roles(preset, team_size, evidence)
    skills = build_skills(preset, roles, evidence)
    artifact_inventory = collect_artifact_inventory(root.resolve(), [str(skill["id"]) for skill in skills])
    pattern = choose_pattern(preset, diagnosis, team_size)
    generic_output = bool(evidence["evidence_refs"]) and not any(skill.get("evidence_refs") for skill in skills)
    history_feedback = diagnosis.get("history_feedback", {})
    closed_loop = history_feedback.get("closed_loop", {})
    feedback_next_steps = [str(item) for item in history_feedback.get("recommendations", [])][:3]
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
            "history_feedback": history_feedback,
            "human_involvement": diagnosis["human_involvement"],
            "next_review_trigger": diagnosis["harness_design"]["next_review_trigger"],
        },
        "repo_evidence": evidence,
        "artifact_inventory": artifact_inventory,
        "factory_quality": {
            "generic_output": generic_output,
            "evidence_ref_count": len(evidence["evidence_refs"]),
            "skills_with_evidence": sum(1 for skill in skills if skill.get("evidence_refs")),
            "roles_with_evidence": sum(1 for role in roles if role.get("evidence_refs")),
            "conflict_count": artifact_inventory["summary"]["conflict_count"],
            "stale_count": artifact_inventory["summary"]["stale_count"],
            "closed_loop_signal_count": int(closed_loop.get("signal_count", len(history_feedback.get("signals", []))) or 0),
            "eval_score_records": int(history_feedback.get("eval_score_records", 0) or 0),
            "review_pressure": history_feedback.get("review_pressure", "normal"),
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
                "Docs/AI/codex-skills/*/SKILL.md",
                "Docs/AI/team-orchestration.md",
                "Docs/AI/harness-eval-plan.md",
            ],
            "next_steps": [
                "review this factory plan with the current human-involvement level",
                "review repo evidence and artifact conflicts before writing generated outputs",
                *feedback_next_steps,
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
    evidence = payload.get("repo_evidence", {})
    inventory = payload.get("artifact_inventory", {})
    feedback = engine.get("history_feedback", {})
    lines = [
        "# Factory Plan",
        GENERATED_MARKER,
        "",
        f"Updated: {payload['created_at']}",
        f"Domain: {payload['domain']}",
        f"Project type: {payload['project_type']}",
        f"Phase: {payload['phase']}",
        f"Goal: {payload['factory_goal']}",
        f"Harness readiness: {engine['readiness']['score']}/{engine['readiness']['max_score']}",
        f"Human involvement: {engine['human_involvement']}/5",
        f"Next review trigger: {engine['next_review_trigger']}",
        f"Review pressure: {feedback.get('review_pressure', 'normal')}",
        "",
        "## Team Architecture",
        f"- Label: {team['label']}",
        f"- Pattern: {team['architecture_pattern']['label']} (`{team['architecture_pattern']['id']}`)",
        f"- Visibility: {team['architecture_pattern']['visibility']}",
        f"- Coordination: {team['architecture_pattern']['coordination']}",
        "",
        "## Repo Evidence",
        f"- Summary: {evidence.get('summary', 'No concrete evidence summary available.')}",
    ]
    for item in evidence.get("evidence_refs", []):
        lines.append(f"- Evidence: `{item}`")
    if feedback.get("signals"):
        lines.extend(["", "## Closed-Loop Feedback"])
        lines.append(f"- Eval score records: {feedback.get('eval_score_records', 0)}")
        for signal in feedback.get("signals", []):
            lines.append(f"- {signal['type']}: {signal['detail']}")
        for recommendation in feedback.get("recommendations", []):
            lines.append(f"- Recommendation: {recommendation}")
    lines.extend(["", "## Artifact Inventory"])
    summary = inventory.get("summary", {})
    lines.append(
        "- Existing artifacts: "
        f"{summary.get('artifact_count', 0)}, conflicts: {summary.get('conflict_count', 0)}, "
        f"stale/unmanaged: {summary.get('stale_count', 0)}, installed overlaps: {summary.get('installed_overlap_count', 0)}"
    )
    for item in inventory.get("conflicts", []):
        lines.append(f"- Conflict `{item['id']}` at `{item['path']}`: {item['update_path']}")
    for item in inventory.get("stale", []):
        lines.append(f"- Unmanaged `{item['path']}`: {item['update_path']}")
    lines.extend(
        [
            "",
        "## Roles",
        ]
    )
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


def build_agent_team_doc(payload: dict[str, Any]) -> str:
    team = payload["team_factory"]
    engine = payload["harness_engine"]
    evidence = payload.get("repo_evidence", {})
    inventory = payload.get("artifact_inventory", {})
    feedback = engine.get("history_feedback", {})
    lines = [
        "# Agent Team",
        GENERATED_MARKER,
        "",
        f"Domain: {payload['domain']}",
        f"Project type: {payload['project_type']}",
        f"Phase: {payload['phase']}",
        f"Harness readiness: {engine['readiness']['score']}/{engine['readiness']['max_score']}",
        f"Human involvement: {engine['human_involvement']}/5",
        "",
        "## Team Goal",
        payload["factory_goal"],
        "",
        "## Repo Evidence",
        f"- Summary: {evidence.get('summary', 'No concrete evidence summary available.')}",
    ]
    for item in evidence.get("evidence_refs", []):
        lines.append(f"- `{item}`")
    inventory_summary = inventory.get("summary", {})
    lines.extend(
        [
            "",
            "## Existing Artifact Signals",
            f"- Existing artifacts: {inventory_summary.get('artifact_count', 0)}",
            f"- Conflicts: {inventory_summary.get('conflict_count', 0)}",
            f"- Stale or unmanaged artifacts: {inventory_summary.get('stale_count', 0)}",
            "",
            "## Closed-Loop Feedback",
            f"- Review pressure: {feedback.get('review_pressure', 'normal')}",
            f"- Eval score records: {feedback.get('eval_score_records', 0)}",
            f"- Signals: {len(feedback.get('signals', []))}",
            "",
            "## Architecture",
            f"- Team: {team['label']}",
            f"- Pattern: {team['architecture_pattern']['label']} (`{team['architecture_pattern']['id']}`)",
            f"- Visibility: {team['architecture_pattern']['visibility']}",
            f"- Coordination: {team['architecture_pattern']['coordination']}",
            "",
            "## Roles",
        ]
    )
    for role in team["roles"]:
        lines.extend(
            [
                f"### {role['id']}",
                f"- Purpose: {role['purpose']}",
                f"- Visibility: {role['visibility']}",
                "- Outputs:",
                *[f"  - {item}" for item in role["outputs"]],
                "",
            ]
        )
    lines.extend(
        [
            "## Operating Rules",
            "- The main Codex thread owns final decisions, writes, and closeout.",
            "- Use visible chats for user-inspectable decisions, approval, product direction, release, or QA evidence.",
            "- Use background/read-only workers for independent review, validation, source checks, and bounded audits.",
            "- Keep persisted artifacts concise enough for future Codex sessions to reuse.",
            "",
            "## Evaluation",
            "- Run `repo-harness-tuner eval` when the team materially changes.",
            "- Record repeated misses with `repo-harness-tuner history` so the harness engine can tune this team over time.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_skill_doc(payload: dict[str, Any], skill: dict[str, Any]) -> str:
    team = payload["team_factory"]
    related_roles = ", ".join(role["id"] for role in team["roles"]) or "main Codex thread"
    lines = [
        f"# {skill['id']}",
        GENERATED_MARKER,
        "",
        f"Status: {skill['status']}",
        f"Domain: {payload['domain']}",
        f"Team: {team['label']}",
        "",
        "## Purpose",
        skill["purpose"],
        "",
        "## Trigger",
        skill["trigger"],
        "",
        "## Related Roles",
        related_roles,
        "",
        "## Repo Evidence",
    ]
    for item in skill.get("evidence_refs", []):
        lines.append(f"- `{item}`")
    if not skill.get("evidence_refs"):
        lines.append("- No concrete repo evidence available; start with conservative discovery.")
    lines.extend(
        [
            "",
            "## Validation",
        ]
    )
    for item in skill.get("validation", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Boundaries"])
    for item in skill.get("boundaries", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Workflow",
            "1. Inspect the repo source of truth before adding process.",
            "2. Keep scope bounded to the current task and domain.",
            "3. Produce concise evidence that the main thread can merge.",
            "4. Escalate to visible user review for product direction, release, destructive operations, dependencies, secrets, or privacy-sensitive changes.",
            "",
            "## Evidence",
            "- concise findings or decision summary",
            "- file references when relevant",
            "- validation command, skipped-check reason, or manual evidence",
            "",
            "## Tuning",
            "Use `repo-harness-tuner diagnose`, `history`, and `eval --score` to decide whether this skill should be kept, revised, or retired.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def normalize_skill_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return (normalized or "generated-skill")[:64].strip("-") or "generated-skill"


def yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def trigger_phrase(value: str) -> str:
    text = value.strip()
    lowered = text.lower()
    if lowered.startswith("use when "):
        return text[9:]
    return text


def build_codex_skill_md(payload: dict[str, Any], skill: dict[str, Any]) -> str:
    skill_name = normalize_skill_name(str(skill["id"]))
    team = payload["team_factory"]
    related_roles = ", ".join(role["id"] for role in team["roles"]) or "main Codex thread"
    evidence_refs = [str(item) for item in skill.get("evidence_refs", [])]
    evidence_text = ", ".join(short_list(evidence_refs, 4)) if evidence_refs else "limited concrete repo markers"
    description = (
        f"{skill['purpose']} Use when Codex is working on {payload['domain']} and needs "
        f"{trigger_phrase(str(skill.get('trigger', 'this workflow')))}, "
        f"grounded in {evidence_text}, bounded scope, and handoff back to the main thread."
    )
    lines = [
        "---",
        f"name: {skill_name}",
        f"description: {yaml_scalar(description)}",
        "---",
        "",
        f"# {skill_name}",
        GENERATED_MARKER,
        "",
        "## Purpose",
        skill["purpose"],
        "",
        "## Trigger",
        skill["trigger"],
        "",
        "## Repo Evidence",
    ]
    for item in evidence_refs:
        lines.append(f"- `{item}`")
    if not evidence_refs:
        lines.append("- No concrete repo evidence available; begin with conservative discovery.")
    lines.extend(
        [
            "",
            "## Validation",
        ]
    )
    for item in skill.get("validation", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Boundaries"])
    for item in skill.get("boundaries", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Use",
            "- Inspect the repository source of truth before adding new process.",
            "- Keep the work bounded to the current request and domain.",
            "- Return concise evidence that the main Codex thread can merge.",
            "- Escalate to visible user review for product direction, release, destructive operations, dependencies, secrets, or privacy-sensitive changes.",
            "",
            "## Related Roles",
            related_roles,
            "",
            "## Expected Evidence",
            "- concise findings or decision summary",
            "- file references when relevant",
            "- validation command, skipped-check reason, or manual evidence",
            "",
            "## Tuning",
            "Revise or retire this skill when `repo-harness-tuner eval --score` or `repo-harness-tuner history` shows no improvement, repeated misses, or unnecessary overhead.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_orchestration_doc(payload: dict[str, Any]) -> str:
    team = payload["team_factory"]
    evidence = payload.get("repo_evidence", {})
    lines = [
        "# Team Orchestration",
        GENERATED_MARKER,
        "",
        f"Domain: {payload['domain']}",
        f"Pattern: {team['architecture_pattern']['label']} (`{team['architecture_pattern']['id']}`)",
        f"Repo evidence: {evidence.get('summary', 'No concrete evidence summary available.')}",
        "",
        "## Default Flow",
        "1. Main thread analyzes the request, repo state, and human-involvement level.",
        "2. Main thread chooses whether a single-agent path is enough.",
        "3. If worker help is useful, assign bounded scopes using `patterns --prompt <pattern-id>` or the role purposes in `Docs/AI/agent-team.md`.",
        "4. Background workers return concise findings only; visible chats are used for decisions the user should inspect.",
        "5. Main thread merges findings, applies approved changes, runs validation, and records history when useful.",
        "",
        "## Visibility Policy",
        *[f"- {item}" for item in team["orchestration"]],
        "",
        "## Role Order",
    ]
    for role in sorted(team["roles"], key=lambda item: int(item["order"])):
        lines.append(f"- {role['order']}. `{role['id']}`: {role['purpose']}")
    lines.extend(
        [
            "",
            "## Stop Conditions",
            "- Human involvement 5 without explicit approval.",
            "- Destructive filesystem or data operations.",
            "- Dependency, release, CI, secret, credential, migration, or privacy-sensitive changes.",
            "- Product, roadmap, UX, narrative, or scope choices not answered by a repo source of truth.",
            "",
            "## Durable Artifacts",
            "- Persist only decisions, evidence, or role/skill guidance that future Codex sessions should reuse.",
            "- Prefer updating `Docs/AI/agent-team.md`, `Docs/AI/skills/*.md`, or `Docs/AI/harness-history.jsonl` over adding broad reports.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_file_once(root: Path, rel: str, content: str, force: bool, replace_unmanaged: bool = False) -> dict[str, str]:
    path = root / rel
    existed = path.exists()
    if existed:
        existing_text = path.read_text(encoding="utf-8-sig", errors="replace") if path.is_file() else ""
        generated = GENERATED_MARKER in existing_text
        if not force:
            flag = "--force" if generated else "--force --replace-unmanaged"
            return {
                "path": rel,
                "status": "skipped-existing",
                "reason": f"Existing {'generated' if generated else 'unmanaged'} file preserved; review and pass {flag} to replace.",
            }
        if not generated and not replace_unmanaged:
            return {
                "path": rel,
                "status": "blocked-unmanaged-existing",
                "reason": "Existing file has no repo-harness-tuner generated marker; pass --replace-unmanaged with --force after review to replace it.",
            }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if existed:
        status = "overwrite-unmanaged" if replace_unmanaged else "overwrite"
    else:
        status = "create"
    return {"path": rel, "status": status}


def validate_codex_skill_content(skill_name: str, content: str) -> list[str]:
    errors: list[str] = []
    if not content.startswith("---\n"):
        errors.append("missing YAML frontmatter")
        return errors
    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append("frontmatter is not closed")
        return errors
    frontmatter = parts[1]
    body = parts[2].strip()
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    if fields.get("name") != skill_name:
        errors.append(f"frontmatter name must be {skill_name}")
    if not fields.get("description"):
        errors.append("frontmatter description is required")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", fields.get("name", "")):
        errors.append("skill name must use lowercase letters, digits, and hyphens only")
    if not body:
        errors.append("skill body is required")
    return errors


def default_skill_install_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home) / "skills"
    return Path.home() / ".codex" / "skills"


def install_codex_skill_scaffolds(
    payload: dict[str, Any],
    install_root: Path | None = None,
    force: bool = False,
    replace_unmanaged: bool = False,
) -> list[dict[str, Any]]:
    root = (install_root or default_skill_install_root()).resolve()
    results: list[dict[str, Any]] = []
    for skill in payload["team_factory"]["skills"]:
        skill_name = normalize_skill_name(str(skill["id"]))
        content = build_codex_skill_md(payload, skill)
        errors = validate_codex_skill_content(skill_name, content)
        destination = root / skill_name
        if errors:
            results.append({"path": str(destination), "skill": skill_name, "status": "invalid", "errors": errors})
            continue
        if destination.exists() and not force:
            results.append({"path": str(destination), "skill": skill_name, "status": "skipped-existing"})
            continue
        existed = destination.exists()
        if existed:
            existing_skill = destination / "SKILL.md"
            existing_text = existing_skill.read_text(encoding="utf-8-sig", errors="replace") if existing_skill.exists() else ""
            generated = GENERATED_MARKER in existing_text
            if not generated and not replace_unmanaged:
                results.append(
                    {
                        "path": str(destination),
                        "skill": skill_name,
                        "status": "blocked-unmanaged-existing",
                        "reason": "Existing installed skill has no repo-harness-tuner generated marker; pass --replace-unmanaged with --force after review to replace it.",
                    }
                )
                continue
        if existed and force:
            shutil.rmtree(destination)
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "SKILL.md").write_text(content, encoding="utf-8")
        if existed:
            status = "overwrite-unmanaged" if replace_unmanaged else "overwrite"
        else:
            status = "installed"
        results.append({"path": str(destination), "skill": skill_name, "status": status})
    return results


def write_factory_artifacts(root: Path, payload: dict[str, Any], force: bool = False) -> list[dict[str, str]]:
    team = payload["team_factory"]
    results = [
        write_file_once(root, "Docs/AI/agent-team.md", build_agent_team_doc(payload), force, bool(payload.get("replace_unmanaged"))),
        write_file_once(root, "Docs/AI/team-orchestration.md", build_orchestration_doc(payload), force, bool(payload.get("replace_unmanaged"))),
    ]
    for skill in team["skills"]:
        if skill["target_file"] == "Docs/AI/team-orchestration.md":
            continue
        results.append(write_file_once(root, skill["target_file"], build_skill_doc(payload, skill), force, bool(payload.get("replace_unmanaged"))))
    return results


def write_codex_skill_scaffolds(
    root: Path,
    payload: dict[str, Any],
    output_rel: str = "Docs/AI/codex-skills",
    force: bool = False,
) -> list[dict[str, str]]:
    results = []
    for skill in payload["team_factory"]["skills"]:
        skill_name = normalize_skill_name(str(skill["id"]))
        rel = str(Path(output_rel) / skill_name / "SKILL.md").replace("\\", "/")
        results.append(write_file_once(root, rel, build_codex_skill_md(payload, skill), force, bool(payload.get("replace_unmanaged"))))
    return results


def print_factory_plan(payload: dict[str, Any]) -> None:
    team = payload["team_factory"]
    engine = payload["harness_engine"]
    evidence = payload.get("repo_evidence", {})
    inventory = payload.get("artifact_inventory", {})
    quality = payload.get("factory_quality", {})
    print(f"Factory goal: {payload['factory_goal']}")
    print(f"Repo: {payload['repo']}")
    print(f"Domain: {payload['domain']}")
    print(f"Project type: {payload['project_type']}")
    print(f"Readiness: {engine['readiness']['score']}/{engine['readiness']['max_score']}")
    print(f"Human involvement: {engine['human_involvement']}/5")
    print(f"Repo evidence: {evidence.get('summary', 'No concrete evidence summary available.')}")
    print(
        "Factory quality: "
        f"evidence_refs={quality.get('evidence_ref_count', 0)}, "
        f"skills_with_evidence={quality.get('skills_with_evidence', 0)}, "
        f"conflicts={quality.get('conflict_count', 0)}, stale={quality.get('stale_count', 0)}, "
        f"closed_loop_signals={quality.get('closed_loop_signal_count', 0)}, "
        f"eval_scores={quality.get('eval_score_records', 0)}, pressure={quality.get('review_pressure', 'normal')}"
    )
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
        if skill.get("evidence_refs"):
            print(f"  Evidence: {', '.join(short_list([str(item) for item in skill['evidence_refs']], 4))}")
    if inventory.get("conflicts") or inventory.get("stale"):
        print("")
        print("Artifact update signals:")
        for item in inventory.get("conflicts", []):
            print(f"- conflict {item['id']}: {item['path']} ({item['update_path']})")
        for item in inventory.get("stale", []):
            print(f"- unmanaged {item['path']} ({item['update_path']})")


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
    parser.add_argument("--write-artifacts", action="store_true", help="Write Docs/AI/agent-team.md, Docs/AI/skills/*.md, and Docs/AI/team-orchestration.md.")
    parser.add_argument("--write-codex-skills", action="store_true", help="Write Codex SKILL.md draft folders under --codex-skill-output.")
    parser.add_argument("--codex-skill-output", default="Docs/AI/codex-skills", help="Repo-relative output directory for generated Codex skill drafts.")
    parser.add_argument("--install-codex-skills", action="store_true", help="Install generated Codex skill drafts into --skill-install-root or $CODEX_HOME/skills.")
    parser.add_argument("--skill-install-root", help="Destination skills directory. Defaults to $CODEX_HOME/skills or ~/.codex/skills.")
    parser.add_argument("--confirm-install", action="store_true", help="Required with --install-codex-skills.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing factory artifact files when writing.")
    parser.add_argument("--replace-unmanaged", action="store_true", help="Allow --force to replace existing files without the repo-harness-tuner generated marker.")
    parser.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo)
    payload = build_factory_plan(root, args.domain, args.phase, args.module, args.human_involvement, args.repo_type, args.team_size)
    payload["replace_unmanaged"] = args.replace_unmanaged
    if args.write_plan or args.write_artifacts or args.write_codex_skills or args.install_codex_skills:
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
    if args.install_codex_skills and not args.confirm_install:
        payload["install_blocked"] = {
            "blocked": True,
            "required_flag": "--confirm-install",
            "reason": "Installing generated skills writes outside the target repo and must be explicitly confirmed.",
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print_factory_plan(payload)
            print("")
            print("Install blocked: pass --confirm-install after reviewing the generated skill drafts.")
        return 2
    if args.write_plan:
        payload["plan_path"] = str(write_factory_plan(root.resolve(), payload))
    if args.write_artifacts:
        payload["artifact_results"] = write_factory_artifacts(root.resolve(), payload, args.force)
    if args.write_codex_skills:
        payload["codex_skill_results"] = write_codex_skill_scaffolds(root.resolve(), payload, args.codex_skill_output, args.force)
    if args.install_codex_skills:
        install_root = Path(args.skill_install_root) if args.skill_install_root else None
        payload["install_results"] = install_codex_skill_scaffolds(payload, install_root, args.force, args.replace_unmanaged)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print_factory_plan(payload)
        if args.write_plan:
            print("")
            print(f"Factory plan written: {payload['plan_path']}")
        if args.write_artifacts:
            print("")
            print("Factory artifacts:")
            for result in payload["artifact_results"]:
                print(f"- {result['status']}: {result['path']}")
        if args.write_codex_skills:
            print("")
            print("Codex skill drafts:")
            for result in payload["codex_skill_results"]:
                print(f"- {result['status']}: {result['path']}")
        if args.install_codex_skills:
            print("")
            print("Installed Codex skills:")
            for result in payload["install_results"]:
                print(f"- {result['status']}: {result['skill']} -> {result['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
