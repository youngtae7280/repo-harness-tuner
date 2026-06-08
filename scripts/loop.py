#!/usr/bin/env python3
"""One-command doctor and run-loop orchestration for Repo Harness Tuner."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


def configure_console_output() -> None:
    """Avoid UnicodeEncodeError on legacy Windows console encodings."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")


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
factory_module = load_local_module("factory")
evaluate_module = load_local_module("evaluate")
tune_module = load_local_module("tune")
history_module = load_local_module("history")
write_policy = load_local_module("write_policy")
bootstrap_module = load_local_module("bootstrap")
skill_recommender = load_local_module("skill_recommender")


def quote_cli(value: str | Path) -> str:
    text = str(value)
    if not text:
        return '""'
    if re.search(r"\s", text):
        return json.dumps(text, ensure_ascii=False)
    return text


def command_line(
    command: str,
    root: Path,
    phase: str,
    modules: list[str] | None = None,
    human_involvement: int | None = None,
    repo_type: str | None = None,
    extra: list[str] | None = None,
) -> str:
    parts = [
        "python",
        "scripts/console.py",
        command,
        "--repo",
        quote_cli(root.resolve()),
        "--phase",
        phase,
    ]
    if repo_type and repo_type != "unknown":
        parts.extend(["--repo-type", quote_cli(repo_type)])
    if human_involvement is not None:
        parts.extend(["--human-involvement", str(human_involvement)])
    for module in modules or []:
        parts.extend(["--module", quote_cli(module)])
    if extra:
        parts.extend(extra)
    return " ".join(parts)


def write_target_exists(root: Path, rel: str) -> bool:
    variants = {
        rel,
        rel.replace("Docs/AI", "docs/AI"),
        rel.replace("Docs/AI", "docs/ai"),
    }
    return any((root / variant).exists() for variant in variants)


SAFE_AUTO_APPLY_KINDS = {"bootstrap", "tune", "factory-artifacts", "skill-recommendations-plan"}
SAFE_AUTO_APPLY_FILES = {"AGENTS.md"}
SAFE_AUTO_APPLY_PREFIXES = ("Docs/AI/", "docs/AI/", "docs/ai/")
BLOCKED_AUTO_APPLY_FRAGMENTS = (
    ".github/",
    ".codex-plugin/",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "marketplace.json",
)


def normalize_rel_path(path: str) -> str:
    return str(path).replace("\\", "/").lstrip("./")


def safe_auto_apply_path(path: str) -> bool:
    rel = normalize_rel_path(path)
    lowered = rel.lower()
    if any(fragment.lower() in lowered for fragment in BLOCKED_AUTO_APPLY_FRAGMENTS):
        return False
    return rel in SAFE_AUTO_APPLY_FILES or any(rel.startswith(prefix) for prefix in SAFE_AUTO_APPLY_PREFIXES)


def auto_apply_guard(action: dict[str, Any], planned_items: list[dict[str, Any]]) -> dict[str, Any]:
    kind = str(action.get("write_kind") or "none")
    checked_paths = [normalize_rel_path(str(item.get("path", ""))) for item in planned_items if item.get("path")]
    unsafe_paths = [path for path in checked_paths if not safe_auto_apply_path(path)]
    unsafe_actions = [
        str(item.get("action") or item.get("status") or "")
        for item in planned_items
        if str(item.get("action") or item.get("status") or "") in {"delete", "remove", "install", "uninstall", "enable", "disable"}
    ]
    if kind not in SAFE_AUTO_APPLY_KINDS:
        return {
            "allowed": False,
            "reason": f"{kind} is not a low-risk managed harness write kind.",
            "checked_paths": checked_paths,
        }
    if unsafe_actions:
        return {
            "allowed": False,
            "reason": f"Unsafe action(s) are not eligible for automatic apply: {', '.join(sorted(set(unsafe_actions)))}.",
            "checked_paths": checked_paths,
        }
    if unsafe_paths:
        return {
            "allowed": False,
            "reason": "Recommended write touches paths outside managed harness docs or AGENTS.md.",
            "checked_paths": checked_paths,
            "unsafe_paths": unsafe_paths,
        }
    return {
        "allowed": True,
        "reason": "Recommended write is limited to managed harness docs or AGENTS.md.",
        "checked_paths": checked_paths,
    }


def closed_loop_evidence_note(history_feedback: dict[str, Any], next_action: dict[str, Any]) -> str:
    signals = history_feedback.get("signals", [])
    if not signals:
        return "No stored history or eval evidence changed the next action."
    if next_action.get("id") in {"tune", "eval-review"}:
        return "Stored history or eval evidence influenced the next action."
    return "Stored history or eval evidence was reported but did not override higher-priority harness gaps."


def choose_next_action(
    root: Path,
    phase: str,
    modules: list[str] | None,
    human_involvement: int | None,
    repo_type: str | None,
    domain: str,
    repo_scan: dict[str, Any],
    diagnosis: dict[str, Any],
    tune_payload: dict[str, Any],
    history_summary: dict[str, Any],
) -> dict[str, Any]:
    missing = list(repo_scan.get("missing_recommended", []))
    history_feedback = diagnosis.get("history_feedback", {})
    signal_types = {str(signal.get("type")) for signal in history_feedback.get("signals", []) if isinstance(signal, dict)}
    eval_repair_signals = {"eval-regression", "eval-unchanged-fail"} & signal_types
    if len(missing) >= 2:
        return {
            "id": "bootstrap",
            "label": "Bootstrap missing repo harness files",
            "reason": "multiple baseline harness files are missing",
            "command": command_line(
                "bootstrap",
                root,
                phase,
                modules,
                human_involvement,
                repo_type,
                ["--write"],
            ),
            "write_kind": "bootstrap",
        }
    if eval_repair_signals and tune_payload.get("proposals"):
        return {
            "id": "tune",
            "label": "Apply the proposed harness tuning diff",
            "reason": f"latest eval/history feedback raised {', '.join(sorted(eval_repair_signals))}",
            "command": command_line(
                "tune",
                root,
                phase,
                modules,
                human_involvement,
                repo_type,
                ["--dry-run", "--diff"],
            ),
            "write_kind": "tune",
        }
    if eval_repair_signals:
        return {
            "id": "eval-review",
            "label": "Review eval failures before changing generated teams or skills",
            "reason": f"latest eval/history feedback raised {', '.join(sorted(eval_repair_signals))}, but no safe managed diff was generated",
            "command": command_line("diagnose", root, phase, modules, human_involvement, repo_type),
            "write_kind": "none",
        }
    if tune_payload.get("proposals"):
        return {
            "id": "tune",
            "label": "Apply the proposed harness tuning diff",
            "reason": f"{len(tune_payload['proposals'])} tuning proposal(s) are available",
            "command": command_line(
                "tune",
                root,
                phase,
                modules,
                human_involvement,
                repo_type,
                ["--dry-run", "--diff"],
            ),
            "write_kind": "tune",
        }
    if not write_target_exists(root, "Docs/AI/agent-team.md"):
        return {
            "id": "factory-artifacts",
            "label": "Generate repo-local team and skill artifacts",
            "reason": "the harness is fit, but no repo-local agent team artifact exists yet",
            "command": command_line(
                "factory",
                root,
                phase,
                modules,
                human_involvement,
                repo_type,
                ["--domain", quote_cli(domain), "--write-artifacts"],
            ),
            "write_kind": "factory-artifacts",
        }
    if int(history_summary.get("count", 0) or 0) == 0:
        return {
            "id": "record-history",
            "label": "Record a baseline harness history snapshot",
            "reason": "the harness is fit enough, but no history baseline has been recorded",
            "command": command_line(
                "history",
                root,
                phase,
                modules,
                human_involvement,
                repo_type,
                ["--record", "--write", "--note", quote_cli("baseline from run-loop")],
            ),
            "write_kind": "history",
        }
    return {
        "id": "observe",
        "label": "Keep the harness stable and observe",
        "reason": diagnosis["harness_design"]["next_review_trigger"],
        "command": command_line("doctor", root, phase, modules, human_involvement, repo_type),
        "write_kind": "none",
    }


def build_loop_plan(
    root: Path,
    phase: str,
    domain: str = "current repository",
    modules: list[str] | None = None,
    human_involvement: int | None = None,
    repo_type: str | None = None,
    team_size: int = 3,
    skill_sources: str | None = "builtin,ecc",
    skill_limit: int = 3,
    catalog_root: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    repo_scan = scan_repo_harness.scan(root)
    diagnosis = diagnose_module.diagnose(root, repo_scan, phase, modules, human_involvement, repo_type)
    design = diagnosis["harness_design"]
    tune_payload = tune_module.build_proposals(root, phase, modules, human_involvement, repo_type)
    eval_payload = evaluate_module.build_eval_plan(root, phase, modules, human_involvement, repo_type)
    factory_payload = factory_module.build_factory_plan(root, domain, phase, modules, human_involvement, repo_type, team_size)
    skill_payload = skill_recommender.build_recommendation_plan(
        root,
        domain,
        phase,
        modules,
        human_involvement,
        repo_type,
        team_size,
        skill_sources,
        skill_limit,
        catalog_root,
    )
    history_summary = history_module.summarize(history_module.load_history(root))
    history_feedback = diagnosis.get("history_feedback", {})
    closed_loop = history_feedback.get("closed_loop", {})
    adaptive = diagnosis.get("adaptive", {})
    adaptive_cadence = adaptive.get("cadence", {}) if isinstance(adaptive, dict) else {}
    adaptive_involvement = adaptive.get("human_involvement", {}) if isinstance(adaptive, dict) else {}
    next_action = choose_next_action(
        root,
        phase,
        modules,
        human_involvement,
        repo_type,
        domain,
        repo_scan,
        diagnosis,
        tune_payload,
        history_summary,
    )
    if next_action.get("id") == "observe" and skill_payload["summary"].get("recommendation_count", 0):
        next_action = {
            "id": "skill-recommendations",
            "label": "Review minimal skill and external catalog recommendations",
            "reason": "the harness is stable enough to review optional skills without changing files or installing anything",
            "command": skill_recommender.recommendation_command(
                root,
                phase,
                domain,
                skill_payload["options"]["sources"],
                int(skill_payload["options"]["limit"]),
                catalog_root,
                ["--write-plan"],
            ),
            "write_kind": "skill-recommendations-plan",
        }
    status = "fit"
    if int(diagnosis["readiness"]["score"]) < 60:
        status = "needs-bootstrap"
    elif tune_payload.get("proposals"):
        status = "needs-tune"
    elif history_feedback.get("review_pressure") in {"high", "elevated"}:
        status = "needs-review"
    elif diagnosis.get("drift") or diagnosis.get("human_involvement_enforcement"):
        status = "needs-review"

    return {
        "schema": "repo-harness-tuner.loop.v1",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "repo": str(root),
        "phase": phase,
        "domain": domain,
        "options": {
            "modules": modules or [],
            "human_involvement": human_involvement,
            "repo_type": repo_type or "unknown",
            "team_size": team_size,
            "skill_sources": skill_payload["options"]["sources"],
            "skill_limit": skill_payload["options"]["limit"],
            "catalog_root": str(catalog_root.resolve()) if catalog_root else None,
        },
        "status": status,
        "summary": {
            "project_type": design["project_type"],
            "project_label": design["project_label"],
            "readiness": diagnosis["readiness"]["score"],
            "max_readiness": diagnosis["readiness"]["max_score"],
            "human_involvement": diagnosis["human_involvement"],
            "worker_pattern": design["worker_architecture"]["pattern"],
            "worker_label": design["worker_architecture"].get("label", design["worker_architecture"]["pattern"]),
            "tune_proposals": len(tune_payload.get("proposals", [])),
            "eval_tasks": len(eval_payload.get("golden_tasks", [])),
            "history_entries": int(history_summary.get("count", 0) or 0),
            "eval_score_records": int(history_feedback.get("eval_score_records", 0) or 0),
            "closed_loop_signals": int(closed_loop.get("signal_count", len(history_feedback.get("signals", []))) or 0),
            "review_pressure": history_feedback.get("review_pressure", "normal"),
            "closed_loop_evidence_note": closed_loop_evidence_note(history_feedback, next_action),
            "adaptive_cadence_severity": adaptive_cadence.get("severity", "normal"),
            "adaptive_human_involvement_direction": adaptive_involvement.get("direction", "keep"),
            "skill_recommendations": int(skill_payload["summary"].get("recommendation_count", 0) or 0),
            "external_skill_recommendations": int(skill_payload["summary"].get("external_recommendation_count", 0) or 0),
            "skill_curator_action": skill_payload["curator"].get("action", "baseline"),
            "next_action": next_action,
        },
        "analyze": {
            "project_markers": repo_scan.get("project_markers", []),
            "harness_files": repo_scan.get("files", []),
            "missing_recommended": repo_scan.get("missing_recommended", []),
        },
        "diagnose": {
            "readiness": diagnosis["readiness"],
            "drift": diagnosis.get("drift", []),
            "process_overhead": diagnosis.get("process_overhead", []),
            "human_involvement_enforcement": diagnosis.get("human_involvement_enforcement", []),
            "history_feedback": diagnosis.get("history_feedback", {}),
        },
        "closed_loop": {
            "review_pressure": history_feedback.get("review_pressure", "normal"),
            "signals": history_feedback.get("signals", []),
            "recommendations": history_feedback.get("recommendations", []),
            "eval_score_records": int(history_feedback.get("eval_score_records", 0) or 0),
            "uses_history": bool(closed_loop.get("uses_history")),
            "uses_eval_scores": bool(closed_loop.get("uses_eval_scores")),
            "used_for_next_action": next_action["id"] in {"tune", "eval-review"},
            "evidence_note": closed_loop_evidence_note(history_feedback, next_action),
        },
        "adaptive": adaptive,
        "design": {
            "target_files": design.get("target_files", []),
            "worker_architecture": design.get("worker_architecture", {}),
            "next_review_trigger": design.get("next_review_trigger", ""),
            "evaluation_steps": design.get("evaluation_steps", []),
        },
        "factory": {
            "label": factory_payload["team_factory"]["label"],
            "pattern": factory_payload["team_factory"]["architecture_pattern"],
            "roles": factory_payload["team_factory"]["roles"],
            "skills": factory_payload["team_factory"]["skills"],
            "planned_outputs": factory_payload["team_factory"]["planned_outputs"],
        },
        "skill_recommendations": skill_payload,
        "tune": {
            "proposals": tune_payload.get("proposals", []),
            "notes": tune_payload.get("notes", []),
        },
        "evaluate": {
            "mode": eval_payload.get("evaluation_mode", "plan-only"),
            "golden_tasks": eval_payload.get("golden_tasks", []),
            "runbook": eval_payload.get("runbook", []),
        },
        "history": history_summary,
        "commands": [
            command_line("doctor", root, phase, modules, human_involvement, repo_type, ["--domain", quote_cli(domain)]),
            command_line("run-loop", root, phase, modules, human_involvement, repo_type, ["--domain", quote_cli(domain)]),
            skill_recommender.recommendation_command(
                root,
                phase,
                domain,
                skill_payload["options"]["sources"],
                int(skill_payload["options"]["limit"]),
                catalog_root,
            ),
            next_action["command"],
        ],
    }


def write_loop_plan(root: Path, payload: dict[str, Any]) -> Path:
    docs_ai = root / "Docs" / "AI"
    docs_ai.mkdir(parents=True, exist_ok=True)
    path = docs_ai / "harness-loop-plan.md"
    summary = payload["summary"]
    next_action = summary["next_action"]
    lines = [
        "# Harness Loop Plan",
        "",
        f"Updated: {payload['created_at']}",
        f"Phase: {payload['phase']}",
        f"Domain: {payload['domain']}",
        f"Status: {payload['status']}",
        f"Project type: {summary['project_label']} (`{summary['project_type']}`)",
        f"Readiness: {summary['readiness']}/{summary['max_readiness']}",
        f"Human involvement: {summary['human_involvement']}/5",
        f"Worker pattern: {summary['worker_label']} (`{summary['worker_pattern']}`)",
        f"Review pressure: {summary['review_pressure']} ({summary['closed_loop_signals']} closed-loop signal(s), {summary['eval_score_records']} eval score record(s))",
        f"Closed-loop evidence: {summary['closed_loop_evidence_note']}",
        "",
        "## Adaptive Recommendations",
    ]
    adaptive = payload.get("adaptive", {})
    cadence = adaptive.get("cadence", {}) if isinstance(adaptive, dict) else {}
    involvement = adaptive.get("human_involvement", {}) if isinstance(adaptive, dict) else {}
    if cadence:
        lines.append(
            f"- Cadence: {cadence.get('severity', 'normal')} pressure, "
            f"`{cadence.get('recommended_interval', 'use phase default cadence')}`."
        )
    if involvement:
        lines.append(
            f"- Human involvement: {involvement.get('direction', 'keep')} "
            f"{involvement.get('current_default', summary['human_involvement'])}/5 -> "
            f"{involvement.get('recommended_default', summary['human_involvement'])}/5."
        )
        if involvement.get("approval_required"):
            lines.append("- Policy change requires explicit user approval; no silent apply.")
    lines.extend(
        [
            "",
            "## Next Action",
            f"- {next_action['label']}",
            f"- Reason: {next_action['reason']}",
            f"- Command: `{next_action['command']}`",
            "",
            "## Loop Summary",
            f"- Analyze: {len(payload['analyze']['harness_files'])} harness/support file(s), {len(payload['analyze']['missing_recommended'])} missing recommended file(s).",
            f"- Diagnose: {len(payload['diagnose']['drift'])} drift issue(s), {len(payload['diagnose']['human_involvement_enforcement'])} human-involvement gap(s).",
            f"- Design: {len(payload['design']['target_files'])} target action(s), next review `{payload['design']['next_review_trigger']}`.",
        f"- Factory: {payload['factory']['label']} with {len(payload['factory']['roles'])} role(s) and {len(payload['factory']['skills'])} planned skill(s).",
        f"- Skill recommendations: {summary['skill_recommendations']} candidate(s), {summary['external_skill_recommendations']} external, curator `{summary['skill_curator_action']}`.",
        f"- Tune: {len(payload['tune']['proposals'])} proposal(s).",
            f"- Evaluate: {len(payload['evaluate']['golden_tasks'])} golden task(s).",
            f"- History: {summary['history_entries']} recorded event(s).",
            f"- Closed loop: {summary['closed_loop_signals']} signal(s), review pressure `{summary['review_pressure']}`.",
            f"- Adaptive: cadence `{summary['adaptive_cadence_severity']}`, human involvement `{summary['adaptive_human_involvement_direction']}`.",
            f"- Evidence note: {summary['closed_loop_evidence_note']}",
            "",
            "## Target Files",
        ]
    )
    for item in payload["design"]["target_files"]:
        lines.append(f"- {item['action']}: `{item['path']}` - {item['reason']}")
    lines.extend(["", "## Factory Roles"])
    for role in payload["factory"]["roles"]:
        lines.append(f"- `{role['id']}`: {role['purpose']}")
    lines.extend(["", "## Skill Recommendations"])
    skill_payload = payload.get("skill_recommendations", {})
    if skill_payload.get("recommendations"):
        for item in skill_payload["recommendations"]:
            lines.append(
                f"- `{item['id']}` ({item['source']}): {item['capability_label']} via `{item['name']}` - {item['reason']}"
            )
    else:
        lines.append("- No additional skill or external catalog recommendation is needed right now.")
    if skill_payload.get("curator"):
        curator = skill_payload["curator"]
        lines.append(f"- Curator: `{curator.get('action', 'baseline')}` - {curator.get('reason', '')}")
    lines.append("- Install boundary: adapter-only installs require explicit `--install --confirm-install`; no external hooks, MCP servers, slash commands, or agents are installed.")
    lines.extend(["", "## Evaluation Tasks"])
    for task in payload["evaluate"]["golden_tasks"]:
        lines.append(f"- `{task['id']}`: {task['purpose']}")
    lines.extend(["", "## Commands"])
    for command in payload["commands"]:
        lines.append(f"- `{command}`")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def apply_recommended(payload: dict[str, Any], root: Path, force: bool = False) -> dict[str, Any]:
    action = payload["summary"]["next_action"]
    kind = action.get("write_kind")
    options = payload.get("options", {})
    modules = list(options.get("modules", [])) or None
    human_involvement = options.get("human_involvement")
    repo_type = options.get("repo_type") or "unknown"
    team_size = int(options.get("team_size") or 3)
    if kind == "bootstrap":
        plan = bootstrap_module.plan_bootstrap(root, payload["phase"], human_involvement, repo_type, modules, force)
        guard = auto_apply_guard(action, list(plan.get("actions", [])))
        if not guard["allowed"]:
            return {"action": action, "results": [], "auto_apply_guard": guard, "blocked": True}
        return {"action": action, "results": bootstrap_module.apply_bootstrap(plan, root), "auto_apply_guard": guard}
    if kind == "tune":
        tune_payload = tune_module.build_proposals(root, payload["phase"], modules, human_involvement, repo_type, force)
        guard = auto_apply_guard(action, list(tune_payload.get("proposals", [])))
        if not guard["allowed"]:
            return {"action": action, "results": [], "auto_apply_guard": guard, "blocked": True}
        return {"action": action, "results": tune_module.apply_proposals(tune_payload, root, force), "auto_apply_guard": guard}
    if kind == "factory-artifacts":
        factory_payload = factory_module.build_factory_plan(
            root,
            payload["domain"],
            payload["phase"],
            modules,
            human_involvement,
            repo_type,
            team_size,
        )
        planned = [
            {"path": "Docs/AI/agent-team.md", "action": "create"},
            {"path": "Docs/AI/team-orchestration.md", "action": "create"},
        ]
        planned.extend({"path": skill["target_file"], "action": "create"} for skill in factory_payload["team_factory"]["skills"])
        guard = auto_apply_guard(action, planned)
        if not guard["allowed"]:
            return {"action": action, "results": [], "auto_apply_guard": guard, "blocked": True}
        return {"action": action, "results": factory_module.write_factory_artifacts(root, factory_payload, force), "auto_apply_guard": guard}
    if kind == "skill-recommendations-plan":
        planned = [{"path": "Docs/AI/skill-recommendations.md", "action": "create"}]
        guard = auto_apply_guard(action, planned)
        if not guard["allowed"]:
            return {"action": action, "results": [], "auto_apply_guard": guard, "blocked": True}
        path = skill_recommender.write_recommendation_plan(root, payload["skill_recommendations"])
        return {
            "action": action,
            "results": [{"status": "create", "path": str(path.relative_to(root))}],
            "auto_apply_guard": guard,
        }
    return {"action": action, "results": [], "note": "No file changes were recommended for this action."}


def record_history(payload: dict[str, Any], root: Path, note: str = "") -> dict[str, Any]:
    options = payload.get("options", {})
    modules = list(options.get("modules", [])) or None
    event = history_module.build_event(
        root,
        payload["phase"],
        options.get("human_involvement"),
        options.get("repo_type") or "unknown",
        modules,
        note or "run-loop snapshot",
        "run-loop-snapshot",
    )
    path = history_module.append_event(root, event)
    return {"event": event, "path": str(path)}


def print_doctor(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    next_action = summary["next_action"]
    print("Repo Harness Doctor")
    print(f"Repo: {payload['repo']}")
    print(f"Project: {summary['project_label']} ({summary['project_type']})")
    print(f"Status: {payload['status']}")
    print(f"Readiness: {summary['readiness']}/{summary['max_readiness']}")
    print(f"Human involvement: {summary['human_involvement']}/5")
    print(f"Worker pattern: {summary['worker_label']} ({summary['worker_pattern']})")
    print("")
    print("Loop:")
    print(f"- Analyze: {len(payload['analyze']['harness_files'])} harness/support file(s)")
    print(f"- Diagnose: {len(payload['diagnose']['drift'])} drift issue(s), {len(payload['diagnose']['human_involvement_enforcement'])} human-involvement gap(s)")
    print(f"- Design: {len(payload['design']['target_files'])} target action(s)")
    print(f"- Factory: {payload['factory']['label']} ({len(payload['factory']['roles'])} role(s))")
    print(f"- Tune: {summary['tune_proposals']} proposal(s)")
    print(f"- Evaluate: {summary['eval_tasks']} golden task(s)")
    print(f"- History: {summary['history_entries']} event(s)")
    print(f"- Closed loop: {summary['closed_loop_signals']} signal(s), {summary['eval_score_records']} eval score record(s), pressure={summary['review_pressure']}")
    print(f"- Evidence note: {summary['closed_loop_evidence_note']}")
    print(
        f"- Skills: {summary['skill_recommendations']} recommendation(s), "
        f"{summary['external_skill_recommendations']} external, curator={summary['skill_curator_action']}"
    )
    adaptive = payload.get("adaptive", {})
    cadence = adaptive.get("cadence", {}) if isinstance(adaptive, dict) else {}
    involvement = adaptive.get("human_involvement", {}) if isinstance(adaptive, dict) else {}
    print("")
    print("Adaptive:")
    if cadence:
        print(
            f"- Cadence: {cadence.get('severity', 'normal')} pressure, "
            f"{cadence.get('recommended_interval', 'use phase default cadence')}"
        )
    if involvement:
        print(
            f"- Human involvement: {involvement.get('direction', 'keep')} "
            f"{involvement.get('current_default', summary['human_involvement'])}/5 -> "
            f"{involvement.get('recommended_default', summary['human_involvement'])}/5"
        )
        if involvement.get("approval_required"):
            print("- Approval required before changing human-involvement policy.")
    skill_payload = payload.get("skill_recommendations", {})
    print("")
    print("Skill Recommendations:")
    if skill_payload.get("recommendations"):
        for item in skill_payload["recommendations"]:
            print(f"- {item['id']}: {item['capability_label']} via {item['name']} [{item['source']}]")
        print("- Install boundary: adapter-only, explicit --install --confirm-install required.")
    else:
        print("- None needed right now.")
    print("")
    if payload["status"] == "fit":
        print("Optional next action:")
        print("- Required: none. Current harness appears fit.")
    else:
        print("Required next action:")
    print(f"- {next_action['label']}")
    print(f"- Reason: {next_action['reason']}")
    print(f"- Command: {next_action['command']}")


def main() -> int:
    configure_console_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    parser.add_argument("--domain", default="current repository")
    parser.add_argument("--module", action="append")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--repo-type", default="unknown")
    parser.add_argument("--team-size", type=int, default=3)
    parser.add_argument("--skill-source", default="builtin,ecc", help="Comma-separated skill recommendation sources: builtin,ecc,all.")
    parser.add_argument("--skill-limit", type=int, default=3, help="Maximum skill recommendations to show, capped at 3.")
    parser.add_argument("--catalog-root", help="Optional local checkout for an external catalog such as ECC.")
    parser.add_argument("--write-plan", action="store_true", help="Write Docs/AI/harness-loop-plan.md.")
    parser.add_argument("--write-recommended", action="store_true", help="Apply the next recommended file-writing action.")
    parser.add_argument("--record-history", action="store_true", help="Append a run-loop snapshot to Docs/AI/harness-history.jsonl.")
    parser.add_argument("--note", default="")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo)
    catalog_root = Path(args.catalog_root) if args.catalog_root else None
    payload = build_loop_plan(
        root,
        args.phase,
        args.domain,
        args.module,
        args.human_involvement,
        args.repo_type,
        args.team_size,
        args.skill_source,
        args.skill_limit,
        catalog_root,
    )
    if args.write_plan or args.write_recommended or args.record_history:
        guard = write_policy.write_guard("run-loop", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            payload["write_blocked"] = guard
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=True))
            else:
                print_doctor(payload)
                print("")
                print(write_policy.format_guard(guard))
            return 2
    if args.write_plan:
        payload["loop_plan_path"] = str(write_loop_plan(root.resolve(), payload))
    if args.write_recommended:
        payload["recommended_write"] = apply_recommended(payload, root.resolve(), args.force)
    if args.record_history:
        payload["history_record"] = record_history(payload, root.resolve(), args.note)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print_doctor(payload)
        if args.write_plan:
            print("")
            print(f"Loop plan written: {payload['loop_plan_path']}")
        if args.write_recommended:
            print("")
            print("Recommended write:")
            guard = payload["recommended_write"].get("auto_apply_guard", {})
            if payload["recommended_write"].get("blocked"):
                print(f"- blocked: {guard.get('reason', 'auto-apply guard blocked the write')}")
            for result in payload["recommended_write"]["results"]:
                print(f"- {result['status']}: {result['path']}")
            if not payload["recommended_write"]["results"]:
                print(f"- {payload['recommended_write'].get('note', guard.get('reason', 'No changes.'))}")
        if args.record_history:
            print("")
            print(f"History written: {payload['history_record']['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
