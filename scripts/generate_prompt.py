#!/usr/bin/env python3
"""Generate codex-harness-setup prompts from simple human-involvement settings."""
from __future__ import annotations

import argparse
import json


def build_prompt(args: argparse.Namespace) -> str:
    modules = args.module or []
    phase = getattr(args, "phase", "active-development")
    human_involvement = getattr(args, "human_involvement", None)
    internal_ambiguity = getattr(args, "default_ambiguity", 3) if human_involvement is None else max(1, min(5, 6 - human_involvement))
    cadence = {
        "new-project": "initial setup now, again after the first working feature, then every 3-5 meaningful cycles",
        "prototype": "after structural/product/validation changes, otherwise every 3-5 cycles",
        "active-development": "lightweight fit check every task, short review every 3-5 meaningful cycles",
        "pre-release": "before release candidates, after QA failures, and whenever release validation changes",
        "maintenance": "monthly, after repeated mistakes, or before high-risk changes",
        "high-risk": "before planning, before implementation, and after validation",
    }.get(phase, "every 3-5 meaningful cycles")
    lines = [
        "Use the embedded codex-harness-setup skill from the repo-harness-tuner plugin.",
        "",
        f"Mode: {args.mode}",
        f"Repository type: {args.repo_type}",
        f"Project phase: {phase}",
        f"Human involvement: {human_involvement if human_involvement is not None else max(1, min(5, 6 - internal_ambiguity))}/5",
        f"Recommended harness tuning cadence: {cadence}",
        "",
        "Module overrides:",
    ]
    if modules:
        for item in modules:
            lines.append(f"- {item}")
    else:
        lines.append("- No module overrides provided.")
    lines.extend(
        [
            "",
            "Inspect existing AGENTS.md, Docs/AI/*, docs/ai/*, README, package scripts, CI/hooks, and project coordination docs.",
            "Create or update only the smallest useful repo-local harness.",
            "Prefer AGENTS.md, Docs/AI/harness-profile.md, and Docs/AI/validation.md when they reduce real future-agent risk.",
            "Do not add CI gates, release gates, dependencies, or destructive scripts without explicit approval.",
            "Treat this as the Design and Restructure step of the analyze -> diagnose -> design -> restructure -> evaluate loop.",
            "Design the harness first: identify target files, worker visibility, validation evidence, and the next review trigger before editing.",
            "",
            "Parallel work visibility policy:",
            f"- Visible chats: {args.visible_policy}",
            f"- Background workers: {args.background_policy}",
            "- Single agent is preferred for small, low-risk changes.",
            "",
            "Human involvement policy:",
            "- Human involvement 5: stop and ask for explicit approval before edits.",
            "- Human involvement 4: ask 1-3 focused questions before edits unless a named repo source of truth already answers them.",
            "- Human involvement 3: infer from repo context, but ask before hard-to-reverse or user-visible direction changes.",
            "- Human involvement 2: proceed from existing patterns; mention assumptions in closeout.",
            "- Human involvement 1: explore autonomously unless a protected area or explicit approval trigger appears.",
            "- Any row or rule marked Ask before is a stop condition before file edits.",
            "",
            "Close out with changed files, validation, skipped checks with reasons, and remaining risks.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", default="Setup", choices=["Audit only", "Setup", "Targeted upgrade", "Recovery", "Ambiguity profiling"])
    parser.add_argument("--repo-type", default="unknown")
    parser.add_argument("--phase", default="active-development", choices=["new-project", "prototype", "active-development", "pre-release", "maintenance", "high-risk"])
    parser.add_argument("--default-ambiguity", type=int, default=3, choices=[1, 2, 3, 4, 5], help="Compatibility fallback when --human-involvement is not set.")
    parser.add_argument("--human-involvement", type=int, choices=[1, 2, 3, 4, 5], help="User-facing intervention level: 1=minimal, 5=maximum.")
    parser.add_argument("--module", action="append", help="Module human-involvement override, for example 'Ending taxonomy: 5'.")
    parser.add_argument("--visible-policy", default="product decisions, roadmap changes, QA evidence, user-facing specialist work")
    parser.add_argument("--background-policy", default="read-only audits, code review, test review, security review, static scans")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    prompt = build_prompt(args)
    if args.json:
        print(json.dumps({"prompt": prompt}, indent=2, ensure_ascii=False))
    else:
        print(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
