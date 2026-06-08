#!/usr/bin/env python3
"""Codex worker-architecture patterns for repo harness design."""
from __future__ import annotations

import argparse
import json
from typing import Any


PATTERNS: dict[str, dict[str, Any]] = {
    "single-agent": {
        "label": "Single Agent",
        "summary": "One Codex thread handles analysis, edits, and closeout.",
        "use_when": [
            "small, low-risk edits",
            "well-documented repo conventions",
            "no independent specialist review is likely to change the result",
        ],
        "visibility": "single thread",
        "coordination": "keep decisions in the main response",
        "evidence": ["changed files", "focused validation or skipped-check reason"],
        "avoid_when": ["high-risk work", "parallel review would materially reduce risk"],
    },
    "background-review": {
        "label": "Background Review",
        "summary": "Main thread implements; short-lived read-only worker reviews a focused risk.",
        "use_when": [
            "shared contracts, validation docs, or harness policy changed",
            "code/test/security review can be summarized without user participation",
            "the main thread needs independent findings, not collaboration",
        ],
        "visibility": "background/read-only",
        "coordination": "main thread owns edits; worker returns concise findings",
        "evidence": ["review findings with file references", "validation commands"],
        "avoid_when": ["subjective product direction", "approval-gated operations"],
    },
    "visible-decision-thread": {
        "label": "Visible Decision Thread",
        "summary": "Use a visible user-facing specialist thread for decisions the user should inspect.",
        "use_when": [
            "product, roadmap, UX, narrative, release, or scope decisions",
            "human involvement is high",
            "approval or tradeoff selection matters more than raw implementation speed",
        ],
        "visibility": "visible chat",
        "coordination": "ask or expose the decision before file edits",
        "evidence": ["decision summary", "chosen tradeoff", "remaining open risks"],
        "avoid_when": ["pure static scans", "tiny mechanical edits"],
    },
    "producer-reviewer": {
        "label": "Producer Reviewer",
        "summary": "One worker proposes or edits; another independently checks objective criteria.",
        "use_when": [
            "a generated harness file needs quality control",
            "objective review criteria exist",
            "a failed edit would be costly but reversible",
        ],
        "visibility": "main thread plus background reviewer",
        "coordination": "producer output is reviewed once; avoid retry loops unless explicit",
        "evidence": ["review checklist result", "accepted/rejected findings"],
        "avoid_when": ["no objective review criteria", "review would duplicate native tests"],
    },
    "fanout-review": {
        "label": "Fan-out Review",
        "summary": "Parallel read-only reviewers inspect different risk surfaces, then main thread merges findings.",
        "use_when": [
            "multiple independent risk surfaces exist",
            "security, validation, UI, data, or release concerns can be separated",
            "parallel findings are useful and bounded",
        ],
        "visibility": "background/read-only by default",
        "coordination": "main thread assigns bounded scopes and merges conflicts",
        "evidence": ["per-scope findings", "merged priority list", "skipped scopes with reasons"],
        "avoid_when": ["small tasks", "review scopes overlap heavily", "token cost outweighs risk reduction"],
    },
    "supervisor-cycle": {
        "label": "Supervisor Cycle",
        "summary": "Main thread acts as coordinator for a staged, multi-slice harness improvement cycle.",
        "use_when": [
            "large or repeated harness failures need staged repair",
            "work spans discovery, restructuring, validation, and follow-up",
            "task boundaries must be kept reviewable",
        ],
        "visibility": "main visible coordinator plus optional background workers",
        "coordination": "main thread owns task board, sequencing, and final acceptance",
        "evidence": ["stage status", "worker summaries", "final validation"],
        "avoid_when": ["single-pass setup", "no repeated failure evidence"],
    },
    "phase-handoff": {
        "label": "Phase Handoff",
        "summary": "Separate phases preserve artifacts so later workers can continue without rereading everything.",
        "use_when": [
            "long-running harness work must survive context transitions",
            "analysis, design, edit, and evaluation need separate artifacts",
            "future sessions must reuse decisions",
        ],
        "visibility": "visible summaries, background execution where safe",
        "coordination": "persist concise artifacts before switching phase",
        "evidence": ["harness-design-plan.md", "harness-status.md", "history or flaw records"],
        "avoid_when": ["short tasks where persistent artifacts are noise"],
    },
}


def list_patterns() -> list[dict[str, Any]]:
    return [{"id": key, **value} for key, value in PATTERNS.items()]


def get_pattern(pattern_id: str) -> dict[str, Any]:
    if pattern_id not in PATTERNS:
        choices = ", ".join(sorted(PATTERNS))
        raise ValueError(f"Unknown worker pattern: {pattern_id}. Choices: {choices}")
    return {"id": pattern_id, **PATTERNS[pattern_id]}


def build_worker_prompt(
    pattern_id: str,
    repo: str = ".",
    phase: str = "active-development",
    scope: str = "repo harness tuning",
    human_involvement: int | None = None,
) -> str:
    pattern = get_pattern(pattern_id)
    lines = [
        "You are a Codex worker participating in repo harness tuning.",
        "",
        f"Repository: {repo}",
        f"Project phase: {phase}",
        f"Worker pattern: {pattern['label']} (`{pattern['id']}`)",
        f"Visibility: {pattern['visibility']}",
        f"Coordination: {pattern['coordination']}",
        f"Scope: {scope}",
    ]
    if human_involvement is not None:
        lines.append(f"Human involvement: {max(1, min(5, human_involvement))}/5")
    lines.extend(
        [
            "",
            "Instructions:",
            "- Stay within the assigned scope and avoid broad repo rewrites.",
            "- Prefer read-only analysis unless this prompt explicitly asks you to edit.",
            "- Return concise findings, decisions, or evidence that the main thread can merge.",
            "- If your work touches product direction, release gates, destructive operations, dependencies, secrets, or privacy-sensitive areas, stop and mark it as needing visible user approval.",
            "",
            "Use when:",
        ]
    )
    lines.extend(f"- {item}" for item in pattern["use_when"])
    lines.extend(["", "Expected evidence:"])
    lines.extend(f"- {item}" for item in pattern["evidence"])
    lines.extend(["", "Avoid this pattern when:"])
    lines.extend(f"- {item}" for item in pattern["avoid_when"])
    return "\n".join(lines)


def select_pattern(
    *,
    phase: str,
    human_involvement: int,
    readiness_score: int,
    needs_restructure: bool,
    drift_count: int,
    overhead_count: int,
    enforcement_count: int,
    project_type: str,
) -> dict[str, Any]:
    reasons: list[str] = []

    if phase == "high-risk" or human_involvement >= 5:
        pattern_id = "visible-decision-thread"
        reasons.append("high-risk phase or maximum human involvement requires visible approval points")
    elif overhead_count:
        pattern_id = "single-agent"
        reasons.append("overbroad process was detected, so the repair should avoid adding more coordination overhead")
    elif readiness_score < 60 and needs_restructure:
        pattern_id = "supervisor-cycle"
        reasons.append("low readiness plus required restructuring needs a staged coordinator")
    elif drift_count and needs_restructure:
        pattern_id = "producer-reviewer"
        reasons.append("validation or skills drift benefits from one focused repair plus independent review")
    elif enforcement_count or human_involvement >= 4:
        pattern_id = "visible-decision-thread"
        reasons.append("human-involvement policy needs visible ask-before-edit behavior")
    elif needs_restructure and readiness_score < 85:
        pattern_id = "background-review"
        reasons.append("moderate harness repair benefits from a short read-only review")
    elif phase in {"pre-release", "maintenance"} and needs_restructure:
        pattern_id = "producer-reviewer"
        reasons.append("release or maintenance changes should have objective review evidence")
    elif project_type in {"unity", "godot", "vite-node"} and needs_restructure:
        pattern_id = "background-review"
        reasons.append("user-visible project surfaces benefit from focused review without a full team")
    else:
        pattern_id = "single-agent"
        reasons.append("current harness is fit enough for a single-thread loop")

    pattern = {"id": pattern_id, **PATTERNS[pattern_id]}
    pattern["selection_reasons"] = reasons
    pattern["fallback_patterns"] = fallback_patterns(pattern_id, human_involvement, needs_restructure)
    return pattern


def fallback_patterns(pattern_id: str, human_involvement: int, needs_restructure: bool) -> list[str]:
    fallbacks: list[str] = []
    if pattern_id != "single-agent":
        fallbacks.append("single-agent")
    if pattern_id != "background-review" and needs_restructure:
        fallbacks.append("background-review")
    if pattern_id != "visible-decision-thread" and human_involvement >= 4:
        fallbacks.append("visible-decision-thread")
    return fallbacks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", help="Build an assignment prompt for a specific pattern id.")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--phase", default="active-development")
    parser.add_argument("--scope", default="repo harness tuning")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.prompt:
        prompt = build_worker_prompt(args.prompt, args.repo, args.phase, args.scope, args.human_involvement)
        payload = {"pattern": get_pattern(args.prompt), "prompt": prompt}
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=True))
        else:
            print(prompt)
        return 0
    payload = {"patterns": list_patterns(), "count": len(PATTERNS)}
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(f"Worker patterns: {payload['count']}")
        for pattern in payload["patterns"]:
            print(f"- {pattern['id']}: {pattern['label']} - {pattern['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
