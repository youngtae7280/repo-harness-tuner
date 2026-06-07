#!/usr/bin/env python3
"""Shared storage and feedback helpers for repo harness history."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA = "repo-harness-tuner.history.v1"
EVAL_SCHEMA = "repo-harness-tuner.eval-score.v1"
FAILURE_KEYWORDS = ("failure", "failed", "regression", "miss", "mistake", "blocked", "broken")


def history_path(root: Path) -> Path:
    return root / "Docs" / "AI" / "harness-history.jsonl"


def eval_results_path(root: Path) -> Path:
    return root / "Docs" / "AI" / "harness-eval-results.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
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


def load_history(root: Path) -> list[dict[str, Any]]:
    return load_jsonl(history_path(root))


def load_eval_scores(root: Path) -> list[dict[str, Any]]:
    return load_jsonl(eval_results_path(root))


def valid_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [entry for entry in entries if entry.get("schema") == SCHEMA]


def valid_eval_scores(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [entry for entry in entries if entry.get("schema") == EVAL_SCHEMA]


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


def summarize_eval_scores(entries: list[dict[str, Any]]) -> dict[str, Any]:
    valid = valid_eval_scores(entries)
    latest = valid[-1] if valid else None
    totals = {
        "tasks": 0,
        "assertions": 0,
        "baseline_pass": 0,
        "with_harness_pass": 0,
        "improved": 0,
        "regressed": 0,
        "unchanged_pass": 0,
        "unchanged_fail": 0,
        "not_applicable": 0,
    }
    decisions: dict[str, int] = {}
    net_values: list[int] = []
    for entry in valid:
        entry_totals = entry.get("totals", {})
        if isinstance(entry_totals, dict):
            for key in totals:
                value = entry_totals.get(key)
                if isinstance(value, int):
                    totals[key] += value
        recommendation = str(entry.get("recommendation") or "unknown")
        decisions[recommendation] = decisions.get(recommendation, 0) + 1
        if isinstance(entry.get("net_improvement"), int):
            net_values.append(int(entry["net_improvement"]))
    latest_totals = latest.get("totals", {}) if isinstance(latest, dict) else {}
    return {
        "count": len(valid),
        "parse_errors": len(entries) - len(valid),
        "latest": latest,
        "latest_totals": latest_totals if isinstance(latest_totals, dict) else {},
        "totals": totals,
        "by_recommendation": decisions,
        "net_improvement_latest": net_values[-1] if net_values else None,
        "net_improvement_total": sum(net_values),
    }


def has_failure_note(entry: dict[str, Any]) -> bool:
    text = f"{entry.get('type', '')} {entry.get('note', '')}".lower()
    return any(keyword in text for keyword in FAILURE_KEYWORDS)


def add_eval_feedback(eval_summary: dict[str, Any], signals: list[dict[str, str]], recommendations: list[str]) -> None:
    if not eval_summary.get("count"):
        return
    latest_totals = eval_summary.get("latest_totals", {})
    regressed = int(latest_totals.get("regressed", 0) or 0)
    unchanged_fail = int(latest_totals.get("unchanged_fail", 0) or 0)
    improved = int(latest_totals.get("improved", 0) or 0)
    assertions = int(latest_totals.get("assertions", 0) or 0)

    if regressed:
        signals.append(
            {
                "type": "eval-regression",
                "detail": f"Latest eval score regressed on {regressed} of {assertions} assertion(s).",
            }
        )
        recommendations.append("Revise the harness before promoting the last team, skill, or process change.")
    if unchanged_fail:
        signals.append(
            {
                "type": "eval-unchanged-fail",
                "detail": f"Latest eval score left {unchanged_fail} assertion(s) failing versus the baseline.",
            }
        )
        recommendations.append("Tune the harness around the failed eval assertions and rerun the same golden task.")
    if improved and not regressed and not unchanged_fail:
        signals.append(
            {
                "type": "eval-improvement",
                "detail": f"Latest eval score improved {improved} assertion(s) without regressions.",
            }
        )
        recommendations.append("Keep the current harness direction, record history, and watch for repeated overhead.")


def build_feedback(root: Path, window: int = 5) -> dict[str, Any]:
    entries = load_history(root)
    eval_entries = load_eval_scores(root)
    summary = summarize(entries)
    eval_summary = summarize_eval_scores(eval_entries)
    valid = valid_entries(entries)
    recent = valid[-window:]
    signals: list[dict[str, str]] = []
    recommendations: list[str] = []

    latest = valid[-1] if valid else None
    if valid:
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

    add_eval_feedback(eval_summary, signals, recommendations)

    pressure = "normal"
    signal_types = {signal["type"] for signal in signals}
    if {"readiness-regression", "declining-readiness-trend", "recent-failure-note", "eval-regression"} & signal_types:
        pressure = "high"
    elif signals:
        pressure = "elevated"

    return {
        "history_path": str(history_path(root)),
        "eval_path": str(eval_results_path(root)),
        "count": summary["count"],
        "eval_score_records": eval_summary["count"],
        "parse_errors": summary["parse_errors"] + eval_summary["parse_errors"],
        "history_parse_errors": summary["parse_errors"],
        "eval_parse_errors": eval_summary["parse_errors"],
        "review_pressure": pressure,
        "signals": signals,
        "recommendations": dedupe(recommendations),
        "latest": latest,
        "eval_latest": eval_summary["latest"],
        "eval_totals": eval_summary["totals"],
        "readiness_latest": summary["readiness_latest"],
        "readiness_max": summary["readiness_max"],
        "by_worker_pattern": summary["by_worker_pattern"],
        "closed_loop": {
            "uses_history": summary["count"] > 0,
            "uses_eval_scores": eval_summary["count"] > 0,
            "history_signal_count": sum(1 for signal in signals if not signal["type"].startswith("eval-")),
            "eval_signal_count": sum(1 for signal in signals if signal["type"].startswith("eval-")),
            "signal_count": len(signals),
        },
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
