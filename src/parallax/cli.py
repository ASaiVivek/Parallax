from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .catalog import load_catalog, select_perspectives
from .interview import apply_answers, assess_brief
from .models import DEFAULT_N, Brief
from .workspace import prepare_workspace, synthesize_workspace

app = typer.Typer(
    add_completion=False,
    help="Parallax — query-chosen isolated viewpoints, then one decision with dissent.",
)


def _echo_json(payload: object) -> None:
    if hasattr(payload, "model_dump"):
        typer.echo(payload.model_dump_json(indent=2))
    else:
        typer.echo(json.dumps(payload, indent=2))


def _load_brief(brief: Optional[Path], question: Optional[str]) -> Brief:
    if brief:
        return Brief.model_validate_json(brief.read_text(encoding="utf-8"))
    if question:
        return Brief(question=question)
    raise typer.BadParameter("Provide --brief or --question.")


def _apply_roster(
    brief: Brief,
    upto: Optional[int],
    exactly: Optional[int],
) -> Brief:
    if upto is not None and exactly is not None:
        raise typer.BadParameter("Use either --upto or --exactly, not both.")
    if exactly is not None:
        return brief.model_copy(update={"roster_mode": "exactly", "roster_n": exactly})
    if upto is not None:
        return brief.model_copy(update={"roster_mode": "upto", "roster_n": upto})
    return brief


@app.command("interview")
def interview_cmd(
    brief: Optional[Path] = typer.Option(None, help="Path to brief JSON."),
    question: Optional[str] = typer.Option(None, help="Question if you have no brief file yet."),
) -> None:
    """Return remaining interview questions. Ready=false means do not run perspectives yet."""
    result = assess_brief(_load_brief(brief, question))
    _echo_json(result)


@app.command("brief")
def brief_cmd(
    question: str = typer.Option(..., help="The decision or design question."),
    domain: Optional[str] = typer.Option(None),
    user_claim: Optional[str] = typer.Option(None, help="User's preferred answer, or 'none'."),
    constraint: list[str] = typer.Option([], "--constraint", help="Repeatable hard constraint."),
    criterion: list[str] = typer.Option([], "--criterion", help="Repeatable success criterion."),
    fact: list[str] = typer.Option([], "--fact"),
    unknown: list[str] = typer.Option([], "--unknown"),
    audience: Optional[str] = typer.Option(None),
    extra: list[str] = typer.Option([], "--extra", help="Force-include catalog ids."),
    upto: Optional[int] = typer.Option(None, help="At most N offsets (default)."),
    exactly: Optional[int] = typer.Option(None, help="Always N offsets."),
    out: Optional[Path] = typer.Option(None, help="Write brief JSON to this path."),
) -> None:
    """Create a brief. Use 'none' for user_claim when the requester has no preferred answer."""
    built = Brief(question=question)
    built = apply_answers(
        built,
        {
            "domain": domain,
            "user_claim": user_claim,
            "constraints": constraint,
            "success_criteria": criterion,
            "facts": fact,
            "unknowns": unknown,
            "audience": audience,
            "extra_perspective_ids": extra,
        },
    )
    built = _apply_roster(built, upto, exactly)
    text = built.model_dump_json(indent=2) + "\n"
    if out:
        out.write_text(text, encoding="utf-8")
    typer.echo(text, nl=False)


@app.command("select")
def select_cmd(
    question: str = typer.Option(...),
    domain: Optional[str] = typer.Option(None),
    extra: list[str] = typer.Option([], "--extra", help="Catalog ids to force-include."),
    upto: Optional[int] = typer.Option(None, help="Pick at most N offsets from the query (default 4)."),
    exactly: Optional[int] = typer.Option(None, help="Always pick exactly N offsets."),
    catalog: list[Path] = typer.Option([], "--catalog", help="Extra directory of offset JSON files."),
) -> None:
    """Show which isolated perspectives would run."""
    if upto is not None and exactly is not None:
        raise typer.BadParameter("Use either --upto or --exactly, not both.")
    if exactly is not None:
        mode, n = "exactly", exactly
    else:
        mode, n = "upto", upto if upto is not None else DEFAULT_N
    specs = select_perspectives(
        question,
        domain,
        extra_ids=extra,
        mode=mode,
        n=n,
        extra_dirs=catalog or None,
    )
    _echo_json([{"id": spec.id, "title": spec.title, "stance": spec.stance} for spec in specs])


@app.command("prepare")
def prepare_cmd(
    out: Path = typer.Option(..., help="Directory to write the isolated work package."),
    brief: Optional[Path] = typer.Option(None),
    question: Optional[str] = typer.Option(None),
    upto: Optional[int] = typer.Option(None, help="Pick at most N offsets (overrides the brief)."),
    exactly: Optional[int] = typer.Option(None, help="Always pick exactly N offsets."),
    catalog: list[Path] = typer.Option([], "--catalog", help="Extra directory of offset JSON files."),
    require_ready: bool = typer.Option(True, help="Refuse to prepare if interview gaps remain."),
) -> None:
    """Write isolated perspective packets. Each file is a complete, separate context."""
    loaded = _apply_roster(_load_brief(brief, question), upto, exactly)
    status = assess_brief(loaded)
    if require_ready and not status.ready:
        _echo_json({"error": "brief_not_ready", "interview": status.model_dump()})
        raise typer.Exit(code=2)
    dest = prepare_workspace(loaded, out, extra_dirs=catalog or None)
    _echo_json(
        {
            "ok": True,
            "work_dir": str(dest),
            "manifest": str(dest / "manifest.json"),
            "roster_mode": loaded.roster_mode,
            "roster_n": loaded.roster_n,
        }
    )


@app.command("synthesize")
def synthesize_cmd(
    work_dir: Path = typer.Argument(..., exists=True, file_okay=False),
) -> None:
    """Merge isolated reports into one decision with dissent. Also refreshes synthesis_prompt.md."""
    decision = synthesize_workspace(work_dir)
    _echo_json(decision)


@app.command("catalog")
def catalog_cmd(
    catalog: list[Path] = typer.Option([], "--catalog", help="Extra directory of offset JSON files."),
) -> None:
    """List perspective ids (builtin plus any drop-in catalogs)."""
    merged = load_catalog(catalog or None)
    _echo_json({pid: spec.model_dump() for pid, spec in merged.items()})


@app.callback()
def main() -> None:
    """Parallax CLI."""


if __name__ == "__main__":
    app()
