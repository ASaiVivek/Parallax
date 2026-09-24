"""Shared interview/prepare/synthesize operations used by the CLI and MCP wrapper.

Roster selection stays in catalog.select_perspectives via workspace.prepare_workspace.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from .interview import apply_answers, assess_brief
from .models import Brief
from .workspace import ReportLoadError, prepare_workspace, synthesize_workspace


class UsageError(ValueError):
    """Invalid caller input (missing brief/question, mutually exclusive flags)."""


@dataclass
class CommandResult:
    payload: object
    exit_code: int = 0


def load_brief(brief: Optional[Path], question: Optional[str]) -> Brief:
    if brief:
        if not brief.is_file():
            raise UsageError(f"Brief file not found: {brief}")
        try:
            return Brief.model_validate_json(brief.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise UsageError(f"Invalid brief JSON: {exc}") from exc
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


def write_brief(
    *,
    question: str,
    domain: Optional[str] = None,
    user_claim: Optional[str] = None,
    constraints: Sequence[str] | None = None,
    success_criteria: Sequence[str] | None = None,
    facts: Sequence[str] | None = None,
    unknowns: Sequence[str] | None = None,
    audience: Optional[str] = None,
    extra_perspective_ids: Sequence[str] | None = None,
    upto: Optional[int] = None,
    exactly: Optional[int] = None,
    out: Optional[Path] = None,
) -> CommandResult:
    built = apply_answers(
        Brief(question=question),
        {
            "domain": domain,
            "user_claim": user_claim,
            "constraints": list(constraints or []),
            "success_criteria": list(success_criteria or []),
            "facts": list(facts or []),
            "unknowns": list(unknowns or []),
            "audience": audience,
            "extra_perspective_ids": list(extra_perspective_ids or []),
        },
    )
    built = apply_roster(built, upto, exactly)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(built.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return CommandResult(payload=built)


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
    dest = dest.resolve()
    packets = sorted((dest / "perspectives").glob("*.md"))
    perspectives = []
    for path in packets:
        stem = path.stem
        pid = stem.split("-", 1)[1] if "-" in stem else stem
        perspectives.append(
            {
                "id": pid,
                "filename": path.name,
                "path": str(path),
                "report": str(dest / "reports" / f"{pid}.json"),
            }
        )
    return CommandResult(
        payload={
            "ok": True,
            "work_dir": str(dest),
            "manifest": str(dest / "manifest.json"),
            "roster_mode": loaded.roster_mode,
            "roster_n": loaded.roster_n,
            "perspectives": perspectives,
            "next": (
                "Run each perspectives/*.md file in a fresh context. "
                "Write reports/<id>.json (not the 01-id.md stem). Then synthesize."
            ),
        }
    )


def synthesize(work_dir: Path) -> CommandResult:
    if not work_dir.is_dir():
        raise UsageError(f"Work directory not found: {work_dir}")
    if not (work_dir / "brief.json").is_file():
        raise UsageError(f"brief.json not found in {work_dir}")
    try:
        decision = synthesize_workspace(work_dir)
    except ReportLoadError as exc:
        raise UsageError(str(exc)) from exc
    return CommandResult(payload=decision)
