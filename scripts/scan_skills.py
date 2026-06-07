#!/usr/bin/env python3
"""Scan common local Codex skill locations."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def skill_roots() -> list[Path]:
    home = Path.home()
    roots = [
        home / ".codex" / "skills",
        home / ".codex" / "skills" / ".system",
        home / ".codex" / "plugins" / "cache",
        home / "plugins",
    ]
    env_roots = os.environ.get("CODEX_SKILL_PATHS", "")
    for entry in env_roots.split(os.pathsep):
        if entry:
            roots.append(Path(entry))
    return roots


def scan() -> list[dict[str, object]]:
    seen: set[Path] = set()
    skills: list[dict[str, object]] = []
    for root in skill_roots():
        if not root.exists():
            continue
        for skill_file in root.rglob("SKILL.md"):
            try:
                resolved = skill_file.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            text = skill_file.read_text(encoding="utf-8", errors="replace")
            meta = parse_frontmatter(text)
            skills.append(
                {
                    "name": meta.get("name") or skill_file.parent.name,
                    "description": meta.get("description", ""),
                    "path": str(skill_file),
                    "plugin_or_root": str(root),
                    "size_bytes": skill_file.stat().st_size,
                }
            )
    return sorted(skills, key=lambda item: str(item["name"]).lower())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    skills = scan()
    if args.json:
        print(json.dumps({"skills": skills, "count": len(skills)}, indent=2, ensure_ascii=False))
    else:
        print(f"Skills found: {len(skills)}")
        for skill in skills:
            print(f"- {skill['name']}: {skill['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
