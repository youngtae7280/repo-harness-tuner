#!/usr/bin/env python3
"""Shared storage and feedback helpers for repo harness history."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA = "repo-harness-tuner.history.v1"
FAILURE_KEYWORDS = ("failure", "failed", "regression", "miss", "mistake", "blocked", "broken")


def history_path(root: Path) -> Path:
    return root / "Docs" / "AI" / "harness-history.jsonl"


def load_history(root: Path) -> list[dict[str, Any]]:
    path = history_path(root)
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            entries.append({"type": "parse-error", "raw": line})
    return entries


def valid_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [entry for entry in entries if entry.get("schema") == SCHEMA]


def summarize(entries: list[dict[str, Any]]) -> dict[str, Any]:
    valid = valid_entries(entries)
    latest = valid[-1] if valid else None
    by_type: dict[str, int] = {}
    by_pattern: dict[str, int] = {}
    readiness_values: list[int] = []
    totals = {
        "drift_count": 0,
        "process_overhead_count": 0,
        "human_involvement_gap_count": 0,
    }
    for entry in valid:
        by_type[str(entry.get("type", "unknown"))] = by_type.get(str(entry.get("type", "unknown")), 0) + 1
        by_pattern[str(entry.get("worker_pattern", "unknown"))] = by_pattern.get(str(entry.get("worker_pattern", "unknown")), 0) + 1
        if isinstance(entry.get("readiness"), int):
            readiness_values.append(int(entry["readiness"]))
        for key in totals:
            value = entry.get(key)
            if isinstance(value, int):
                totals[key] += value
    return {
        "count": len(valid),
        "parse_errors": len(entries) - len(valid),
        "by_type": by_type,
        "by_worker_pattern": by_pattern,
        "latest": latest,
        "readiness_min": min(readiness_values) if readiness_values else None,
        "readiness_max": max(readiness_values) if readiness_values else None,
        "readiness_latest": readiness_values[-1] if readiness_values else None,
        "readiness_values": readiness_values,
        "totals": totals,
    }


def has_failure_note(entry: dict[str, Any]) -> bool:
    text = f"{entry.get('type', '')} {entry.get('note', '')}".lower()
    return any(keyword in text for keyword in FAILURE_KEYWORDS)


def build_feedback(root: Path, window: int = 5) -> dict[str, Any]:
    entries = load_history(root)
    summary = summarize(entries)
    valid = valid_entries(entries)
    recent = valid[-window:]
    signals: list[dict[str, str]] = []
    recommendations: list[str] = []

    if not valid:
        return {
            "history_path": str(history_path(root)),
            "count": 0,
            "review_pressure": "normal",
            "signals": signals,
            "recommendations": recommendations,
            "latest": None,
            "readiness_latest": None,
            "readiness_max": None,
        }

    latest = valid[-1]
    readiness_values = [int(entry["readiness"]) for entry in valid if isinstance(entry.get("readiness"), int)]
    previous_values = readiness_values[:-1]
    latest_readiness = readiness_values[-1] if readiness_values else None
    previous_max = max(previous_values) if previous_values else None
    if latest_readiness is not None and previous_max is not None and latest_readiness <= previous_max - 5:
        signals.append(
            {
                "type": "readiness-regression",
                "detail": f"Latest readiness {latest_readiness}/100 is below prior best {previous_max}/100.",
            }
        )
        recommendations.append("Treat the next harness change as a repair cycle because readiness regressed versus prior history.")

    if len(readiness_values) >= 3 and readiness_values[-1] < readiness_values[-3]:
        signals.append(
            {
                "type": "declining-readiness-trend",
                "detail": f"Readiness moved from {readiness_values[-3]}/100 to {readiness_values[-1]}/100 across the latest snapshots.",
            }
        )
        recommendations.append("Shorten the next review interval and verify whether recent project changes made the harness stale.")

    repeated_checks = [
        (
            "drift_count",
            "repeated-validation-drift",
            "Validation drift appeared in multiple recent history entries.",
            "Update validation guidance and record which native commands are authoritative.",
        ),
        (
            "process_overhead_count",
            "repeated-process-overhead",
            "Process overhead appeared in multiple recent history entries.",
            "Demote always-on reports, plans, visible chats, or full validation into risk-triggered guidance.",
        ),
        (
            "human_involvement_gap_count",
            "repeated-human-involvement-gap",
            "Human-involvement enforcement gaps appeared in multiple recent history entries.",
            "Strengthen ask-before-edit rules and link them from AGENTS.md.",
        ),
    ]
    for key, signal_type, detail, recommendation in repeated_checks:
        repeated = sum(1 for entry in recent if isinstance(entry.get(key), int) and int(entry[key]) > 0)
        if repeated >= 2:
            signals.append({"type": signal_type, "detail": detail})
            recommendations.append(recommendation)

    if any(has_failure_note(entry) for entry in recent):
        signals.append(
            {
                "type": "recent-failure-note",
                "detail": "Recent history notes mention a failure, regression, miss, or blocked harness cycle.",
            }
        )
        recommendations.append("Use a visible decision or reviewer checkpoint for the next harness repair.")

    pressure = "normal"
    signal_types = {signal["type"] for signal in signals}
    if {"readiness-regression", "declining-readiness-trend", "recent-failure-note"} & signal_types:
        pressure = "high"
    elif signals:
        pressure = "elevated"

    return {
        "history_path": str(history_path(root)),
        "count": summary["count"],
        "parse_errors": summary["parse_errors"],
        "review_pressure": pressure,
        "signals": signals,
        "recommendations": dedupe(recommendations),
        "latest": latest,
        "readiness_latest": summary["readiness_latest"],
        "readiness_max": summary["readiness_max"],
        "by_worker_pattern": summary["by_worker_pattern"],
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
