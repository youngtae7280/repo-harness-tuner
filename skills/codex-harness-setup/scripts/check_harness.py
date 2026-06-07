#!/usr/bin/env python3
"""Lint repository-local Codex harness files for common setup mistakes.

This helper checks applied repository files such as AGENTS.md and docs/ai/*.
It is intentionally conservative: it does not judge whether a harness is good,
but it catches common template and process mistakes.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\[(?:paths?|commands?|examples?|task types?|project-specific boundary|focused test command|broad command|browser/smoke command|typecheck command|what happened|missing/overhead/stale rule|add/remove/change|name|risk|reason|trigger|low/med/high|used/ignored|fresh/stale|keep/promote/demote/retire|caught issues / none|right/heavy/light|test/review|release/etc\.|irrelevant|review/evidence|change|area|paths or task signals|1-5|decisions requiring user input|safe inferred decisions|validation/review evidence|destructive/data/payment/auth/release triggers|preference-heavy or public-contract triggers|isolated low-risk work|exploration or prototype work|too many questions / too few / right)\]", re.IGNORECASE)
GENERIC_PLACEHOLDER_RE = re.compile(
    r"\b(?:TODO|TBD|REPLACE_ME|FILL_ME)\b|<[^>\n]*(?:path|command|example|todo)[^>\n]*>",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
OVERBROAD_RULES = [
    re.compile(r"\balways\s+run\s+all\s+tests\b", re.IGNORECASE),
    re.compile(r"\b(?:always|must)\s+run\s+(?:the\s+)?(?:entire|full|complete|all)\s+(?:test\s+)?suite(?:\s+for\s+every\s+change)?\b", re.IGNORECASE),
    re.compile(r"\balways\s+create\s+(?:a\s+)?full\s+report\b", re.IGNORECASE),
    re.compile(r"\b(?:always\s+)?(?:produce|create|write)\s+(?:a\s+)?(?:detailed|full|complete)\s+report\s+after\s+(?:each|every)\s+task\b", re.IGNORECASE),
    re.compile(r"\balways\s+create\s+(?:a\s+)?plan\s+before\s+(?:any|every)\s+change\b", re.IGNORECASE),
    re.compile(r"\balways\s+write\s+(?:a\s+)?long\s+plan\b", re.IGNORECASE),
    re.compile(r"\bnever\s+skip\s+(?:any\s+)?(?:full\s+)?validation\b", re.IGNORECASE),
    re.compile(r"\balways\s+(?:perform|do)\s+(?:exhaustive|full|complete)\s+(?:checks|validation)\b", re.IGNORECASE),
]
COMMAND_HINT_RE = re.compile(
    r"\b(npm|pnpm|yarn|bun|npx|node|deno|pytest|python|python3|uv|tox|go|cargo|mvn|gradle|make|just|ruff|eslint|tsc|vitest|jest|dotnet|msbuild|xcodebuild|ctest|Unity|Unity\.exe|UnityTestRunner)\b|(?:^|\s)-batchmode\b"
)
UNKNOWN_VALIDATION_RE = re.compile(
    r"\b(validation|test|command)s?\b.{0,40}\b(unknown|not available|manual only)\b|\b(unknown|not available|manual only)\b.{0,40}\b(validation|test|command)s?\b",
    re.IGNORECASE,
)


def harness_files(root: Path) -> list[Path]:
    files: list[Path] = []
    agents = root / "AGENTS.md"
    if agents.exists():
        files.append(agents)
    docs_ai = root / "docs" / "ai"
    if docs_ai.exists():
        files.extend(sorted(p for p in docs_ai.rglob("*.md") if p.is_file()))
    return files


def line_col(text: str, index: int) -> tuple[int, int]:
    before = text[:index]
    line = before.count("\n") + 1
    col = index - before.rfind("\n")
    return line, col


def check_placeholders(path: Path, text: str) -> list[str]:
    issues = []
    for pattern in (PLACEHOLDER_RE, GENERIC_PLACEHOLDER_RE):
        for match in pattern.finditer(text):
            line, col = line_col(text, match.start())
            issues.append(f"{path}:{line}:{col}: placeholder remains: {match.group(0)}")
    return issues


def check_duplicate_headings(path: Path, text: str) -> list[str]:
    seen: dict[tuple[int, str], int] = {}
    issues = []
    for lineno, line in enumerate(text.splitlines(), 1):
        match = HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        if level > 3:
            continue
        title = re.sub(r"\s+", " ", match.group(2).strip().lower())
        key = (level, title)
        if key in seen:
            issues.append(f"{path}:{lineno}: duplicate heading: {'#' * level} {title} (first seen at line {seen[key]})")
        else:
            seen[key] = lineno
    return issues


def check_overbroad_rules(path: Path, text: str) -> list[str]:
    issues = []
    for pattern in OVERBROAD_RULES:
        for match in pattern.finditer(text):
            line, col = line_col(text, match.start())
            issues.append(f"{path}:{line}:{col}: overbroad process rule: {match.group(0)!r}")
    return issues


def check_agents_length(root: Path) -> list[str]:
    agents = root / "AGENTS.md"
    if not agents.exists():
        return []
    lines = agents.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) > 250:
        return [f"{agents}:1: AGENTS.md is {len(lines)} lines; consider moving details to docs/ai/*"]
    return []


def check_validation_commands(root: Path) -> list[str]:
    validation = root / "docs" / "ai" / "validation.md"
    if not validation.exists():
        return []
    text = validation.read_text(encoding="utf-8", errors="replace")
    # Avoid passing on prose like "npm exists"; require command-like lines or explicit uncertainty.
    meaningful_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip().startswith(("-", "*", "|", "`")) or "`" in line or "$ " in line
    ]
    command_text = "\n".join(meaningful_lines)
    if not COMMAND_HINT_RE.search(command_text) and not UNKNOWN_VALIDATION_RE.search(text):
        return [f"{validation}:1: no obvious validation command found; add real repo-specific commands or state why unknown"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Check applied Codex harness docs for common mistakes.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository root to inspect")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    if not root.exists():
        print(f"error: repository path does not exist: {root}", file=sys.stderr)
        return 2

    files = harness_files(root)
    issues: list[str] = []
    issues.extend(check_agents_length(root))
    issues.extend(check_validation_commands(root))

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        issues.extend(check_placeholders(path, text))
        issues.extend(check_duplicate_headings(path, text))
        issues.extend(check_overbroad_rules(path, text))

    if issues:
        print("Harness check found issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    if files:
        print(f"Harness check passed ({len(files)} file(s) inspected).")
    else:
        print("Harness check passed (no AGENTS.md or docs/ai/*.md files found).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
