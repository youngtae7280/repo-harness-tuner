#!/usr/bin/env python3
"""Diagnose repo-local Codex harness readiness."""
from __future__ import annotations

import argparse
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


worker_patterns = load_local_module("worker_patterns")
history_store = load_local_module("history_store")
write_policy = load_local_module("write_policy")


PHASES = {
    "new-project": {
        "cadence": "Run an initial setup now, review again after the first working feature, then every 3-5 meaningful cycles until patterns stabilize.",
        "default_ambiguity": 3,
    },
    "prototype": {
        "cadence": "Review after each prototype slice that changes structure, validation, or product direction; otherwise every 3-5 cycles.",
        "default_ambiguity": 4,
    },
    "active-development": {
        "cadence": "Run a lightweight fit check every task, a short harness review every 3-5 meaningful cycles, and a full review after missed regressions.",
        "default_ambiguity": 3,
    },
    "pre-release": {
        "cadence": "Review before each release candidate, after QA failures, and whenever validation or release steps change.",
        "default_ambiguity": 2,
    },
    "maintenance": {
        "cadence": "Review monthly, after recurring agent mistakes, or before high-risk changes.",
        "default_ambiguity": 3,
    },
    "high-risk": {
        "cadence": "Review before planning, before implementation, and after validation; keep explicit human approval points.",
        "default_ambiguity": 1,
    },
}


PROJECT_PRESETS = {
    "unity": {
        "label": "Unity project",
        "primary_risks": [
            "scene, prefab, asset, and serialized data changes",
            "editor/build validation drift",
            "user-visible gameplay and UI direction",
        ],
        "validation_emphasis": [
            "prefer focused project scripts when present",
            "record when Unity Editor validation is unavailable",
            "treat asset/meta churn as review evidence",
        ],
        "baseline_files": ["AGENTS.md", "Docs/AI/harness-profile.md", "Docs/AI/validation.md"],
    },
    "godot": {
        "label": "Godot project",
        "primary_risks": [
            "scene/resource churn",
            "script/runtime validation gaps",
            "gameplay or UI direction changes",
        ],
        "validation_emphasis": [
            "prefer headless checks when configured",
            "record manual/editor validation gaps",
        ],
        "baseline_files": ["AGENTS.md", "Docs/AI/harness-profile.md", "Docs/AI/validation.md"],
    },
    "vite-node": {
        "label": "Vite/Node project",
        "primary_risks": [
            "build/typecheck drift",
            "frontend interaction regressions",
            "test selection becoming too broad or too narrow",
        ],
        "validation_emphasis": [
            "map npm scripts to focused and broad validation",
            "use browser evidence for meaningful UI changes",
        ],
        "baseline_files": ["AGENTS.md", "Docs/AI/harness-profile.md", "Docs/AI/validation.md"],
    },
    "node": {
        "label": "Node project",
        "primary_risks": [
            "script drift",
            "test/build selection",
            "shared contract changes",
        ],
        "validation_emphasis": [
            "map package scripts to when-to-run guidance",
            "keep broad validation reserved for shared or release-facing changes",
        ],
        "baseline_files": ["AGENTS.md", "Docs/AI/harness-profile.md", "Docs/AI/validation.md"],
    },
    "python": {
        "label": "Python project",
        "primary_risks": [
            "test/lint/type command drift",
            "environment assumptions",
            "data or migration safety when present",
        ],
        "validation_emphasis": [
            "document venv or bundled runtime assumptions",
            "separate fast focused checks from broad suites",
        ],
        "baseline_files": ["AGENTS.md", "Docs/AI/harness-profile.md", "Docs/AI/validation.md"],
    },
    "codex-plugin": {
        "label": "Codex plugin project",
        "primary_risks": [
            "plugin manifest and marketplace metadata drift",
            "skill frontmatter or trigger wording becoming invalid",
            "CLI smoke coverage missing generated factory and install flows",
        ],
        "validation_emphasis": [
            "validate plugin.json with plugin-creator",
            "validate bundled skills with skill-creator",
            "compile scripts and run focused CLI smoke tests before cachebuster updates",
        ],
        "baseline_files": ["AGENTS.md", "Docs/AI/harness-profile.md", "Docs/AI/validation.md"],
    },
    "docs-only": {
        "label": "Docs-only project",
        "primary_risks": [
            "unnecessary engineering process",
            "source-of-truth drift",
            "review overhead for small edits",
        ],
        "validation_emphasis": [
            "prefer source/link review over code-style gates",
            "avoid persistent reports unless decisions must be reused",
        ],
        "baseline_files": ["AGENTS.md", "Docs/AI/harness-profile.md"],
    },
    "unknown": {
        "label": "Unknown project",
        "primary_risks": [
            "missing project-specific validation",
            "over-general agent instructions",
            "unclear ask/decide boundaries",
        ],
        "validation_emphasis": [
            "inspect README and native scripts before adding rules",
            "keep setup minimal until project shape is clearer",
        ],
        "baseline_files": ["AGENTS.md", "Docs/AI/harness-profile.md", "Docs/AI/validation.md"],
    },
}


HUMAN_INVOLVEMENT_POLICY = {
    1: "Explore autonomously unless a protected area or explicit approval trigger appears.",
    2: "Proceed from existing patterns and mention assumptions in closeout.",
    3: "Infer from repo context, but ask before hard-to-reverse or user-visible direction changes.",
    4: "Ask 1-3 focused questions before edits unless a named repo source of truth already answers them.",
    5: "Stop and ask for explicit approval before edits.",
}


def ambiguity_from_human_involvement(value: int | None, phase: str) -> int:
    if value is None:
        return int(PHASES[phase]["default_ambiguity"])
    return max(1, min(5, 6 - value))


def human_involvement_from_ambiguity(value: int) -> int:
    return max(1, min(5, 6 - value))


def normalize_project_type(repo_scan: dict[str, Any], repo_type: str | None = None) -> str:
    value = (repo_type or "").strip().lower()
    if value and value != "unknown":
        if "codex" in value and ("plugin" in value or "skill" in value):
            return "codex-plugin"
        for key in PROJECT_PRESETS:
            if key != "unknown" and key in value:
                return key
        if "vite" in value:
            return "vite-node"
        if "unity" in value:
            return "unity"
        if "godot" in value:
            return "godot"
        if "python" in value:
            return "python"
        if "node" in value or "javascript" in value or "typescript" in value:
            return "node"
        if "docs" in value or "documentation" in value:
            return "docs-only"
        return value
    detected = str(repo_scan.get("project_type") or "unknown").lower()
    return detected if detected in PROJECT_PRESETS else "unknown"


def project_preset(repo_scan: dict[str, Any], repo_type: str | None = None) -> dict[str, Any]:
    key = normalize_project_type(repo_scan, repo_type)
    preset = dict(PROJECT_PRESETS.get(key, PROJECT_PRESETS["unknown"]))
    preset["key"] = key
    preset["markers"] = list(repo_scan.get("project_markers", []))
    return preset


def involvement_text(value: int) -> str:
    return HUMAN_INVOLVEMENT_POLICY[max(1, min(5, value))]


SCRIPT_HINTS = {
    "validate": "Docs/AI/validation.md should mention content or focused validation.",
    "test": "Docs/AI/validation.md should mention test selection.",
    "build": "Docs/AI/validation.md should mention build/type validation.",
    "lint": "Docs/AI/validation.md should mention lint/static checks.",
    "typecheck": "Docs/AI/validation.md should mention type validation.",
    "qa": "Docs/AI/validation.md should describe broad pre-merge or closeout validation.",
    "check": "Docs/AI/validation.md should mention focused project checks.",
}


OVERBROAD_RULES = [
    (
        re.compile(r"\balways\s+run\s+(?:all|the full|the entire|the complete)\s+(?:test\s+)?suite\b", re.IGNORECASE),
        "Overbroad validation rule",
    ),
    (
        re.compile(r"\balways\s+(?:create|write|produce)\s+(?:a\s+)?(?:full|detailed|complete)\s+report\b", re.IGNORECASE),
        "Overbroad report rule",
    ),
    (
        re.compile(r"\balways\s+(?:create|write)\s+(?:a\s+)?(?:detailed|full|long\s+)?plan\b", re.IGNORECASE),
        "Overbroad planning rule",
    ),
    (
        re.compile(r"\balways\s+(?:use|spawn|create)\s+(?:visible\s+)?(?:chats?|workers?|subagents?)\b", re.IGNORECASE),
        "Overbroad worker rule",
    ),
    (
        re.compile(r"\b(?:every|all)\s+(?:task|change|edit)s?.{0,60}\b(?:full\s+QA|full\s+validation|persistent\s+report)\b", re.IGNORECASE),
        "Every-task process rule",
    ),
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def find_file(root: Path, candidates: list[str]) -> Path | None:
    for rel in candidates:
        path = root / rel
        if path.exists():
            return path
    return None


def has_file(repo_scan: dict[str, Any], suffix: str) -> bool:
    normalized = suffix.replace("/", "\\").lower()
    for item in repo_scan.get("files", []):
        path = str(item.get("path", "")).replace("/", "\\").lower()
        if path == normalized:
            return True
    return False


def score_repo(root: Path, repo_scan: dict[str, Any], phase: str) -> dict[str, Any]:
    score = 0
    max_score = 100
    findings: list[dict[str, str]] = []
    recommendations: list[str] = []

    def add(points: int, ok: bool, title: str, pass_detail: str, gap_detail: str | None = None, recommendation: str | None = None) -> None:
        nonlocal score
        if ok:
            score += points
            findings.append({"status": "pass", "title": title, "detail": pass_detail})
        else:
            findings.append({"status": "gap", "title": title, "detail": gap_detail or pass_detail})
            if recommendation:
                recommendations.append(recommendation)

    add(
        15,
        has_file(repo_scan, "AGENTS.md"),
        "Entry point",
        "AGENTS.md is present.",
        "AGENTS.md is missing.",
        "Add a short AGENTS.md as the repo-local Codex entry point.",
    )
    add(
        15,
        has_file(repo_scan, "Docs/AI/harness-profile.md") or has_file(repo_scan, "docs/ai/harness-profile.md"),
        "Harness profile",
        "Harness profile is present.",
        "Harness profile is missing.",
        "Add Docs/AI/harness-profile.md with cycle sizing, always-on harnesses, usually-skipped harnesses, and review cadence.",
    )
    add(
        15,
        has_file(repo_scan, "Docs/AI/validation.md") or has_file(repo_scan, "docs/ai/validation.md"),
        "Validation guide",
        "Validation guide is present.",
        "Validation guide is missing.",
        "Add Docs/AI/validation.md with focused and broad validation commands.",
    )

    profile_path = find_file(root, ["Docs/AI/harness-profile.md", "docs/AI/harness-profile.md", "docs/ai/harness-profile.md"])
    profile_text = read_text(profile_path) if profile_path else ""
    add(
        10,
        bool(re.search(r"ambiguity|ask|question|clarif", profile_text, re.IGNORECASE)),
        "Human involvement policy",
        "Harness profile mentions human-involvement, ask, or question policy.",
        "Harness profile does not mention human-involvement, ask, or question policy.",
        "Add module/risk human-involvement rules so agents know when to ask and when to infer.",
    )
    add(
        10,
        bool(re.search(r"visible|background|subagent|worker|chat", profile_text, re.IGNORECASE)),
        "Worker visibility",
        "Harness profile mentions worker/subagent visibility.",
        "Harness profile does not mention worker/subagent visibility.",
        "Add visible-chat vs background-worker policy for parallel work.",
    )

    validation_path = find_file(root, ["Docs/AI/validation.md", "docs/AI/validation.md", "docs/ai/validation.md"])
    validation_text = read_text(validation_path) if validation_path else ""
    package_scripts = repo_scan.get("package_scripts", {})
    if package_scripts:
        covered = any(name in validation_text for name in package_scripts)
        add(
            15,
            covered,
            "Script coverage",
            "Validation guide references package scripts.",
            "Validation guide does not reference detected package scripts.",
            "Update Docs/AI/validation.md to reference current package scripts and when to run each one.",
        )
    else:
        add(5, True, "Script coverage", "No package scripts detected; use project-specific validation when available.")

    agents_path = root / "AGENTS.md"
    agents_lines = len(read_text(agents_path).splitlines()) if agents_path.exists() else 0
    add(
        10,
        agents_lines == 0 or agents_lines <= 120,
        "Overhead risk",
        f"AGENTS.md line count is {agents_lines}.",
        f"AGENTS.md line count is {agents_lines}, which may be too long.",
        "Shorten AGENTS.md and move details to Docs/AI/* if it is becoming a manual.",
    )

    docs_reports_count = int(repo_scan.get("docs_reports_count", 0) or 0)
    if docs_reports_count >= 20:
        add(
            10,
            bool(re.search(r"report|Reports|persistent", profile_text, re.IGNORECASE)),
            "Report policy",
            f"Docs/Reports has {docs_reports_count} entries.",
            f"Docs/Reports has {docs_reports_count} entries but no clear report persistence policy was found.",
            "Add a report persistence policy so small tasks do not create unnecessary durable reports.",
        )
    else:
        add(10, True, "Report policy", f"Docs/Reports has {docs_reports_count} entries.")

    if phase == "new-project" and score > 80:
        recommendations.append("Keep the initial harness light; avoid security/release/data-safety docs until real risk appears.")

    return {
        "score": min(score, max_score),
        "max_score": max_score,
        "findings": findings,
        "recommendations": dedupe(recommendations),
    }


def dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def drift_check(root: Path, repo_scan: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    validation_path = find_file(root, ["Docs/AI/validation.md", "docs/AI/validation.md", "docs/ai/validation.md"])
    validation_text = read_text(validation_path) if validation_path else ""
    scripts = repo_scan.get("package_scripts", {})
    for name, command in scripts.items():
        lowered = f"{name} {command}".lower()
        relevant = any(hint in lowered for hint in SCRIPT_HINTS)
        if relevant and name not in validation_text and command not in validation_text:
            issues.append(
                {
                    "type": "validation-script-drift",
                    "item": name,
                    "detail": f"package.json script `{name}` is not referenced in Docs/AI/validation.md.",
                }
            )

    skills_doc = find_file(root, ["Docs/SKILLS.md", "docs/SKILLS.md", "docs/skills.md"])
    skills_text = read_text(skills_doc) if skills_doc else ""
    if skills_doc and "codex-harness-setup" not in skills_text and (root / "AGENTS.md").exists():
        issues.append(
            {
                "type": "skills-doc-drift",
                "item": "codex-harness-setup",
                "detail": "Repo has Codex harness files but Docs/SKILLS.md does not mention codex-harness-setup.",
            }
        )
    return issues


def overbroad_process_check(root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    candidates: list[Path] = []
    agents = root / "AGENTS.md"
    if agents.exists():
        candidates.append(agents)
    for docs_root in [root / "Docs" / "AI", root / "docs" / "AI", root / "docs" / "ai"]:
        if docs_root.exists():
            candidates.extend(sorted(path for path in docs_root.rglob("*.md") if path.is_file()))

    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        text = read_text(path)
        for pattern, title in OVERBROAD_RULES:
            for match in pattern.finditer(text):
                line = text[: match.start()].count("\n") + 1
                issues.append(
                    {
                        "type": "overbroad-process",
                        "item": f"{path.relative_to(root)}:{line}",
                        "detail": f"{title}: {match.group(0)}",
                    }
                )
    return issues


def ambiguity_enforcement_check(root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    ambiguity_path = find_file(root, ["Docs/AI/ambiguity-profile.md", "docs/AI/ambiguity-profile.md", "docs/ai/ambiguity-profile.md"])
    agents_text = read_text(root / "AGENTS.md")
    profile_text = read_text(find_file(root, ["Docs/AI/harness-profile.md", "docs/AI/harness-profile.md", "docs/ai/harness-profile.md"]) or Path("__missing__"))

    if not ambiguity_path:
        issues.append(
            {
                "type": "ambiguity-profile-missing",
                "item": "Docs/AI/ambiguity-profile.md",
                "detail": "No dedicated human-involvement/ask-before profile found; agents may not know when to ask vs infer.",
            }
        )
        return issues

    text = read_text(ambiguity_path)
    checks = [
        (
            "ask-before-column",
            bool(re.search(r"ask\s+before|must\s+ask|before\s+edits?", text, re.IGNORECASE)),
            "Ambiguity profile should define concrete ask-before triggers.",
        ),
        (
            "decide-column",
            bool(re.search(r"agent\s+may\s+decide|may\s+decide|safe\s+to\s+decide|proceed", text, re.IGNORECASE)),
            "Ambiguity profile should define what the agent may decide without asking.",
        ),
        (
            "level-scale",
            all(str(level) in text for level in range(1, 6)),
            "Ambiguity profile should include levels 1-5 or equivalent behavior levels.",
        ),
        (
            "approval-trigger",
            bool(re.search(r"explicit\s+approval|approval|required|ask\s+before", text, re.IGNORECASE)),
            "Ambiguity profile should mark approval/ask triggers for high-risk areas.",
        ),
    ]
    for item, ok, detail in checks:
        if not ok:
            issues.append({"type": "ambiguity-enforcement-gap", "item": item, "detail": detail})

    combined = agents_text + "\n" + profile_text
    if "ambiguity-profile.md" not in combined:
        issues.append(
            {
                "type": "ambiguity-link-missing",
                "item": "AGENTS.md or harness-profile.md",
                "detail": "Repo entrypoint should link to Docs/AI/ambiguity-profile.md so agents use it before deciding whether to ask.",
            }
        )
    if not re.search(r"ask\s+before|stop\s+and\s+ask|before\s+editing|before\s+edits?", combined, re.IGNORECASE):
        issues.append(
            {
                "type": "ambiguity-action-gap",
                "item": "AGENTS.md or harness-profile.md",
                "detail": "Repo entrypoint should state that ask-before triggers require stopping to ask before edits.",
            }
        )
    return issues


def ambiguity_matrix(phase: str, modules: list[str] | None = None, human_involvement: int | None = None) -> list[dict[str, str | int]]:
    default = ambiguity_from_human_involvement(human_involvement, phase)
    rows: list[dict[str, str | int]] = [
        {
            "area": "Small docs/copy edits",
            "ambiguity": min(5, default + 1),
            "human_involvement": human_involvement_from_ambiguity(min(5, default + 1)),
            "visibility": "single-agent",
            "validation": "docs review or skipped with reason",
        },
        {
            "area": "Core behavior or shared contracts",
            "ambiguity": max(2, default),
            "human_involvement": human_involvement_from_ambiguity(max(2, default)),
            "visibility": "single-agent or background review",
            "validation": "focused regression plus broad check when shared",
        },
        {
            "area": "Product, roadmap, UX, or narrative direction",
            "ambiguity": max(1, default - 1),
            "human_involvement": human_involvement_from_ambiguity(max(1, default - 1)),
            "visibility": "visible chat",
            "validation": "decision record or concise report",
        },
        {
            "area": "Dependencies, release, data, secrets, or destructive operations",
            "ambiguity": 1,
            "human_involvement": 5,
            "visibility": "visible chat + approval",
            "validation": "explicit approval and rollback evidence",
        },
        {
            "area": "Static review, test review, security review",
            "ambiguity": max(2, default),
            "human_involvement": human_involvement_from_ambiguity(max(2, default)),
            "visibility": "background/read-only",
            "validation": "findings summary with file references",
        },
    ]
    for module in modules or []:
        if ":" in module:
            area, involvement = module.split(":", 1)
            human_value = max(1, min(5, int(re.sub(r"\D", "", involvement) or human_involvement_from_ambiguity(default))))
            ambiguity_value = 6 - human_value
        else:
            area = module
            ambiguity_value = default
            human_value = human_involvement_from_ambiguity(default)
        rows.append(
            {
                "area": area.strip(),
                "ambiguity": max(1, min(5, ambiguity_value)),
                "human_involvement": human_value,
                "visibility": "module override",
                "validation": "use repo-specific focused validation",
            }
        )
    return rows


def human_involvement_matrix(phase: str, modules: list[str] | None = None, human_involvement: int | None = None) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for row in ambiguity_matrix(phase, modules, human_involvement):
        involvement = int(row["human_involvement"])
        rows.append(
            {
                "area": row["area"],
                "human_involvement": involvement,
                "policy": involvement_text(involvement),
                "visibility": row["visibility"],
                "validation": row["validation"],
            }
        )
    return rows


def quote_path(path: Path) -> str:
    return f'"{path}"'


def build_evaluation_steps(root: Path, repo_scan: dict[str, Any], phase: str) -> list[dict[str, str]]:
    plugin_root = Path(__file__).resolve().parent.parent
    check_harness = plugin_root / "skills" / "codex-harness-setup" / "scripts" / "check_harness.py"
    steps = [
        {
            "when": "after AGENTS.md or Docs/AI/* changes",
            "command": f"python {quote_path(check_harness)} {quote_path(root.resolve())}",
        },
        {
            "when": "after diagnosis or design changes",
            "command": f"python {quote_path(plugin_root / 'scripts' / 'console.py')} diagnose --repo {quote_path(root.resolve())} --phase {phase}",
        },
    ]
    scripts = repo_scan.get("package_scripts", {})
    if isinstance(scripts, dict) and scripts:
        focused: list[str] = []
        preferred = ["validate", "check"]
        preferred.extend(sorted(name for name in scripts if name.startswith("check:")))
        preferred.extend(["lint", "typecheck", "test", "build", "qa"])
        for name in preferred:
            if name in scripts:
                focused.append(name)
        if focused:
            steps.append(
                {
                    "when": "after project behavior or validation-guide changes",
                    "command": " or ".join(f"npm run {name}" for name in focused),
                }
            )
        else:
            steps.append(
                {
                    "when": "when project behavior changes",
                    "command": "select the nearest package.json script and record why it was chosen",
                }
            )
    else:
        steps.append(
            {
                "when": "when no native validation command is detected",
                "command": "record manual or unavailable validation explicitly",
            }
        )
    return steps


def worker_architecture(
    phase: str,
    human_involvement: int,
    readiness_score: int,
    needs_restructure: bool,
    drift_count: int,
    overhead_count: int,
    enforcement_count: int,
    project_type: str,
) -> dict[str, object]:
    selected = worker_patterns.select_pattern(
        phase=phase,
        human_involvement=human_involvement,
        readiness_score=readiness_score,
        needs_restructure=needs_restructure,
        drift_count=drift_count,
        overhead_count=overhead_count,
        enforcement_count=enforcement_count,
        project_type=project_type,
    )
    return {
        "pattern": selected["id"],
        "label": selected["label"],
        "summary": selected["summary"],
        "default_visibility": selected["visibility"],
        "coordination": selected["coordination"],
        "selection_reasons": selected["selection_reasons"],
        "use_when": selected["use_when"],
        "evidence": selected["evidence"],
        "avoid": selected["avoid_when"],
        "fallback_patterns": selected["fallback_patterns"],
        "visible_chats": [
            "human approval points",
            "product, roadmap, UI, narrative, or release-direction decisions",
            "QA evidence the user must inspect",
        ],
        "background_workers": [
            "read-only harness audit",
            "test or validation review",
            "security/static review when risk justifies it",
        ],
    }


def next_review_trigger(phase: str, readiness_score: int, history_feedback: dict[str, Any] | None = None) -> str:
    signal_types = {signal.get("type") for signal in (history_feedback or {}).get("signals", [])}
    if "eval-regression" in signal_types:
        return "before promoting the last harness/team change, then after the repaired eval task passes"
    if {"readiness-regression", "declining-readiness-trend", "recent-failure-note"} & signal_types:
        return "after the next meaningful task, then again after the repair is validated"
    if "eval-unchanged-fail" in signal_types:
        return "after the next focused harness tune and before generating new team/skill artifacts"
    if signal_types:
        return "after the next 1-2 meaningful cycles, or sooner if the same harness issue repeats"
    if phase == "new-project":
        return "after the first working feature, then every 3-5 meaningful cycles until the harness stabilizes"
    if phase == "prototype":
        return "after the next structure, validation, or product-direction change"
    if phase == "pre-release":
        return "before the next release candidate and after any QA failure"
    if phase == "high-risk":
        return "before planning, before implementation, and after validation evidence is available"
    if readiness_score < 70:
        return "after the next harness change or repeated agent miss"
    return "every 3-5 meaningful cycles, or sooner after repeated mistakes or validation drift"


def history_signal_types(history_feedback: dict[str, Any] | None) -> list[str]:
    signals = (history_feedback or {}).get("signals", [])
    return sorted({str(signal.get("type")) for signal in signals if isinstance(signal, dict) and signal.get("type")})


def adaptive_cadence_recommendation(
    phase: str,
    base_cadence: str,
    next_trigger: str,
    readiness_score: int,
    history_feedback: dict[str, Any] | None,
) -> dict[str, Any]:
    signal_types = set(history_signal_types(history_feedback))
    review_pressure = str((history_feedback or {}).get("review_pressure") or "normal")
    severity = "normal"
    interval = "use phase default cadence"
    reason = "No stored history or eval signal requires a shorter review interval."
    if review_pressure == "high":
        severity = "high"
        interval = "next meaningful cycle, then again after repair validation"
        reason = "High review pressure means the harness should be checked again immediately after the next repair or meaningful task."
    elif review_pressure == "elevated":
        severity = "elevated"
        interval = "after the next 1-2 meaningful cycles"
        reason = "Stored history or eval signals suggest checking sooner than the phase default."
    elif readiness_score < 70:
        severity = "elevated"
        interval = "after the next harness change"
        reason = "Readiness is below the stable range, so the next harness change should be reviewed promptly."

    if "eval-regression" in signal_types:
        interval = "before promoting the last harness/team change, then after the repaired eval task passes"
    elif "eval-unchanged-fail" in signal_types and severity != "high":
        interval = "after the next focused harness tune"

    return {
        "current_phase": phase,
        "base_cadence": base_cadence,
        "review_pressure": review_pressure,
        "severity": severity,
        "recommended_interval": interval,
        "next_trigger": next_trigger,
        "reason": reason,
        "evidence_signals": sorted(signal_types),
        "approval_required": False,
        "apply_policy_change_requires_approval": True,
    }


def adaptive_human_involvement_recommendation(
    phase: str,
    current_default: int,
    readiness_score: int,
    modules: list[str] | None,
    involvement_enforcement: list[dict[str, str]],
    overhead: list[dict[str, str]],
    history_feedback: dict[str, Any] | None,
) -> dict[str, Any]:
    signal_types = set(history_signal_types(history_feedback))
    review_pressure = str((history_feedback or {}).get("review_pressure") or "normal")
    recommended = current_default
    direction = "keep"
    confidence = "medium"
    reason = "Keep the current phase default; no evidence justifies changing human involvement."
    module_overrides: list[dict[str, Any]] = []

    raise_signals = {
        "readiness-regression",
        "declining-readiness-trend",
        "recent-failure-note",
        "eval-regression",
        "eval-unchanged-fail",
        "repeated-human-involvement-gap",
    }
    lower_signals = {"repeated-process-overhead"}

    should_raise = (
        bool(raise_signals & signal_types)
        or review_pressure == "high"
        or (bool(involvement_enforcement) and readiness_score >= 60)
    )
    should_lower = bool(lower_signals & signal_types) and not should_raise and current_default > 2 and phase not in {"pre-release", "high-risk"}

    if should_raise and current_default < 5:
        recommended = max(current_default + 1, 4)
        recommended = min(5, recommended)
        direction = "raise"
        confidence = "high" if review_pressure == "high" or involvement_enforcement else "medium"
        reason = "Repeated misses, eval pressure, or ask-before-edit gaps justify asking the user more often until the harness stabilizes."
        module_overrides.append(
            {
                "area": "Harness repair and policy-sensitive edits",
                "recommended_human_involvement": recommended,
                "reason": reason,
            }
        )
    elif should_lower:
        recommended = current_default - 1
        direction = "lower"
        confidence = "low"
        reason = "Repeated process overhead suggests lowering involvement for routine low-risk work, while keeping protected areas at level 5."
        module_overrides.append(
            {
                "area": "Routine low-risk implementation or docs edits",
                "recommended_human_involvement": recommended,
                "reason": reason,
            }
        )
    elif current_default >= 5:
        reason = "The current phase already requires explicit approval before edits."

    suggested_command = None
    if direction != "keep":
        suggested_command = f"rerun with --human-involvement {recommended} after the user approves this policy change"

    return {
        "current_default": current_default,
        "recommended_default": recommended,
        "direction": direction,
        "confidence": confidence,
        "reason": reason,
        "evidence_signals": sorted(signal_types),
        "module_overrides": module_overrides,
        "approval_required": direction != "keep",
        "silent_apply": False,
        "suggested_command_or_doc_change": suggested_command
        or "no human-involvement policy change recommended",
    }


def build_adaptive_recommendations(
    phase: str,
    base_cadence: str,
    design: dict[str, Any],
    readiness_score: int,
    current_human_involvement: int,
    modules: list[str] | None,
    involvement_enforcement: list[dict[str, str]],
    overhead: list[dict[str, str]],
    history_feedback: dict[str, Any] | None,
) -> dict[str, Any]:
    cadence = adaptive_cadence_recommendation(
        phase,
        base_cadence,
        str(design.get("next_review_trigger") or ""),
        readiness_score,
        history_feedback,
    )
    involvement = adaptive_human_involvement_recommendation(
        phase,
        current_human_involvement,
        readiness_score,
        modules,
        involvement_enforcement,
        overhead,
        history_feedback,
    )
    evidence = sorted(set(cadence["evidence_signals"]) | set(involvement["evidence_signals"]))
    confidence = "high" if cadence["severity"] == "high" or involvement["confidence"] == "high" else "medium"
    if not evidence and cadence["severity"] == "normal" and involvement["direction"] == "keep":
        confidence = "low"
    return {
        "schema": "repo-harness-tuner.adaptive.v1",
        "mode": "recommendation-only",
        "confidence": confidence,
        "evidence_signals": evidence,
        "cadence": cadence,
        "human_involvement": involvement,
        "approval_required_for_policy_change": involvement["approval_required"] or cadence["apply_policy_change_requires_approval"],
        "silent_apply": False,
    }


def merge_target_files(items: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for item in items:
        path = item["path"]
        if path not in merged:
            merged[path] = dict(item)
            continue
        current = merged[path]
        if current["action"] != item["action"] and current["action"] != "create":
            current["action"] = f"{current['action']}/{item['action']}"
        if item["reason"] not in current["reason"]:
            current["reason"] = f"{current['reason']}; {item['reason']}"
    return list(merged.values())


def build_harness_design(
    root: Path,
    repo_scan: dict[str, Any],
    phase: str,
    readiness: dict[str, Any],
    drift: list[dict[str, str]],
    overhead: list[dict[str, str]],
    involvement_enforcement: list[dict[str, str]],
    human_involvement: int,
    repo_type: str | None = None,
    history_feedback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    preset = project_preset(repo_scan, repo_type)
    missing = list(repo_scan.get("missing_recommended", []))
    target_files: list[dict[str, str]] = []

    for rel in missing:
        target_files.append(
            {
                "path": rel,
                "action": "create",
                "reason": "baseline harness file is missing for this repository",
            }
        )
    if drift:
        target_files.append(
            {
                "path": "Docs/AI/validation.md",
                "action": "update",
                "reason": "detected validation/script drift",
            }
        )
    if involvement_enforcement:
        target_files.append(
            {
                "path": "Docs/AI/ambiguity-profile.md",
                "action": "update",
                "reason": "human-involvement ask/decide enforcement is incomplete",
            }
        )
        target_files.append(
            {
                "path": "AGENTS.md",
                "action": "link/update",
                "reason": "repo entrypoint must point agents to ask-before-edit rules",
            }
        )
    if overhead:
        target_files.append(
            {
                "path": "AGENTS.md and Docs/AI/*",
                "action": "shorten or demote",
                "reason": "overbroad process rules are increasing task overhead",
            }
        )
    if history_feedback and history_feedback.get("recommendations"):
        if not any(item["path"] == "Docs/AI/harness-profile.md" for item in target_files):
            target_files.append(
                {
                    "path": "Docs/AI/harness-profile.md",
                    "action": "update",
                    "reason": "recent harness history shows recurring issues or readiness pressure",
                }
            )

    target_files = merge_target_files(target_files)

    if not target_files:
        target_files.append(
            {
                "path": "no file edit",
                "action": "observe",
                "reason": "current harness is fit enough; keep watching for drift or repeated misses",
            }
        )

    needs_restructure = any(item["action"] != "observe" for item in target_files)
    score_value = int(readiness["score"])
    loop = {
        "analyze": [
            "inspect AGENTS.md, Docs/AI/*, README, native scripts, CI/hooks, and recent coordination docs",
            "identify project type and validation surface before adding rules",
        ],
        "diagnose": [
            "score readiness",
            "detect drift, overbroad process, and human-involvement enforcement gaps",
            "read recent harness history and identify recurring misses when present",
            "choose the smallest reversible harness change",
        ],
        "design": [
            "select target files, worker pattern, validation evidence, and next review trigger",
            "prefer the lightest worker pattern that still reduces the diagnosed risk",
        ],
        "restructure": [
            "update only target files that pay rent for future agent reliability",
            "prefer advisory repo-local docs before scripts, hooks, CI, or release gates",
        ],
        "evaluate": [step["command"] for step in build_evaluation_steps(root, repo_scan, phase)],
    }

    return {
        "project_type": preset["key"],
        "project_label": preset["label"],
        "project_markers": preset["markers"],
        "primary_risks": preset["primary_risks"],
        "validation_emphasis": preset["validation_emphasis"],
        "baseline_files": preset["baseline_files"],
        "target_files": target_files,
        "worker_architecture": worker_architecture(
            phase,
            human_involvement,
            score_value,
            needs_restructure,
            len(drift),
            len(overhead),
            len(involvement_enforcement),
            str(preset["key"]),
        ),
        "loop": loop,
        "evaluation_steps": build_evaluation_steps(root, repo_scan, phase),
        "history_feedback": history_feedback or {},
        "next_review_trigger": next_review_trigger(phase, score_value, history_feedback),
    }


def diagnose(
    root: Path,
    repo_scan: dict[str, Any],
    phase: str,
    modules: list[str] | None = None,
    human_involvement: int | None = None,
    repo_type: str | None = None,
) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"Unknown phase: {phase}")
    score = score_repo(root.resolve(), repo_scan, phase)
    drift = drift_check(root.resolve(), repo_scan)
    overhead = overbroad_process_check(root.resolve())
    involvement_enforcement = ambiguity_enforcement_check(root.resolve())
    if overhead:
        penalty = min(20, len(overhead) * 5)
        score["score"] = max(0, int(score["score"]) - penalty)
        score["findings"].append(
            {
                "status": "gap",
                "title": "Process overhead",
                "detail": f"{len(overhead)} overbroad process rule(s) detected; score reduced by {penalty}.",
            }
        )
        score["recommendations"] = dedupe(
            list(score["recommendations"])
            + [
                "Narrow overbroad process rules so full validation, detailed reports, visible chats, and plans trigger only when risk justifies them."
            ]
        )
    if involvement_enforcement:
        penalty = min(20, len(involvement_enforcement) * 5)
        score["score"] = max(0, int(score["score"]) - penalty)
        score["findings"].append(
            {
                "status": "gap",
                "title": "Human involvement enforcement",
                "detail": f"{len(involvement_enforcement)} human-involvement enforcement issue(s) detected; score reduced by {penalty}.",
            }
        )
        score["recommendations"] = dedupe(
            list(score["recommendations"])
            + [
                "Add or strengthen Docs/AI/ambiguity-profile.md so high human-involvement areas force ask-before-edit behavior and low human-involvement areas allow inference."
            ]
        )
    history_feedback = history_store.build_feedback(root.resolve())
    if history_feedback.get("signals"):
        score["findings"].append(
            {
                "status": "gap" if history_feedback.get("review_pressure") == "high" else "warn",
                "title": "Harness history feedback",
                "detail": (
                    f"{history_feedback['count']} history snapshot(s), "
                    f"{history_feedback.get('eval_score_records', 0)} eval score record(s), "
                    f"{len(history_feedback['signals'])} signal(s), "
                    f"review pressure {history_feedback['review_pressure']}."
                ),
            }
        )
        score["recommendations"] = dedupe(
            list(score["recommendations"]) + list(history_feedback.get("recommendations", []))
        )
    phase_info = PHASES[phase]
    resolved_human_involvement = (
        human_involvement
        if human_involvement is not None
        else human_involvement_from_ambiguity(int(phase_info["default_ambiguity"]))
    )
    internal_default = ambiguity_from_human_involvement(human_involvement, phase)
    public_matrix = human_involvement_matrix(phase, modules, human_involvement)
    internal_matrix = ambiguity_matrix(phase, modules, human_involvement)
    design = build_harness_design(
        root.resolve(),
        repo_scan,
        phase,
        score,
        drift,
        overhead,
        involvement_enforcement,
        resolved_human_involvement,
        repo_type,
        history_feedback,
    )
    adaptive = build_adaptive_recommendations(
        phase,
        str(phase_info["cadence"]),
        design,
        int(score["score"]),
        resolved_human_involvement,
        modules,
        involvement_enforcement,
        overhead,
        history_feedback,
    )
    return {
        "phase": phase,
        "cadence": phase_info["cadence"],
        "human_involvement": resolved_human_involvement,
        "human_involvement_policy": involvement_text(resolved_human_involvement),
        "readiness": score,
        "drift": drift,
        "process_overhead": overhead,
        "human_involvement_enforcement": involvement_enforcement,
        "history_feedback": history_feedback,
        "human_involvement_matrix": public_matrix,
        "harness_design": design,
        "adaptive": adaptive,
        "internal": {
            "default_ambiguity": internal_default,
            "ambiguity_enforcement": involvement_enforcement,
            "ambiguity_matrix": internal_matrix,
        },
    }


def build_tuning_prompt(payload: dict[str, Any], repo_type: str, modules: list[str] | None = None) -> str:
    readiness = payload["readiness"]
    recommendations = readiness.get("recommendations", [])
    drift = payload.get("drift", [])
    overhead = payload.get("process_overhead", [])
    involvement_enforcement = payload.get("human_involvement_enforcement", [])
    history_feedback = payload.get("history_feedback", {})
    design = payload.get("harness_design", {})
    effective_repo_type = repo_type
    if not effective_repo_type or effective_repo_type == "unknown":
        effective_repo_type = str(design.get("project_label") or design.get("project_type") or "unknown")

    lines = [
        "Use the embedded codex-harness-setup skill from the repo-harness-tuner plugin.",
        "",
        "Mode: Targeted upgrade" if recommendations or drift or overhead else "Mode: Audit only",
        f"Repository type: {effective_repo_type}",
        f"Project phase: {payload['phase']}",
        f"Current harness readiness: {readiness['score']}/{readiness['max_score']}",
        f"Human involvement: {payload['human_involvement']}/5",
        f"Human involvement policy: {payload['human_involvement_policy']}",
        f"Recommended tuning cadence: {payload['cadence']}",
        "",
        "Diagnosis summary:",
    ]
    for finding in readiness["findings"]:
        lines.append(f"- {finding['status']}: {finding['title']} - {finding['detail']}")

    lines.append("")
    lines.append("Recommended changes:")
    if recommendations:
        for item in recommendations:
            lines.append(f"- {item}")
    else:
        lines.append("- No immediate harness changes recommended; keep the harness light.")

    if drift:
        lines.append("")
        lines.append("Drift to address:")
        for item in drift:
            lines.append(f"- {item['type']}: {item['detail']}")

    if overhead:
        lines.append("")
        lines.append("Overbroad process rules to narrow:")
        for item in overhead:
            lines.append(f"- {item['item']}: {item['detail']}")

    if involvement_enforcement:
        lines.append("")
        lines.append("Human involvement enforcement gaps to address:")
        for item in involvement_enforcement:
            lines.append(f"- {item['item']}: {item['detail']}")

    if history_feedback.get("signals"):
        lines.append("")
        lines.append("Harness history feedback:")
        lines.append(f"- Review pressure: {history_feedback.get('review_pressure', 'normal')}")
        lines.append(f"- Eval score records: {history_feedback.get('eval_score_records', 0)}")
        for signal in history_feedback["signals"]:
            lines.append(f"- {signal['type']}: {signal['detail']}")
        if history_feedback.get("recommendations"):
            lines.append("History-informed recommendations:")
            for item in history_feedback["recommendations"]:
                lines.append(f"- {item}")

    if design:
        lines.append("")
        lines.append("Harness design target:")
        lines.append(f"- Project type: {design.get('project_label', design.get('project_type', 'unknown'))}")
        for item in design.get("target_files", []):
            lines.append(f"- {item['action']}: {item['path']} - {item['reason']}")
        worker = design.get("worker_architecture", {})
        if worker:
            lines.append(
                f"- Worker pattern: {worker.get('label', worker.get('pattern'))} "
                f"[{worker.get('pattern')}] ({worker.get('default_visibility')})"
            )
            if worker.get("selection_reasons"):
                for reason in worker["selection_reasons"]:
                    lines.append(f"  - Reason: {reason}")
        lines.append(f"- Next review trigger: {design.get('next_review_trigger', 'after meaningful project change')}")

    lines.append("")
    lines.append("Human involvement and worker visibility matrix:")
    for row in payload["human_involvement_matrix"]:
        lines.append(
            f"- {row['area']}: human involvement {row['human_involvement']}/5, "
            f"{row['visibility']}, validation: {row['validation']}"
        )

    lines.extend(
        [
            "",
            "Human involvement policy to enforce:",
            "- Human involvement 5: stop and ask for explicit approval before edits.",
            "- Human involvement 4: ask 1-3 focused questions before edits unless a named repo source of truth already answers them.",
            "- Human involvement 3: infer from repo context, but ask before hard-to-reverse or user-visible direction changes.",
            "- Human involvement 2: proceed from existing patterns; mention assumptions in closeout.",
            "- Human involvement 1: explore autonomously unless a protected area or explicit approval trigger appears.",
            "- Any row or rule marked Ask before is a stop condition before file edits.",
        ]
    )

    if modules:
        lines.append("")
        lines.append("Module overrides requested:")
        for module in modules:
            lines.append(f"- {module}")

    lines.extend(
        [
        "",
        "Apply the smallest useful repo-local harness change as the Design and Restructure step of the analyze -> diagnose -> design -> restructure -> evaluate loop.",
        "Prefer updating AGENTS.md, Docs/AI/harness-profile.md, Docs/AI/validation.md, or Docs/AI/ambiguity-profile.md only when the diagnosis shows a real gap.",
        "When updating human involvement rules, write explicit ask-before-edit triggers and explicit agent-may-decide cases; high involvement should materially increase user questions or approval gates.",
        "Do not add CI gates, release blockers, dependencies, destructive scripts, or mandatory approvals without explicit user approval.",
        "Evaluate by running the embedded check_harness.py if available, rerunning diagnose, and summarizing changed files, validation, skipped checks, and remaining risks.",
    ]
    )
    return "\n".join(lines)


def write_status(root: Path, payload: dict[str, Any]) -> Path:
    docs_ai = root / "Docs" / "AI"
    docs_ai.mkdir(parents=True, exist_ok=True)
    path = docs_ai / "harness-status.md"
    readiness = payload["readiness"]
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Harness Status",
        "",
        f"Updated: {timestamp}",
        f"Phase: {payload['phase']}",
        f"Harness readiness: {readiness['score']}/{readiness['max_score']}",
        f"Human involvement: {payload['human_involvement']}/5",
        f"Human involvement policy: {payload['human_involvement_policy']}",
        f"Recommended tuning cadence: {payload['cadence']}",
        f"Next review trigger: {payload['harness_design']['next_review_trigger']}",
        "",
        "## Adaptive Recommendations",
    ]
    adaptive = payload.get("adaptive", {})
    cadence = adaptive.get("cadence", {}) if isinstance(adaptive, dict) else {}
    involvement = adaptive.get("human_involvement", {}) if isinstance(adaptive, dict) else {}
    if cadence:
        lines.append(
            f"- Cadence: {cadence.get('severity', 'normal')} pressure, "
            f"recommended `{cadence.get('recommended_interval', 'use phase default cadence')}`."
        )
    if involvement:
        lines.append(
            f"- Human involvement: {involvement.get('direction', 'keep')} "
            f"{involvement.get('current_default', payload['human_involvement'])}/5 -> "
            f"{involvement.get('recommended_default', payload['human_involvement'])}/5."
        )
        if involvement.get("approval_required"):
            lines.append("- Policy change requires explicit user approval; no silent apply.")
    lines.extend(
        [
            "",
            "## Findings",
        ]
    )
    for finding in readiness["findings"]:
        lines.append(f"- {finding['status']}: {finding['title']} - {finding['detail']}")
    lines.append("")
    lines.append("## Recommended Changes")
    if readiness["recommendations"]:
        for item in readiness["recommendations"]:
            lines.append(f"- {item}")
    else:
        lines.append("- No immediate harness changes recommended.")
    lines.append("")
    lines.append("## Drift")
    if payload["drift"]:
        for item in payload["drift"]:
            lines.append(f"- {item['type']}: {item['detail']}")
    else:
        lines.append("- No obvious drift detected.")
    lines.append("")
    lines.append("## Process Overhead")
    if payload["process_overhead"]:
        for item in payload["process_overhead"]:
            lines.append(f"- {item['item']}: {item['detail']}")
    else:
        lines.append("- No overbroad process rules detected.")
    lines.append("")
    lines.append("## Human Involvement Enforcement")
    if payload["human_involvement_enforcement"]:
        for item in payload["human_involvement_enforcement"]:
            lines.append(f"- {item['item']}: {item['detail']}")
    else:
        lines.append("- Ask/decide enforcement is present.")
    lines.append("")
    lines.append("## Harness History Feedback")
    history_feedback = payload.get("history_feedback", {})
    if history_feedback.get("signals"):
        lines.append(f"- Review pressure: {history_feedback.get('review_pressure', 'normal')}")
        lines.append(f"- Eval score records: {history_feedback.get('eval_score_records', 0)}")
        for signal in history_feedback["signals"]:
            lines.append(f"- {signal['type']}: {signal['detail']}")
    else:
        lines.append("- No history pressure detected.")
    lines.append("")
    lines.append("## Harness Design")
    for item in payload["harness_design"]["target_files"]:
        lines.append(f"- {item['action']}: {item['path']} - {item['reason']}")
    lines.append("")
    lines.append("## Worker Architecture")
    worker = payload["harness_design"]["worker_architecture"]
    lines.append(f"- Pattern: {worker.get('label', worker['pattern'])} ({worker['pattern']})")
    lines.append(f"- Default visibility: {worker['default_visibility']}")
    lines.append(f"- Coordination: {worker['coordination']}")
    for reason in worker.get("selection_reasons", []):
        lines.append(f"- Selection reason: {reason}")
    lines.append("")
    lines.append("## Evaluation Steps")
    for step in payload["harness_design"]["evaluation_steps"]:
        lines.append(f"- {step['when']}: `{step['command']}`")
    lines.append("")
    lines.append("## Human Involvement Matrix")
    for row in payload["human_involvement_matrix"]:
        lines.append(
            f"- {row['area']}: human involvement {row['human_involvement']}/5, "
            f"{row['visibility']}, validation: {row['validation']}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_design_plan(root: Path, payload: dict[str, Any]) -> Path:
    docs_ai = root / "Docs" / "AI"
    docs_ai.mkdir(parents=True, exist_ok=True)
    path = docs_ai / "harness-design-plan.md"
    design = payload["harness_design"]
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Harness Design Plan",
        "",
        f"Updated: {timestamp}",
        f"Project type: {design['project_label']} ({design['project_type']})",
        f"Phase: {payload['phase']}",
        f"Readiness: {payload['readiness']['score']}/{payload['readiness']['max_score']}",
        f"Human involvement: {payload['human_involvement']}/5",
        f"Next review trigger: {design['next_review_trigger']}",
        "",
        "## Primary Risks",
    ]
    for item in design["primary_risks"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Target Files")
    for item in design["target_files"]:
        lines.append(f"- {item['action']}: {item['path']} - {item['reason']}")
    lines.append("")
    lines.append("## Loop")
    for stage in ["analyze", "diagnose", "design", "restructure", "evaluate"]:
        lines.append(f"### {stage.title()}")
        for item in design["loop"][stage]:
            lines.append(f"- {item}")
        lines.append("")
    lines.append("## Worker Architecture")
    worker = design["worker_architecture"]
    lines.append(f"- Pattern: {worker.get('label', worker['pattern'])} ({worker['pattern']})")
    lines.append(f"- Default visibility: {worker['default_visibility']}")
    lines.append(f"- Coordination: {worker['coordination']}")
    for reason in worker.get("selection_reasons", []):
        lines.append(f"- Selection reason: {reason}")
    lines.append("")
    lines.append("Visible chats:")
    for item in worker["visible_chats"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Background workers:")
    for item in worker["background_workers"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Evaluation Steps")
    for step in design["evaluation_steps"]:
        lines.append(f"- {step['when']}: `{step['command']}`")
    history_feedback = payload.get("history_feedback", {})
    lines.append("")
    lines.append("## Harness History Feedback")
    if history_feedback.get("signals"):
        lines.append(f"- Review pressure: {history_feedback.get('review_pressure', 'normal')}")
        for signal in history_feedback["signals"]:
            lines.append(f"- {signal['type']}: {signal['detail']}")
    else:
        lines.append("- No history pressure detected.")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def print_harness_design(design: dict[str, Any]) -> None:
    print("Harness design:")
    print(f"- Project type: {design['project_label']} ({design['project_type']})")
    if design["project_markers"]:
        print(f"- Markers: {', '.join(design['project_markers'])}")
    print("- Primary risks:")
    for item in design["primary_risks"]:
        print(f"  - {item}")
    print("- Target files:")
    for item in design["target_files"]:
        print(f"  - {item['action']}: {item['path']} - {item['reason']}")
    worker = design["worker_architecture"]
    print(f"- Worker pattern: {worker.get('label', worker['pattern'])} ({worker['pattern']})")
    print(f"- Default visibility: {worker['default_visibility']}")
    print(f"- Coordination: {worker['coordination']}")
    if worker.get("selection_reasons"):
        print("- Pattern selection:")
        for reason in worker["selection_reasons"]:
            print(f"  - {reason}")
    print("- Evaluation:")
    for step in design["evaluation_steps"]:
        print(f"  - {step['when']}: {step['command']}")
    print(f"- Next review: {design['next_review_trigger']}")


def print_diagnosis(payload: dict[str, Any]) -> None:
    readiness = payload["readiness"]
    print(f"Phase: {payload['phase']}")
    print(f"Harness Readiness: {readiness['score']}/{readiness['max_score']}")
    print(f"Human involvement: {payload['human_involvement']}/5")
    print(f"Human involvement policy: {payload['human_involvement_policy']}")
    print(f"Tuning cadence: {payload['cadence']}")
    print("")
    print("Findings:")
    for finding in readiness["findings"]:
        print(f"- {finding['status']}: {finding['title']} - {finding['detail']}")
    print("")
    print("Recommended changes:")
    if readiness["recommendations"]:
        for item in readiness["recommendations"]:
            print(f"- {item}")
    else:
        print("- No immediate harness changes recommended.")
    print("")
    print("Drift:")
    if payload["drift"]:
        for item in payload["drift"]:
            print(f"- {item['type']}: {item['detail']}")
    else:
        print("- No obvious drift detected.")
    print("")
    print("Process overhead:")
    if payload["process_overhead"]:
        for item in payload["process_overhead"]:
            print(f"- {item['item']}: {item['detail']}")
    else:
        print("- No overbroad process rules detected.")
    print("")
    print("Human involvement enforcement:")
    if payload["human_involvement_enforcement"]:
        for item in payload["human_involvement_enforcement"]:
            print(f"- {item['item']}: {item['detail']}")
    else:
        print("- Ask/decide enforcement is present.")
    print("")
    print("Harness history feedback:")
    history_feedback = payload.get("history_feedback", {})
    if history_feedback.get("signals"):
        print(f"- Review pressure: {history_feedback.get('review_pressure', 'normal')}")
        print(f"- Eval score records: {history_feedback.get('eval_score_records', 0)}")
        for signal in history_feedback["signals"]:
            print(f"- {signal['type']}: {signal['detail']}")
    else:
        print("- No history pressure detected.")
    print("")
    adaptive = payload.get("adaptive", {})
    cadence = adaptive.get("cadence", {}) if isinstance(adaptive, dict) else {}
    involvement = adaptive.get("human_involvement", {}) if isinstance(adaptive, dict) else {}
    print("Adaptive recommendations:")
    if cadence:
        print(
            f"- Cadence: {cadence.get('severity', 'normal')} pressure, "
            f"{cadence.get('recommended_interval', 'use phase default cadence')}"
        )
    if involvement:
        print(
            f"- Human involvement: {involvement.get('direction', 'keep')} "
            f"{involvement.get('current_default', payload['human_involvement'])}/5 -> "
            f"{involvement.get('recommended_default', payload['human_involvement'])}/5"
        )
        if involvement.get("approval_required"):
            print("- Approval required before changing human-involvement policy.")
    print("")
    print_harness_design(payload["harness_design"])
    print("")
    print("Human involvement matrix:")
    for row in payload["human_involvement_matrix"]:
        print(
            f"- {row['area']}: human involvement {row['human_involvement']}/5, "
            f"{row['visibility']}, validation: {row['validation']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", default=".")
    parser.add_argument("--phase", default="active-development", choices=sorted(PHASES))
    parser.add_argument("--module", action="append")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--repo-type", default="unknown")
    parser.add_argument("--emit-prompt", action="store_true")
    parser.add_argument("--write-status", action="store_true")
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--confirm-write", action="store_true", help="Confirm file writes when human involvement is 4 or 5.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    import scan_repo_harness

    root = Path(args.repo_root)
    repo_scan = scan_repo_harness.scan(root)
    payload = diagnose(root, repo_scan, args.phase, args.module, args.human_involvement, args.repo_type)
    if args.write_status or args.write_plan:
        guard = write_policy.write_guard("diagnose", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            payload["write_blocked"] = guard
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=True))
            else:
                print(write_policy.format_guard(guard))
            return 2
    if args.emit_prompt:
        payload["tuning_prompt"] = build_tuning_prompt(payload, args.repo_type, args.module)
    if args.write_status:
        payload["status_path"] = str(write_status(root.resolve(), payload))
    if args.write_plan:
        payload["plan_path"] = str(write_design_plan(root.resolve(), payload))
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print_diagnosis(payload)
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


if __name__ == "__main__":
    raise SystemExit(main())
