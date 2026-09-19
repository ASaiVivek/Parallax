from collections import Counter

from .models import Action, Brief, Confidence, Decision, PerspectiveReport

_POSITION_WEIGHT = {
    "reject": 0,
    "abstain": 1,
    "revise": 2,
    "support": 3,
}


def heuristic_decision(brief: Brief, reports: list[PerspectiveReport]) -> Decision:
    if not reports:
        return Decision(
            recommendation="No isolated reports were provided.",
            action="need_more_info",
            confidence="low",
            rationale=["Parallax cannot decide without isolated offset reports."],
            dissent=[],
            risks=["Skipping isolation produces rubber-stamping."],
            changes_required=["Run each perspective packet in a fresh context."],
            open_questions=list(brief.unknowns),
            perspective_tally={},
            synthesis_mode="heuristic",
        )

    tally = {report.perspective_id: report.position for report in reports}
    counts = Counter(report.position for report in reports)
    avg = sum(_POSITION_WEIGHT[report.position] for report in reports) / len(reports)

    if counts["reject"] >= 2 or (counts["reject"] == 1 and counts["support"] == 0):
        action: Action = "do_not_proceed"
    elif counts["revise"] or (counts["reject"] and counts["support"]):
        action = "proceed_with_changes"
    elif counts["support"] == len(reports):
        action = "proceed"
    else:
        action = "need_more_info"

    if avg <= 1:
        confidence: Confidence = "low"
    elif avg >= 2.5 and counts["reject"] == 0:
        confidence = "high"
    else:
        confidence = "medium"

    dissent = [
        report.dissent_from_user_claim or f"{report.perspective_id}: {report.position} — {report.recommendation}"
        for report in reports
        if report.position in {"revise", "reject"} or report.dissent_from_user_claim
    ]
    risks = list(dict.fromkeys(risk for report in reports for risk in report.risks))
    rationale = [
        f"{report.perspective_id} ({report.position}): {report.recommendation}" for report in reports
    ]
    changes = [
        report.recommendation
        for report in reports
        if report.position == "revise"
    ]

    if action == "do_not_proceed":
        recommendation = (
            "Do not adopt the leading claim as stated. "
            + (reports[0].recommendation if reports else "")
        )
        if brief.claim_status == "stated" and brief.user_claim:
            recommendation = (
                f"Reject or replace the claim «{brief.user_claim}». "
                f"Strongest objection: {dissent[0] if dissent else rationale[0]}"
            )
    elif action == "proceed":
        lead = brief.user_claim if brief.claim_status == "stated" and brief.user_claim else reports[0].recommendation
        recommendation = f"Proceed: {lead}"
    elif action == "proceed_with_changes":
        recommendation = "Proceed only with the revisions named by the isolated offsets."
        if brief.claim_status == "stated" and brief.user_claim:
            recommendation = f"Do not accept «{brief.user_claim}» unchanged. {recommendation}"
    else:
        recommendation = "Collect the missing evidence listed in open_questions before deciding."

    open_questions = list(brief.unknowns)
    for report in reports:
        if report.position == "abstain":
            open_questions.append(f"{report.perspective_id} abstained: {report.recommendation}")

    return Decision(
        recommendation=recommendation,
        action=action,
        confidence=confidence,
        rationale=rationale,
        dissent=dissent,
        risks=risks,
        changes_required=changes,
        open_questions=open_questions,
        perspective_tally=tally,
        synthesis_mode="heuristic",
    )
