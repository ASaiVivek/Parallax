from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .catalog import load_catalog, select_perspectives
from .commands import UsageError, apply_roster, interview, prepare, synthesize
from .interview import apply_answers
from .models import DEFAULT_N, Brief

app = typer.Typer(
    add_completion=False,
    help="Parallax — query-chosen isolated viewpoints, then one decision with dissent.",
)


def _echo_json(payload: object) -> None:
    if hasattr(payload, "model_dump"):
        typer.echo(payload.model_dump_json(indent=2))
    else:
        typer.echo(json.dumps(payload, indent=2))


def _emit(result) -> None:
    _echo_json(result.payload)
    if result.exit_code:
        raise typer.Exit(code=result.exit_code)


@app.command("interview")
def interview_cmd(
    brief: Optional[Path] = typer.Option(None, help="Path to brief JSON."),
    question: Optional[str] = typer.Option(None, help="Question if you have no brief file yet."),
) -> None:
    """Return remaining interview questions. Ready=false means do not run perspectives yet."""
    try:
        _emit(interview(brief=brief, question=question))
    except UsageError as exc:
        raise typer.BadParameter(str(exc)) from exc


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
    try:
        built = apply_roster(built, upto, exactly)
    except UsageError as exc:
        raise typer.BadParameter(str(exc)) from exc
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
    try:
        _emit(
            prepare(
                out=out,
                brief=brief,
                question=question,
                upto=upto,
                exactly=exactly,
                catalog=catalog or None,
                require_ready=require_ready,
            )
        )
    except UsageError as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command("synthesize")
def synthesize_cmd(
    work_dir: Path = typer.Argument(..., exists=True, file_okay=False),
) -> None:
    """Merge isolated reports into one decision with dissent. Also refreshes synthesis_prompt.md."""
    _emit(synthesize(work_dir))


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
