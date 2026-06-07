#!/usr/bin/env python3
"""Scan a repository for Codex harness files and validation hints."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


HARNESS_PATHS = [
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
    "Docs/AI/harness-profile.md",
    "Docs/AI/ambiguity-profile.md",
    "Docs/AI/validation.md",
    "Docs/AI/project-map.md",
    "Docs/SKILLS.md",
    "docs/ai/harness-profile.md",
    "docs/ai/ambiguity-profile.md",
    "docs/ai/validation.md",
    "docs/ai/project-map.md",
    "README.md",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "ProjectSettings/ProjectVersion.txt",
    "Packages/manifest.json",
    "project.godot",
    "vite.config.js",
    "vite.config.ts",
]


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - diagnostic scanner
        return {"_error": str(exc)}


def detect_project_type(root: Path, package: dict | None = None) -> dict[str, object]:
    package = package or {}
    scripts = package.get("scripts", {}) if isinstance(package.get("scripts", {}), dict) else {}
    deps: dict[str, object] = {}
    for key in ["dependencies", "devDependencies"]:
        value = package.get(key, {})
        if isinstance(value, dict):
            deps.update(value)

    markers: list[str] = []
    project_type = "unknown"

    if (root / "ProjectSettings").exists() and (root / "Assets").exists():
        project_type = "unity"
        markers.extend(["Assets/", "ProjectSettings/"])
        if (root / "Packages" / "manifest.json").exists():
            markers.append("Packages/manifest.json")
    elif (root / "project.godot").exists():
        project_type = "godot"
        markers.append("project.godot")
    elif (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        project_type = "python"
        if (root / "pyproject.toml").exists():
            markers.append("pyproject.toml")
        if (root / "requirements.txt").exists():
            markers.append("requirements.txt")
    elif (root / "package.json").exists():
        if "vite" in deps or (root / "vite.config.ts").exists() or (root / "vite.config.js").exists():
            project_type = "vite-node"
            markers.append("vite")
        else:
            project_type = "node"
        markers.append("package.json")
        markers.extend([f"script:{name}" for name in sorted(scripts)])

    if project_type == "unknown":
        md_files = list(root.glob("*.md")) + list((root / "Docs").glob("**/*.md") if (root / "Docs").exists() else [])
        if md_files and not scripts:
            project_type = "docs-only"
            markers.append("markdown-docs")

    return {"project_type": project_type, "project_markers": markers}


def scan(root: Path) -> dict[str, object]:
    root = root.resolve()
    files = []
    seen_paths: set[Path] = set()
    for rel in HARNESS_PATHS:
        path = root / rel
        if path.exists():
            resolved = path.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            files.append(
                {
                    "path": str(path.relative_to(root)),
                    "size_bytes": path.stat().st_size,
                    "lines": len(path.read_text(encoding="utf-8", errors="replace").splitlines())
                    if path.suffix.lower() in {".md", ".json"}
                    else None,
                }
            )

    package_path = root / "package.json"
    package: dict = {}
    scripts = {}
    if package_path.exists():
        package = read_json(package_path)
        scripts = package.get("scripts", {}) if isinstance(package.get("scripts", {}), dict) else {}

    docs_reports = root / "Docs" / "Reports"
    report_count = len(list(docs_reports.glob("*"))) if docs_reports.exists() else 0

    missing_recommended = [
        rel
        for rel in ["AGENTS.md", "Docs/AI/harness-profile.md", "Docs/AI/ambiguity-profile.md", "Docs/AI/validation.md"]
        if not (root / rel).exists() and not (root / rel.replace("Docs/AI", "docs/ai")).exists()
    ]

    project = detect_project_type(root, package)

    return {
        "root": str(root),
        "project_type": project["project_type"],
        "project_markers": project["project_markers"],
        "files": files,
        "package_scripts": scripts,
        "docs_reports_count": report_count,
        "missing_recommended": missing_recommended,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", default=".", help="Repository root to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    result = scan(Path(args.repo_root))
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Repo: {result['root']}")
        print(f"Project type: {result['project_type']}")
        if result["project_markers"]:
            print("Project markers:")
            for marker in result["project_markers"]:
                print(f"- {marker}")
        print("Harness files:")
        for file in result["files"]:
            print(f"- {file['path']} ({file['lines']} lines)")
        if result["missing_recommended"]:
            print("Missing recommended:")
            for rel in result["missing_recommended"]:
                print(f"- {rel}")
        scripts = result["package_scripts"]
        if scripts:
            print("Package scripts:")
            for name, command in scripts.items():
                print(f"- {name}: {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
