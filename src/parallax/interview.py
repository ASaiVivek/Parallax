from .models import Brief, InterviewGap, InterviewResult


def assess_brief(brief: Brief) -> InterviewResult:
    """Ask only for what Parallax cannot infer. Do not start isolated work until ready."""
    gaps: list[InterviewGap] = []
    question = brief.question.strip()
    if not question:
        gaps.append(
            InterviewGap(
                field="question",
                question="What decision or design needs an independent answer, in one sentence?",
            )
        )
    if not brief.success_criteria:
        gaps.append(
            InterviewGap(
                field="success_criteria",
                question="How will we know the answer was right? Name 1–3 success criteria.",
            )
        )
    if brief.claim_status == "unknown":
        gaps.append(
            InterviewGap(
                field="user_claim",
                question="Do you already prefer an answer? If yes, state it as a claim. If no, reply none.",
            )
        )
    if not brief.constraints:
        gaps.append(
            InterviewGap(
                field="constraints",
                question="What hard constraints exist (time, budget, stack, law, non-goals)? Reply none if there are none.",
            )
        )
    return InterviewResult(ready=len(gaps) == 0, gaps=gaps, brief=brief)


def apply_answers(brief: Brief, answers: dict[str, str | list[str] | None]) -> Brief:
    data = brief.model_dump()
    for key, value in answers.items():
        if key not in data:
            continue
        if key == "user_claim":
            if value is None:
                continue
            if isinstance(value, str) and value.strip().lower() in {"none", "no", "n/a"}:
                data["user_claim"] = None
                data["claim_status"] = "none"
            elif isinstance(value, str) and value.strip():
                data["user_claim"] = value.strip()
                data["claim_status"] = "stated"
            continue
        if key == "roster_n":
            if value is None:
                continue
            data[key] = int(value)
            continue
        if key == "roster_mode":
            if value is None:
                continue
            data[key] = value
            continue
        if key in {"constraints", "success_criteria", "facts", "unknowns", "extra_perspective_ids"}:
            if isinstance(value, str):
                if value.strip().lower() in {"none", "no", "n/a"}:
                    data[key] = []
                else:
                    data[key] = [part.strip() for part in value.split(";") if part.strip()]
            elif value is None:
                data[key] = []
            else:
                data[key] = value
            continue
        data[key] = value
    return Brief.model_validate(data)
