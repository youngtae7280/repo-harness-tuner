#!/usr/bin/env python3
"""Scan common local Codex plugin locations and marketplace metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def plugin_roots() -> list[Path]:
    home = Path.home()
    return [
        home / "plugins",
        home / ".codex" / "plugins" / "cache",
    ]


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - diagnostic scanner
        return {"_error": str(exc)}


def scan_plugins() -> list[dict[str, object]]:
    plugins: list[dict[str, object]] = []
    seen: set[Path] = set()
    for root in plugin_roots():
        if not root.exists():
            continue
        for manifest in root.rglob(".codex-plugin/plugin.json"):
            resolved = manifest.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            data = read_json(manifest)
            plugin_root = manifest.parent.parent
            plugins.append(
                {
                    "name": data.get("name") or plugin_root.name,
                    "version": data.get("version", ""),
                    "description": data.get("description", ""),
                    "display_name": data.get("interface", {}).get("displayName", ""),
                    "path": str(plugin_root),
                    "manifest": str(manifest),
                    "has_skills": (plugin_root / "skills").exists(),
                    "has_apps": bool(data.get("apps")),
                    "has_mcp": bool(data.get("mcpServers")),
                }
            )
    return sorted(plugins, key=lambda item: str(item["name"]).lower())


def scan_marketplace() -> dict[str, object]:
    path = Path.home() / ".agents" / "plugins" / "marketplace.json"
    if not path.exists():
        return {"path": str(path), "exists": False, "plugins": []}
    data = read_json(path)
    return {
        "path": str(path),
        "exists": True,
        "name": data.get("name", ""),
        "display_name": data.get("interface", {}).get("displayName", ""),
        "plugins": data.get("plugins", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    result = {"plugins": scan_plugins(), "marketplace": scan_marketplace()}
    result["count"] = len(result["plugins"])
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print(f"Plugins found: {result['count']}")
        for plugin in result["plugins"]:
            print(f"- {plugin['name']}: {plugin['path']}")
        marketplace = result["marketplace"]
        print(f"Marketplace: {marketplace['path']} exists={marketplace['exists']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
