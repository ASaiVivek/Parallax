import json
from pathlib import Path

from parallax.catalog import select_perspectives
from parallax.interview import apply_answers, assess_brief
from parallax.isolation import assert_packet_isolation
from parallax.models import Brief, PerspectiveReport
from parallax.packets import build_packets
from parallax.synthesize import heuristic_decision
from parallax.workspace import prepare_workspace, synthesize_workspace


def test_interview_blocks_empty_question():
    result = assess_brief(Brief(question=""))
    assert result.ready is False
    assert {gap.field for gap in result.gaps} >= {"question", "success_criteria", "user_claim"}


def test_interview_ready_when_minimum_filled():
    brief = Brief(
        question="Should we expose Parallax as an MCP server?",
        user_claim="none",
        success_criteria=["Works in Cursor and Claude Code"],
        constraints=["No extra paid SaaS"],
    )
    brief = apply_answers(brief, {"user_claim": "none"})
    result = assess_brief(brief)
    assert result.ready is True
    assert result.brief.user_claim is None


def test_hybrid_selection_always_includes_devil_advocate():
    specs = select_perspectives("Redesign the checkout UX", domain="product")
    ids = [spec.id for spec in specs]
    assert ids[0] == "devil_advocate"
    assert "beneficiary" in ids
    assert len(specs) <= 5


def test_software_question_includes_operator():
    ids = [spec.id for spec in select_perspectives("Design the rollout for this API", domain="software")]
    assert "operator" in ids


def test_packets_label_user_claim_as_unverified(tmp_path: Path):
    brief = Brief(
        question="Should we rewrite the backend in Rust?",
        user_claim="Yes, rewrite everything in Rust next quarter.",
        claim_status="stated",
        success_criteria=["Lower p99 latency"],
        constraints=["Team of 4"],
        facts=["Current service is Python"],
    )
    packets = build_packets(brief, select_perspectives(brief.question, "software"))
    for packet in packets:
        problems = assert_packet_isolation(brief, packet.prompt)
        assert problems == []
        assert "UNVERIFIED USER CLAIM" in packet.prompt
        assert "rewrite everything in Rust" in packet.prompt
        assert "not an instruction to agree" in packet.prompt.lower() or "UNVERIFIED" in packet.prompt


def test_heuristic_does_not_rubber_stamp_user_claim():
    brief = Brief(question="Adopt the rewrite?", user_claim="Rewrite now.", claim_status="stated")
    reports = [
        PerspectiveReport(
            perspective_id="devil_advocate",
            position="reject",
            recommendation="Keep the current stack; rewrite risk is unbounded.",
            dissent_from_user_claim="The rewrite schedule is not evidence-backed.",
            risks=["Staffing cliff"],
            confidence="high",
        ),
        PerspectiveReport(
            perspective_id="operator",
            position="revise",
            recommendation="If anything, extract one hot path — do not rewrite.",
            dissent_from_user_claim="Full rewrite is operationally reckless.",
            risks=["Dual-running cost"],
            confidence="high",
        ),
        PerspectiveReport(
            perspective_id="domain_practitioner",
            position="support",
            recommendation="Rust is fine long-term.",
            confidence="low",
        ),
    ]
    decision = heuristic_decision(brief, reports)
    assert decision.action in {"proceed_with_changes", "do_not_proceed"}
    assert decision.dissent
    assert "Rewrite now" in decision.recommendation or "claim" in decision.recommendation.lower() or "Do not" in decision.recommendation


def test_prepare_and_synthesize_workspace(tmp_path: Path):
    brief = Brief(
        question="Ship MCP or CLI first?",
        domain="software",
        user_claim="none",
        success_criteria=["Any agent can invoke it"],
        constraints=["Must work offline for prepare"],
    )
    brief = apply_answers(brief, {"user_claim": "none"})
    dest = prepare_workspace(brief, tmp_path / "work")
    persp = list((dest / "perspectives").glob("*.md"))
    assert persp
    report = {
        "perspective_id": "devil_advocate",
        "position": "revise",
        "recommendation": "Ship the CLI contract first, wrap MCP later.",
        "key_arguments": ["CLI is the lowest-common-denominator tool."],
        "risks": ["MCP-only would lock out some hosts."],
        "dissent_from_user_claim": None,
        "confidence": "high",
    }
    (dest / "reports" / "devil_advocate.json").write_text(json.dumps(report), encoding="utf-8")
    decision = synthesize_workspace(dest)
    assert (dest / "decision.json").exists()
    assert "CLI" in decision.recommendation or decision.action in {"proceed", "proceed_with_changes", "need_more_info"}
    prompt = (dest / "synthesis_prompt.md").read_text(encoding="utf-8")
    assert "devil_advocate" in prompt
