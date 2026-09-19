"""Local stdio MCP wrapper around Parallax CLI operations.

Does not call models. Does not reimplement roster selection. Hosts still run
each perspectives/*.md file in a fresh context, then call synthesize.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .commands import UsageError, interview, prepare, synthesize


def _json(payload: object) -> str:
    if hasattr(payload, "model_dump_json"):
        return payload.model_dump_json(indent=2)
    return json.dumps(payload, indent=2)


def _paths(catalog: Optional[list[str]]) -> list[Path] | None:
    if not catalog:
        return None
    return [Path(item) for item in catalog]


def interview_tool(question: Optional[str] = None, brief: Optional[str] = None) -> str:
    """Return remaining interview gaps. Ready=false means do not prepare yet."""
    try:
        result = interview(
            brief=Path(brief) if brief else None,
            question=question,
        )
    except UsageError as exc:
        return _json({"error": "usage", "message": str(exc)})
    return _json(result.payload)


def prepare_tool(
    out: str,
    brief: Optional[str] = None,
    question: Optional[str] = None,
    upto: Optional[int] = None,
    exactly: Optional[int] = None,
    catalog: Optional[list[str]] = None,
    require_ready: bool = True,
) -> str:
    """Write isolated perspective packets. Does not run models."""
    try:
        result = prepare(
            out=Path(out),
            brief=Path(brief) if brief else None,
            question=question,
            upto=upto,
            exactly=exactly,
            catalog=_paths(catalog),
            require_ready=require_ready,
        )
    except UsageError as exc:
        return _json({"error": "usage", "message": str(exc)})
    return _json(result.payload)


def synthesize_tool(work_dir: str) -> str:
    """Merge isolated reports into one decision with dissent."""
    try:
        result = synthesize(Path(work_dir))
    except UsageError as exc:
        return _json({"error": "usage", "message": str(exc)})
    return _json(result.payload)


def create_server():
    """Build the stdio FastMCP server. Requires the optional `mcp` extra."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - exercised when extra missing
        raise SystemExit(
            "Parallax MCP needs the optional extra. Install with "
            "`uv sync --extra mcp` or `pip install 'parallax[mcp]'`."
        ) from exc

    server = FastMCP(
        "parallax",
        instructions=(
            "Local Parallax wrapper. Tools wrap the parallax CLI only. "
            "Do not run every offset in one model context. After prepare, "
            "the host must run each perspectives/*.md file in a fresh session "
            "and write reports/<id>.json, then call synthesize. "
            "Pushing GitHub does not update this process; reload after upgrade."
        ),
    )

    @server.tool(name="parallax_interview")
    def parallax_interview(question: Optional[str] = None, brief: Optional[str] = None) -> str:
        """Return remaining interview questions before isolated work may start."""
        return interview_tool(question=question, brief=brief)

    @server.tool(name="parallax_prepare")
    def parallax_prepare(
        out: str,
        brief: Optional[str] = None,
        question: Optional[str] = None,
        upto: Optional[int] = None,
        exactly: Optional[int] = None,
        catalog: Optional[list[str]] = None,
        require_ready: bool = True,
    ) -> str:
        """Materialize isolated packets. Host still runs one fresh context per file."""
        return prepare_tool(
            out=out,
            brief=brief,
            question=question,
            upto=upto,
            exactly=exactly,
            catalog=catalog,
            require_ready=require_ready,
        )

    @server.tool(name="parallax_synthesize")
    def parallax_synthesize(work_dir: str) -> str:
        """Heuristic merge of reports into one decision with dissent."""
        return synthesize_tool(work_dir)

    return server


def main() -> None:
    create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
