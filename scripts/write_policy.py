#!/usr/bin/env python3
"""Human-involvement write guards for repo harness commands."""
from __future__ import annotations

from typing import Any


DEFAULT_HUMAN_INVOLVEMENT_BY_PHASE = {
    "new-project": 3,
    "prototype": 2,
    "active-development": 3,
    "pre-release": 4,
    "maintenance": 3,
    "high-risk": 5,
}


def effective_human_involvement(phase: str, human_involvement: int | None = None) -> int:
    if human_involvement is not None:
        return max(1, min(5, int(human_involvement)))
    return DEFAULT_HUMAN_INVOLVEMENT_BY_PHASE.get(phase, 3)


def write_guard(command: str, phase: str, human_involvement: int | None, confirm_write: bool) -> dict[str, Any] | None:
    effective = effective_human_involvement(phase, human_involvement)
    if effective < 4 or confirm_write:
        return None
    return {
        "blocked": True,
        "command": command,
        "phase": phase,
        "effective_human_involvement": effective,
        "required_flag": "--confirm-write",
        "reason": (
            "Human involvement is 4 or 5, so this write must be explicitly confirmed. "
            "Review the dry-run/diff output first, then rerun with --confirm-write if the file changes are approved."
        ),
    }


def format_guard(guard: dict[str, Any]) -> str:
    return (
        f"Write blocked for `{guard['command']}`: {guard['reason']} "
        f"(phase={guard['phase']}, human involvement={guard['effective_human_involvement']}/5, "
        f"required={guard['required_flag']})"
    )
