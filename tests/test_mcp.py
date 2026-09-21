"""MCP wrapper tools must match CLI JSON and keep roster/isolation rules."""

import json
from pathlib import Path

from typer.testing import CliRunner

from parallax.cli import app
from parallax.interview import apply_answers
from parallax.mcp_server import brief_tool, create_server, interview_tool, prepare_tool, synthesize_tool
from parallax.models import Brief, PerspectiveReport
from parallax.workspace import prepare_workspace

runner = CliRunner()


def _ready_brief(tmp_path: Path) -> Path:
    brief = apply_answers(
        Brief(question="CLI or MCP first?"),
        {
            "domain": "software",
            "user_claim": "MCP only",
            "constraints": ["Must work in any IDE"],
            "success_criteria": ["Any agent can invoke it"],
        },
    )
    path = tmp_path / "brief.json"
    path.write_text(brief.model_dump_json(), encoding="utf-8")
    return path


def test_interview_tool_matches_cli():
    cli = runner.invoke(app, ["interview", "--question", "Pick a database"])
    assert cli.exit_code == 0
    tool = json.loads(interview_tool(question="Pick a database"))
    assert json.loads(cli.stdout) == tool
    assert tool["ready"] is False
    assert "success_criteria" in {gap["field"] for gap in tool["gaps"]}


def test_prepare_tool_refuses_incomplete_brief(tmp_path: Path):
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(Brief(question="Pick a database").model_dump_json(), encoding="utf-8")
    out = tmp_path / "work"
    cli = runner.invoke(app, ["prepare", "--brief", str(brief_path), "--out", str(out)])
    tool = json.loads(prepare_tool(out=str(out), brief=str(brief_path)))
    assert cli.exit_code == 2
    assert json.loads(cli.stdout) == tool
    assert tool["error"] == "brief_not_ready"


def test_prepare_and_synthesize_tools_match_cli(tmp_path: Path):
    brief_path = _ready_brief(tmp_path)
    work = tmp_path / "work"
    cli_prep = runner.invoke(app, ["prepare", "--brief", str(brief_path), "--out", str(work)])
    tool_prep = json.loads(prepare_tool(out=str(work), brief=str(brief_path)))
    assert cli_prep.exit_code == 0, cli_prep.stdout
    assert json.loads(cli_prep.stdout) == tool_prep
    assert tool_prep["roster_mode"] == "upto"
    assert tool_prep["roster_n"] == 4
    assert (work / "perspectives").exists()

    cli_syn = runner.invoke(app, ["synthesize", str(work)])
    tool_syn = json.loads(synthesize_tool(str(work)))
    assert cli_syn.exit_code == 0
    assert json.loads(cli_syn.stdout) == tool_syn
    assert tool_syn["action"] == "need_more_info"


def test_prepare_tool_respects_upto_with_drop_in_catalog(tmp_path: Path):
    extra = tmp_path / "offsets"
    extra.mkdir()
    (extra / "regulator.json").write_text(
        json.dumps(
            {
                "id": "regulator",
                "title": "Regulator",
                "stance": "legal",
                "mandate": "Ask whether a supervisor would allow this.",
                "cues": ["bank", "capital", "basel"],
                "required": False,
                "priority": 15,
            }
        ),
        encoding="utf-8",
    )
    brief = apply_answers(
        Brief(question="Does this meet Basel capital rules for the bank?"),
        {
            "user_claim": "none",
            "constraints": ["none"],
            "success_criteria": ["Supervisor would allow it"],
        },
    )
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(brief.model_dump_json(), encoding="utf-8")
    work = tmp_path / "work"
    payload = json.loads(
        prepare_tool(
            out=str(work),
            brief=str(brief_path),
            upto=4,
            catalog=[str(extra)],
        )
    )
    assert payload["ok"] is True
    assert payload["roster_n"] == 4
    packets = list((work / "perspectives").glob("*.md"))
    ids = [path.stem.split("-", 1)[1] for path in packets]
    assert "regulator" in ids
    assert "devil_advocate" in ids
    assert len(ids) <= 4
    for path in packets:
        text = path.read_text(encoding="utf-8")
        assert "UNVERIFIED USER CLAIM" in text
        assert "fresh context" in text.lower() or "isolated offset" in text.lower()


def test_prepare_tool_rejects_upto_and_exactly_together(tmp_path: Path):
    payload = json.loads(
        prepare_tool(
            out=str(tmp_path / "work"),
            question="Pick a database",
            upto=3,
            exactly=3,
        )
    )
    assert payload["error"] == "usage"
    assert "upto" in payload["message"]


def test_synthesize_tool_keeps_dissent_from_isolated_reports(tmp_path: Path):
    brief = apply_answers(
        Brief(question="Adopt the rewrite?"),
        {
            "user_claim": "Rewrite now.",
            "constraints": ["Team of 4"],
            "success_criteria": ["Ship this quarter"],
        },
    )
    work = tmp_path / "work"
    prepare_workspace(brief, work)
    report = PerspectiveReport(
        perspective_id="devil_advocate",
        position="reject",
        recommendation="Keep the current stack.",
        dissent_from_user_claim="The rewrite schedule is not evidence-backed.",
        risks=["Staffing cliff"],
        confidence="high",
    )
    (work / "reports" / "devil_advocate.json").write_text(report.model_dump_json(), encoding="utf-8")
    decision = json.loads(synthesize_tool(str(work)))
    assert decision["action"] == "do_not_proceed"
    assert any("rewrite" in item.lower() or "claim" in item.lower() for item in decision["dissent"] + [decision["recommendation"]])


def test_brief_tool_matches_cli_and_writes_file(tmp_path: Path):
    out = tmp_path / "nested" / "brief.json"
    args = [
        "brief",
        "--question",
        "CLI or MCP first?",
        "--domain",
        "software",
        "--user-claim",
        "none",
        "--constraint",
        "Must work in any IDE",
        "--criterion",
        "Any agent can invoke it",
        "--out",
        str(out),
    ]
    cli = runner.invoke(app, args)
    assert cli.exit_code == 0, cli.stdout
    tool = json.loads(
        brief_tool(
            question="CLI or MCP first?",
            domain="software",
            user_claim="none",
            constraints=["Must work in any IDE"],
            success_criteria=["Any agent can invoke it"],
            out=str(out),
        )
    )
    assert json.loads(cli.stdout) == tool
    assert tool["claim_status"] == "none"
    assert tool["user_claim"] is None
    assert out.is_file()


def test_interview_tool_reports_missing_brief_file(tmp_path: Path):
    missing = tmp_path / "nope.json"
    payload = json.loads(interview_tool(brief=str(missing)))
    assert payload["error"] == "usage"
    assert "not found" in payload["message"]


def test_synthesize_tool_reports_missing_work_dir(tmp_path: Path):
    payload = json.loads(synthesize_tool(str(tmp_path / "missing-work")))
    assert payload["error"] == "usage"
    assert "not found" in payload["message"]


def test_stdio_server_registers_cli_tools():
    server = create_server()
    names = sorted(server._tool_manager._tools)
    assert names == [
        "parallax_brief",
        "parallax_interview",
        "parallax_prepare",
        "parallax_synthesize",
    ]


def test_stdio_handshake_writes_into_process_cwd(tmp_path: Path):
    import asyncio
    import os
    import sys

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    binary = Path(__file__).resolve().parents[1] / ".venv" / "bin" / "parallax-mcp"
    if not binary.is_file():
        binary = Path(sys.executable).resolve().parent / "parallax-mcp"
    command = str(binary) if binary.is_file() else sys.executable
    args = [] if binary.is_file() else ["-m", "parallax.mcp_server"]
    assert binary.is_file() or command == sys.executable

    async def run() -> None:
        params = StdioServerParameters(
            command=command,
            args=args,
            cwd=str(tmp_path),
            env={**os.environ},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                names = sorted(tool.name for tool in (await session.list_tools()).tools)
                assert "parallax_brief" in names
                brief = await session.call_tool(
                    "parallax_brief",
                    {
                        "question": "Should local MCP be the install path?",
                        "domain": "software",
                        "user_claim": "none",
                        "constraints": ["Stay on the consumer machine"],
                        "success_criteria": ["Host can finish a run with MCP tools"],
                        "out": "brief.json",
                    },
                )
                assert brief.content
                text = brief.content[0].text
                assert json.loads(text)["claim_status"] == "none"
                assert (tmp_path / "brief.json").is_file()
                prep = await session.call_tool(
                    "parallax_prepare",
                    {"out": ".parallax/work", "brief": "brief.json"},
                )
                payload = json.loads(prep.content[0].text)
                assert payload["ok"] is True
                assert (tmp_path / ".parallax" / "work" / "perspectives").is_dir()

    asyncio.run(run())
