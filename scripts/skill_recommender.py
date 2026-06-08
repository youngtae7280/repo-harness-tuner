#!/usr/bin/env python3
"""Recommend and install minimal Codex skill adapters from repo evidence."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
GENERATED_MARKER = "<!-- repo-harness-tuner:generated:skill-recommendation -->"
MAX_RECOMMENDATIONS = 3


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
history_store = load_local_module("history_store")
write_policy = load_local_module("write_policy")


CAPABILITY_RULES: list[dict[str, Any]] = [
    {
        "id": "code-review",
        "label": "Code review",
        "base": 30,
        "project_types": ["vite-node", "node", "python", "codex-plugin", "unity", "godot"],
        "scripts": ["lint", "typecheck", "test", "build"],
        "signals": ["eval-regression", "recent-failure-note", "readiness-regression"],
        "keywords": ["review", "quality", "bug", "regression"],
        "reason": "review code quality, regressions, and maintainability before Codex merges changes",
    },
    {
        "id": "tdd",
        "label": "TDD and regression reproduction",
        "base": 18,
        "project_types": ["vite-node", "node", "python", "codex-plugin"],
        "scripts": ["test", "check", "validate"],
        "signals": ["eval-unchanged-fail", "eval-regression", "repeated-validation-drift"],
        "keywords": ["test", "tdd", "regression", "fixture"],
        "reason": "turn repeated failures into focused tests before changing the harness again",
    },
    {
        "id": "security",
        "label": "Security review",
        "base": 12,
        "project_types": ["vite-node", "node", "python", "codex-plugin"],
        "scripts": ["audit", "security"],
        "signals": ["recent-failure-note"],
        "keywords": ["security", "secret", "credential", "auth", "payment", "privacy"],
        "phase_bonus": {"pre-release": 35, "high-risk": 45},
        "reason": "check secrets, dependencies, auth, and policy-sensitive changes before risky work",
    },
    {
        "id": "docs",
        "label": "Documentation",
        "base": 20,
        "project_types": ["docs-only", "codex-plugin"],
        "scripts": ["docs"],
        "signals": ["repeated-human-involvement-gap"],
        "keywords": ["docs", "documentation", "readme", "guide", "manual"],
        "reason": "keep user-facing and repo-local guidance short, current, and source-backed",
    },
    {
        "id": "build-fix",
        "label": "Build failure repair",
        "base": 18,
        "project_types": ["vite-node", "node", "python", "codex-plugin", "unity", "godot"],
        "scripts": ["build", "compile", "typecheck", "check"],
        "signals": ["repeated-validation-drift", "eval-unchanged-fail"],
        "keywords": ["build", "compile", "validation", "typecheck"],
        "reason": "repair build or validation failures with the nearest native command",
    },
    {
        "id": "frontend-ui",
        "label": "Frontend UI",
        "base": 10,
        "project_types": ["vite-node", "node"],
        "scripts": ["dev", "build", "lint"],
        "signals": [],
        "keywords": ["frontend", "website", "react", "vite", "ui", "screen"],
        "reason": "keep UI implementation and browser evidence grounded in the detected frontend stack",
    },
    {
        "id": "release-check",
        "label": "Release check",
        "base": 8,
        "project_types": ["codex-plugin", "vite-node", "node", "python"],
        "scripts": ["release", "publish", "version", "build", "test"],
        "signals": ["eval-regression", "readiness-regression"],
        "keywords": ["release", "publish", "deploy", "ship", "version"],
        "phase_bonus": {"pre-release": 45, "high-risk": 35},
        "reason": "gate release-facing changes with explicit validation and approval evidence",
    },
    {
        "id": "harness-curation",
        "label": "Harness curation",
        "base": 15,
        "project_types": ["codex-plugin", "docs-only", "vite-node", "node", "python", "unity", "godot"],
        "scripts": ["validate", "check", "test"],
        "signals": [
            "repeated-process-overhead",
            "repeated-human-involvement-gap",
            "repeated-validation-drift",
            "declining-readiness-trend",
        ],
        "keywords": ["harness", "agent", "skill", "codex", "process"],
        "reason": "revise, keep, or retire skill guidance based on history and eval evidence",
    },
]


ECC_SEED_CATALOG: list[dict[str, Any]] = [
    {
        "id": "ecc-code-reviewer",
        "capability": "code-review",
        "name": "code-reviewer",
        "surface": "agent/command",
        "native_invocation": "/code-review or code-reviewer agent",
        "paths": ["agents/code-reviewer.md", "commands/code-review.md"],
    },
    {
        "id": "ecc-tdd-workflow",
        "capability": "tdd",
        "name": "tdd-workflow",
        "surface": "skill",
        "native_invocation": "tdd-workflow skill",
        "paths": ["skills/tdd-workflow/SKILL.md", "commands/tdd-workflow.md"],
    },
    {
        "id": "ecc-security-scan",
        "capability": "security",
        "name": "security-scan",
        "surface": "command/agent",
        "native_invocation": "/security-scan or security-reviewer agent",
        "paths": ["commands/security-scan.md", "agents/security-reviewer.md"],
    },
    {
        "id": "ecc-build-fix",
        "capability": "build-fix",
        "name": "build-fix",
        "surface": "command/agent",
        "native_invocation": "/build-fix or build-error-resolver agent",
        "paths": ["commands/build-fix.md", "agents/build-error-resolver.md"],
    },
    {
        "id": "ecc-e2e-testing",
        "capability": "frontend-ui",
        "name": "e2e-testing",
        "surface": "skill/agent",
        "native_invocation": "e2e-testing skill or e2e-runner agent",
        "paths": ["skills/e2e-testing/SKILL.md", "agents/e2e-runner.md"],
    },
    {
        "id": "ecc-test-coverage",
        "capability": "release-check",
        "name": "test-coverage",
        "surface": "command",
        "native_invocation": "/test-coverage",
        "paths": ["commands/test-coverage.md"],
    },
    {
        "id": "ecc-update-docs",
        "capability": "docs",
        "name": "update-docs",
        "surface": "command/agent",
        "native_invocation": "/update-docs or doc-updater agent",
        "paths": ["commands/update-docs.md", "agents/doc-updater.md"],
    },
]


def dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def short_list(items: list[str], limit: int = 6) -> list[str]:
    return items[:limit]


def normalize_skill_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return (normalized or "recommended-skill")[:64].strip("-") or "recommended-skill"


def parse_sources(value: str | None) -> list[str]:
    text = value or "builtin,ecc"
    tokens = [item.strip().lower() for item in text.split(",") if item.strip()]
    valid = []
    for token in tokens:
        if token == "all":
            valid.extend(["builtin", "ecc"])
        elif token in {"builtin", "factory", "local"}:
            valid.append("builtin")
        elif token in {"ecc", "external"}:
            valid.append("ecc")
    return dedupe(valid) or ["builtin"]


def evidence_strings(factory_payload: dict[str, Any], diagnosis: dict[str, Any], domain: str) -> list[str]:
    evidence = factory_payload.get("repo_evidence", {})
    refs = [str(item) for item in evidence.get("evidence_refs", [])]
    markers = [str(item) for item in diagnosis.get("harness_design", {}).get("project_markers", [])]
    return short_list(dedupe(refs + markers + [f"domain:{domain}"]), 10)


def capability_scores(
    factory_payload: dict[str, Any],
    diagnosis: dict[str, Any],
    phase: str,
    domain: str,
) -> list[dict[str, Any]]:
    project_type = str(factory_payload.get("project_type") or "unknown")
    evidence = factory_payload.get("repo_evidence", {})
    script_names = {str(item.get("name")) for item in evidence.get("package_scripts", []) if isinstance(item, dict)}
    history_feedback = diagnosis.get("history_feedback", {})
    signals = {
        str(signal.get("type"))
        for signal in history_feedback.get("signals", [])
        if isinstance(signal, dict) and signal.get("type")
    }
    text = " ".join(
        [
            domain.lower(),
            project_type.lower(),
            " ".join(str(item).lower() for item in evidence.get("evidence_refs", [])),
            " ".join(script_names).lower(),
        ]
    )
    ranked: list[dict[str, Any]] = []
    for index, rule in enumerate(CAPABILITY_RULES):
        score = int(rule["base"])
        reasons = [str(rule["reason"])]
        if project_type in rule.get("project_types", []):
            score += 25
            reasons.append(f"project type is {project_type}")
        matched_scripts = sorted(script_names & set(rule.get("scripts", [])))
        if matched_scripts:
            score += min(25, 8 * len(matched_scripts))
            reasons.append("native script(s): " + ", ".join(matched_scripts[:3]))
        matched_signals = sorted(signals & set(rule.get("signals", [])))
        if matched_signals:
            score += min(40, 18 * len(matched_signals))
            reasons.append("closed-loop signal(s): " + ", ".join(matched_signals[:3]))
        keyword_hits = [keyword for keyword in rule.get("keywords", []) if keyword in text]
        if keyword_hits:
            score += min(18, 6 * len(keyword_hits))
            reasons.append("keyword(s): " + ", ".join(keyword_hits[:3]))
        phase_bonus = int(rule.get("phase_bonus", {}).get(phase, 0))
        if phase_bonus:
            score += phase_bonus
            reasons.append(f"phase is {phase}")
        if rule["id"] == "harness-curation" and history_feedback.get("review_pressure") in {"elevated", "high"}:
            score += 25
            reasons.append(f"review pressure is {history_feedback.get('review_pressure')}")
        ranked.append(
            {
                "id": rule["id"],
                "label": rule["label"],
                "score": score,
                "rank_key": index,
                "reasons": dedupe(reasons),
            }
        )
    return sorted(ranked, key=lambda item: (-int(item["score"]), int(item["rank_key"])))


def find_factory_skill(capability_id: str, factory_payload: dict[str, Any]) -> dict[str, Any] | None:
    skills = list(factory_payload.get("team_factory", {}).get("skills", []))
    capability_terms = {
        "docs": ["docs", "source-map", "synthesis"],
        "frontend-ui": ["frontend", "browser", "screen"],
        "build-fix": ["validation", "cli-smoke", "engine-change"],
        "release-check": ["validation", "cli-smoke", "team-orchestration"],
        "harness-curation": ["orchestration", "plugin-contract", "quality-review"],
        "code-review": ["quality-review", "docs-review", "validation"],
    }.get(capability_id, [])
    for skill in skills:
        text = f"{skill.get('id', '')} {skill.get('purpose', '')}".lower()
        if any(term in text for term in capability_terms):
            return skill
    return None


def ecc_candidate_for(capability_id: str, catalog_root: Path | None) -> dict[str, Any] | None:
    for entry in ECC_SEED_CATALOG:
        if entry["capability"] != capability_id:
            continue
        candidate = dict(entry)
        checked_paths = []
        found_paths = []
        if catalog_root:
            for rel in entry.get("paths", []):
                path = catalog_root / rel
                checked_paths.append(str(path))
                if path.exists():
                    found_paths.append(str(path))
        candidate["catalog_root"] = str(catalog_root.resolve()) if catalog_root else None
        candidate["checked_paths"] = checked_paths
        candidate["found_paths"] = found_paths
        candidate["catalog_available"] = bool(found_paths) if catalog_root else False
        return candidate
    return None


def build_curator(history_feedback: dict[str, Any], capability_rank: list[dict[str, Any]]) -> dict[str, Any]:
    signals = [
        str(signal.get("type"))
        for signal in history_feedback.get("signals", [])
        if isinstance(signal, dict) and signal.get("type")
    ]
    signal_set = set(signals)
    history_records = int(history_feedback.get("count", 0) or 0)
    eval_score_records = int(history_feedback.get("eval_score_records", 0) or 0)
    has_stored_evidence = history_records > 0 or eval_score_records > 0
    action = "baseline"
    reason = "No stored history/eval record exists yet; install only the smallest useful skill set."
    if {"eval-regression", "eval-unchanged-fail", "readiness-regression", "recent-failure-note"} & signal_set:
        action = "repair"
        reason = "Recent eval/history pressure says the next skill change should repair a concrete miss."
    elif "repeated-process-overhead" in signal_set:
        action = "reduce"
        reason = "Repeated process overhead says to avoid new always-on skills and retire noisy guidance."
    elif "eval-improvement" in signal_set:
        action = "keep"
        reason = "Latest eval evidence improved without regression; keep the current direction and observe."
    elif signals:
        action = "watch"
        reason = "Stored signals exist, but they do not justify a broad skill install."
    elif has_stored_evidence:
        action = "watch"
        reason = (
            f"Stored history/eval exists ({history_records} history, {eval_score_records} eval), "
            "but no pressure signal justifies a broad skill install."
        )

    return {
        "schema": "repo-harness-tuner.skill-curator.v1",
        "mode": "recommendation-only",
        "action": action,
        "reason": reason,
        "evidence_signals": sorted(signal_set),
        "history_records": history_records,
        "eval_score_records": eval_score_records,
        "top_capabilities": [item["id"] for item in capability_rank[:MAX_RECOMMENDATIONS]],
        "approval_required_for_install": True,
        "silent_apply": False,
        "review_next": "after the next eval score or 1-2 meaningful Codex work cycles",
    }


def recommendation_command(
    root: Path,
    phase: str,
    domain: str,
    sources: list[str],
    limit: int,
    catalog_root: Path | None,
    extra: list[str] | None = None,
) -> str:
    parts = [
        "python",
        "scripts/console.py",
        "recommend-skills",
        "--repo",
        quote_cli(root.resolve()),
        "--phase",
        phase,
        "--domain",
        quote_cli(domain),
        "--source",
        ",".join(sources),
        "--limit",
        str(limit),
    ]
    if catalog_root:
        parts.extend(["--catalog-root", quote_cli(catalog_root)])
    if extra:
        parts.extend(extra)
    return " ".join(parts)


def quote_cli(value: str | Path) -> str:
    text = str(value)
    if not text:
        return '""'
    if re.search(r"\s", text):
        return json.dumps(text, ensure_ascii=False)
    return text


def build_recommendation_plan(
    root: Path,
    domain: str,
    phase: str,
    modules: list[str] | None = None,
    human_involvement: int | None = None,
    repo_type: str | None = None,
    team_size: int = 3,
    sources: str | None = None,
    limit: int = MAX_RECOMMENDATIONS,
    catalog_root: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    sources_list = parse_sources(sources)
    limit = max(1, min(MAX_RECOMMENDATIONS, int(limit or MAX_RECOMMENDATIONS)))
    repo_scan = scan_repo_harness.scan(root)
    diagnosis = diagnose_module.diagnose(root, repo_scan, phase, modules, human_involvement, repo_type)
    factory_payload = factory_module.build_factory_plan(root, domain, phase, modules, human_involvement, repo_type, team_size)
    history_feedback = diagnosis.get("history_feedback", {})
    ranked = capability_scores(factory_payload, diagnosis, phase, domain)
    evidence = evidence_strings(factory_payload, diagnosis, domain)
    has_repo_evidence = bool(factory_payload.get("repo_evidence", {}).get("evidence_refs"))
    curator = build_curator(history_feedback, ranked)
    recommendations: list[dict[str, Any]] = []
    used_adapter_names: set[str] = set()

    for capability in ranked:
        if len(recommendations) >= limit:
            break
        capability_id = str(capability["id"])
        score = int(capability.get("score", 0) or 0)
        reason_text = " ".join(str(item) for item in capability.get("reasons", []))
        recommendation: dict[str, Any] | None = None
        ecc = ecc_candidate_for(capability_id, catalog_root) if "ecc" in sources_list else None
        factory_skill = find_factory_skill(capability_id, factory_payload) if "builtin" in sources_list else None
        repair_mode = curator["action"] == "repair"
        external_allowed = score >= 55 or repair_mode
        factory_allowed = score >= 25 and (has_repo_evidence or "keyword(s)" in reason_text or curator["action"] != "baseline")
        external_is_preferred = (
            capability_id in {"code-review", "tdd", "security", "build-fix", "release-check"}
            and ecc is not None
            and external_allowed
        )
        if external_is_preferred:
            recommendation = {
                "id": str(ecc["id"]),
                "capability": capability_id,
                "capability_label": capability["label"],
                "score": capability["score"],
                "source": "ecc",
                "source_kind": "external-catalog-seed",
                "name": ecc["name"],
                "surface": ecc["surface"],
                "native_invocation": ecc["native_invocation"],
                "catalog_root": ecc.get("catalog_root"),
                "catalog_available": ecc.get("catalog_available", False),
                "found_paths": ecc.get("found_paths", []),
                "install_strategy": "codex-adapter-skill",
                "installable": True,
                "approval_required": True,
                "reason": "; ".join(short_list([str(item) for item in capability["reasons"]], 3)),
                "evidence": evidence,
            }
        elif factory_skill is not None and factory_allowed:
            recommendation = {
                "id": f"factory-{factory_skill['id']}",
                "capability": capability_id,
                "capability_label": capability["label"],
                "score": capability["score"],
                "source": "factory",
                "source_kind": "repo-local-generated",
                "name": factory_skill["id"],
                "surface": "repo-local planning artifact",
                "native_invocation": f"repo-local planning artifact {factory_skill['id']}",
                "target_file": factory_skill.get("target_file"),
                "install_strategy": "codex-adapter-skill",
                "installable": True,
                "approval_required": True,
                "reason": "; ".join(short_list([str(item) for item in capability["reasons"]], 3)),
                "evidence": short_list([str(item) for item in factory_skill.get("evidence_refs", evidence)], 8),
            }
        elif ecc is not None and external_allowed:
            recommendation = {
                "id": str(ecc["id"]),
                "capability": capability_id,
                "capability_label": capability["label"],
                "score": capability["score"],
                "source": "ecc",
                "source_kind": "external-catalog-seed",
                "name": ecc["name"],
                "surface": ecc["surface"],
                "native_invocation": ecc["native_invocation"],
                "catalog_root": ecc.get("catalog_root"),
                "catalog_available": ecc.get("catalog_available", False),
                "found_paths": ecc.get("found_paths", []),
                "install_strategy": "codex-adapter-skill",
                "installable": True,
                "approval_required": True,
                "reason": "; ".join(short_list([str(item) for item in capability["reasons"]], 3)),
                "evidence": evidence,
            }
        if recommendation:
            adapter_name = normalize_skill_name(f"{recommendation.get('source', 'factory')}-{recommendation.get('name', recommendation['id'])}")
            if adapter_name in used_adapter_names:
                continue
            used_adapter_names.add(adapter_name)
            recommendations.append(recommendation)

    return {
        "schema": "repo-harness-tuner.skill-recommendations.v1",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "repo": str(root),
        "domain": domain,
        "phase": phase,
        "options": {
            "modules": modules or [],
            "human_involvement": human_involvement,
            "repo_type": repo_type or "unknown",
            "team_size": team_size,
            "sources": sources_list,
            "limit": limit,
            "catalog_root": str(catalog_root.resolve()) if catalog_root else None,
        },
        "summary": {
            "project_type": factory_payload.get("project_type", "unknown"),
            "recommendation_count": len(recommendations),
            "external_recommendation_count": sum(1 for item in recommendations if item.get("source") != "factory"),
            "approval_required": any(bool(item.get("approval_required")) for item in recommendations),
            "curator_action": curator["action"],
            "install_mode": "adapter-only",
            "bulk_install_allowed": False,
        },
        "capabilities": ranked[:limit],
        "recommendations": recommendations,
        "curator": curator,
        "safety": {
            "read_only_default": True,
            "approval_required_for_install": True,
            "external_catalog_bulk_install": False,
            "external_hooks_mcp_commands_are_not_installed": True,
            "writes_outside_repo_require_confirm_install": True,
            "human_involvement_policy_silent_apply": False,
        },
        "commands": [
            recommendation_command(root, phase, domain, sources_list, limit, catalog_root),
            recommendation_command(root, phase, domain, sources_list, limit, catalog_root, ["--write-plan"]),
            recommendation_command(root, phase, domain, sources_list, limit, catalog_root, ["--install", "--confirm-install"]),
        ],
    }


def default_skill_install_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home) / "skills"
    return Path.home() / ".codex" / "skills"


def build_adapter_skill_md(payload: dict[str, Any], recommendation: dict[str, Any]) -> str:
    source = str(recommendation.get("source", "factory"))
    name = normalize_skill_name(f"{source}-{recommendation['name']}")
    capability = str(recommendation.get("capability_label") or recommendation.get("capability"))
    evidence = [str(item) for item in recommendation.get("evidence", [])]
    evidence_text = ", ".join(short_list(evidence, 4)) if evidence else "limited repo evidence"
    description = (
        f"Adapter skill recommended by repo-harness-tuner for {capability}. "
        f"Use when Codex is working on {payload['domain']} and needs {recommendation.get('reason', 'a bounded workflow')}, "
        f"grounded in {evidence_text}. Installs no external hooks, MCPs, or commands."
    )
    lines = [
        "---",
        f"name: {name}",
        f"description: {json.dumps(description, ensure_ascii=False)}",
        "---",
        "",
        f"# {name}",
        GENERATED_MARKER,
        "",
        "## Source",
        f"- Recommendation source: `{source}`",
        f"- Component: `{recommendation.get('name', name)}`",
        f"- Surface: `{recommendation.get('surface', 'Codex skill')}`",
        f"- Native invocation: `{recommendation.get('native_invocation', 'Codex skill')}`",
        f"- Install strategy: `{recommendation.get('install_strategy', 'codex-adapter-skill')}`",
        "",
        "## Use When",
        f"- {recommendation.get('reason', 'This repo needs the recommended capability.')}",
        "",
        "## Repo Evidence",
    ]
    if evidence:
        lines.extend(f"- `{item}`" for item in evidence)
    else:
        lines.append("- No concrete repo evidence was available; start with conservative discovery.")
    lines.extend(
        [
            "",
            "## Workflow",
            "1. Inspect the repo source of truth before adding process.",
            "2. Use this adapter as a bounded checklist, not as permission to install a broad external pack.",
            "3. Prefer existing repo validation commands and record skipped checks explicitly.",
            "4. Escalate before release, dependency, CI, secret, credential, marketplace, migration, privacy-sensitive, destructive, or user-visible direction changes.",
            "5. Return concise evidence to the main Codex thread.",
            "",
            "## External Catalog Boundary",
            "- This adapter does not copy ECC content and does not install ECC hooks, MCP servers, slash commands, or agents.",
            "- If the native ECC component is separately installed and approved, prefer the native component for its original workflow.",
            "- Keep installs minimal; do not add more than the reviewed recommendations.",
            "",
            "## Curator Rule",
            "Use repo-harness-tuner history and eval results to keep, revise, or retire this adapter. Remove it when it adds process overhead without improving the next meaningful task.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_file_once(path: Path, content: str, force: bool, replace_unmanaged: bool = False) -> dict[str, Any]:
    existed = path.exists()
    if existed:
        existing_skill = path / "SKILL.md" if path.is_dir() else path
        existing_text = existing_skill.read_text(encoding="utf-8-sig", errors="replace") if existing_skill.exists() else ""
        generated = GENERATED_MARKER in existing_text
        if not force:
            return {
                "path": str(path),
                "status": "skipped-existing",
                "reason": "Existing skill preserved; review and pass --force to replace generated content.",
            }
        if not generated and not replace_unmanaged:
            return {
                "path": str(path),
                "status": "blocked-unmanaged-existing",
                "reason": "Existing skill has no repo-harness-tuner generated marker; pass --replace-unmanaged with --force after review.",
            }
    if existed and force:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    path.mkdir(parents=True, exist_ok=True)
    return {"path": str(path), "status": "overwrite" if existed else "installed"}


def install_recommended_adapters(
    payload: dict[str, Any],
    install_root: Path | None = None,
    force: bool = False,
    replace_unmanaged: bool = False,
) -> list[dict[str, Any]]:
    root = (install_root or default_skill_install_root()).resolve()
    results: list[dict[str, Any]] = []
    for recommendation in payload.get("recommendations", [])[:MAX_RECOMMENDATIONS]:
        if not recommendation.get("installable"):
            continue
        source = str(recommendation.get("source", "factory"))
        skill_name = normalize_skill_name(f"{source}-{recommendation['name']}")
        destination = root / skill_name
        result = write_file_once(destination, build_adapter_skill_md(payload, recommendation), force, replace_unmanaged)
        if result["status"] in {"installed", "overwrite"}:
            (destination / "SKILL.md").write_text(build_adapter_skill_md(payload, recommendation), encoding="utf-8")
        result.update(
            {
                "skill": skill_name,
                "source": source,
                "component": recommendation.get("name"),
                "capability": recommendation.get("capability"),
            }
        )
        results.append(result)
    return results


def write_recommendation_plan(root: Path, payload: dict[str, Any]) -> Path:
    docs_ai = root / "Docs" / "AI"
    docs_ai.mkdir(parents=True, exist_ok=True)
    path = docs_ai / "skill-recommendations.md"
    lines = [
        "# Skill Recommendations",
        GENERATED_MARKER,
        "",
        f"Updated: {payload['created_at']}",
        f"Domain: {payload['domain']}",
        f"Phase: {payload['phase']}",
        f"Project type: {payload['summary']['project_type']}",
        f"Curator action: {payload['curator']['action']}",
        f"Curator reason: {payload['curator']['reason']}",
        "",
        "## Safety",
        "- Read-only by default.",
        "- Installs require `--install --confirm-install`.",
        "- External catalogs are adapter-only; no bulk ECC install, hooks, MCP servers, commands, or agents are installed.",
        "- Human-involvement policy changes are never silently applied.",
        "",
        "## Recommendations",
    ]
    for item in payload.get("recommendations", []):
        lines.extend(
            [
                f"- `{item['id']}` ({item['source']}): {item['capability_label']}",
                f"  - Component: `{item['name']}` via {item['surface']}",
                f"  - Reason: {item['reason']}",
                f"  - Install strategy: `{item['install_strategy']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Command Flow",
            "- Run preview first, write this plan only after review, and install adapter skills only after explicit approval.",
        ]
    )
    for command in payload.get("commands", []):
        if "--install --confirm-install" in command:
            label = "Confirmed install after approval"
        elif "--write-plan" in command:
            label = "Write this plan"
        else:
            label = "Preview candidates"
        lines.append(f"- {label}: `{command}`")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def print_recommendations(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    print("Skill Recommendations")
    print(f"Repo: {payload['repo']}")
    print(f"Project type: {summary['project_type']}")
    print(f"Sources: {', '.join(payload['options']['sources'])}")
    print(f"Recommendations: {summary['recommendation_count']} (external={summary['external_recommendation_count']})")
    print(f"Curator: {payload['curator']['action']} - {payload['curator']['reason']}")
    print("")
    if not payload["recommendations"]:
        print("No skill or external catalog recommendation is needed right now.")
    for item in payload["recommendations"]:
        print(f"- {item['id']}: {item['capability_label']} [{item['source']}]")
        print(f"  Component: {item['name']} ({item['surface']})")
        print(f"  Reason: {item['reason']}")
        print(f"  Install: {item['install_strategy']} approval_required={item['approval_required']}")
    print("")
    print("Safety:")
    print("- Read-only by default.")
    print("- Install uses Codex adapter skills only and requires --confirm-install.")
    print("- No ECC bulk install, hooks, MCP servers, slash commands, or agents are installed.")


def main() -> int:
    configure_console_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--domain", default="current repository")
    parser.add_argument("--phase", default="active-development", choices=sorted(diagnose_module.PHASES))
    parser.add_argument("--module", action="append")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--repo-type", default="unknown")
    parser.add_argument("--team-size", type=int, default=3)
    parser.add_argument("--source", default="builtin,ecc", help="Comma-separated sources: builtin,ecc,all.")
    parser.add_argument("--limit", type=int, default=MAX_RECOMMENDATIONS)
    parser.add_argument("--catalog-root", help="Optional local checkout for an external catalog such as ECC.")
    parser.add_argument("--write-plan", action="store_true", help="Write Docs/AI/skill-recommendations.md.")
    parser.add_argument("--install", action="store_true", help="Install recommended Codex adapter skills.")
    parser.add_argument("--skill-install-root", help="Destination skills directory. Defaults to $CODEX_HOME/skills or ~/.codex/skills.")
    parser.add_argument("--confirm-install", action="store_true", help="Required with --install.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--replace-unmanaged", action="store_true")
    parser.add_argument("--confirm-write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    catalog_root = Path(args.catalog_root) if args.catalog_root else None
    payload = build_recommendation_plan(
        Path(args.repo),
        args.domain,
        args.phase,
        args.module,
        args.human_involvement,
        args.repo_type,
        args.team_size,
        args.source,
        args.limit,
        catalog_root,
    )
    if args.write_plan or args.install:
        guard = write_policy.write_guard("recommend-skills", args.phase, args.human_involvement, args.confirm_write)
        if guard:
            payload["write_blocked"] = guard
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=True))
            else:
                print_recommendations(payload)
                print("")
                print(write_policy.format_guard(guard))
            return 2
    if args.install and not args.confirm_install:
        payload["install_blocked"] = {
            "blocked": True,
            "required_flag": "--confirm-install",
            "reason": "Installing recommended adapter skills writes outside the target repo and must be explicitly confirmed.",
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=True))
        else:
            print_recommendations(payload)
            print("")
            print("Install blocked: pass --confirm-install after reviewing the recommendation plan.")
        return 2
    if args.write_plan:
        payload["plan_path"] = str(write_recommendation_plan(Path(args.repo).resolve(), payload))
    if args.install:
        install_root = Path(args.skill_install_root) if args.skill_install_root else None
        payload["install_results"] = install_recommended_adapters(payload, install_root, args.force, args.replace_unmanaged)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print_recommendations(payload)
        if args.write_plan:
            print("")
            print(f"Recommendation plan written: {payload['plan_path']}")
        if args.install:
            print("")
            print("Installed adapter skills:")
            for result in payload["install_results"]:
                print(f"- {result['status']}: {result['skill']} -> {result['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
