"""Shared interview/prepare/synthesize operations used by the CLI and MCP wrapper.

Roster selection stays in catalog.select_perspectives via workspace.prepare_workspace.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from .interview import assess_brief
from .models import Brief
from .workspace import prepare_workspace, synthesize_workspace


class UsageError(ValueError):
    """Invalid caller input (missing brief/question, mutually exclusive flags)."""


@dataclass
class CommandResult:
    payload: object
    exit_code: int = 0


def load_brief(brief: Optional[Path], question: Optional[str]) -> Brief:
    if brief:
        return Brief.model_validate_json(brief.read_text(encoding="utf-8"))
    if question:
        return Brief(question=question)
    raise UsageError("Provide brief or question.")


def apply_roster(
    brief: Brief,
    upto: Optional[int],
    exactly: Optional[int],
) -> Brief:
    if upto is not None and exactly is not None:
        raise UsageError("Use either upto or exactly, not both.")
    if exactly is not None:
        return brief.model_copy(update={"roster_mode": "exactly", "roster_n": exactly})
    if upto is not None:
        return brief.model_copy(update={"roster_mode": "upto", "roster_n": upto})
    return brief


def interview(*, brief: Optional[Path] = None, question: Optional[str] = None) -> CommandResult:
    result = assess_brief(load_brief(brief, question))
    return CommandResult(payload=result)


def prepare(
    *,
    out: Path,
    brief: Optional[Path] = None,
    question: Optional[str] = None,
    upto: Optional[int] = None,
    exactly: Optional[int] = None,
    catalog: Sequence[Path] | None = None,
    require_ready: bool = True,
) -> CommandResult:
    loaded = apply_roster(load_brief(brief, question), upto, exactly)
    status = assess_brief(loaded)
    if require_ready and not status.ready:
        return CommandResult(
            payload={"error": "brief_not_ready", "interview": status.model_dump()},
            exit_code=2,
        )
    dest = prepare_workspace(loaded, out, extra_dirs=catalog or None)
    return CommandResult(
        payload={
            "ok": True,
            "work_dir": str(dest),
            "manifest": str(dest / "manifest.json"),
            "roster_mode": loaded.roster_mode,
            "roster_n": loaded.roster_n,
        }
    )


def synthesize(work_dir: Path) -> CommandResult:
    decision = synthesize_workspace(work_dir)
    return CommandResult(payload=decision)
