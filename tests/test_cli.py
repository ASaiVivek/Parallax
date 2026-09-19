"""CLI smoke tests."""

from pathlib import Path

from typer.testing import CliRunner

from parallax.cli import app
from parallax.interview import apply_answers
from parallax.models import Brief

runner = CliRunner()


def test_interview_cli_json():
    result = runner.invoke(app, ["interview", "--question", "Pick a database"])
    assert result.exit_code == 0
    assert "success_criteria" in result.stdout
    assert '"ready": false' in result.stdout


def test_prepare_refuses_incomplete_brief(tmp_path: Path):
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(Brief(question="Pick a database").model_dump_json(), encoding="utf-8")
    result = runner.invoke(app, ["prepare", "--brief", str(brief_path), "--out", str(tmp_path / "work")])
    assert result.exit_code == 2
    assert "brief_not_ready" in result.stdout


def test_prepare_and_synthesize_cli(tmp_path: Path):
    brief = apply_answers(
        Brief(question="CLI or MCP first?"),
        {
            "domain": "software",
            "user_claim": "MCP only",
            "constraints": ["Must work in any IDE"],
            "success_criteria": ["Any agent can invoke it"],
        },
    )
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(brief.model_dump_json(), encoding="utf-8")
    work = tmp_path / "work"
    result = runner.invoke(app, ["prepare", "--brief", str(brief_path), "--out", str(work)])
    assert result.exit_code == 0, result.stdout
    assert (work / "perspectives").exists()
    syn = runner.invoke(app, ["synthesize", str(work)])
    assert syn.exit_code == 0
    assert "need_more_info" in syn.stdout
