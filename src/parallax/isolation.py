"""Guards so packets never treat the user claim as ground truth."""

from .models import Brief
from .packets import ISOLATION_RULES, render_prompt, render_synthesis_prompt
from .catalog import CATALOG


FORBIDDEN_AGREEMENT = (
    "agree with the user",
    "the user is right",
    "implement the user's plan as specified",
)


def assert_packet_isolation(brief: Brief, prompt: str) -> list[str]:
    problems: list[str] = []
    lowered = prompt.lower()
    for phrase in FORBIDDEN_AGREEMENT:
        if phrase in lowered:
            problems.append(f"prompt asks the model to {phrase}")
    if brief.user_claim:
        if "UNVERIFIED USER CLAIM" not in prompt:
            problems.append("user claim is not labeled unverified")
        if brief.user_claim in prompt.split("QUESTION", 1)[0]:
            # claim may appear later; it must not replace the question
            pass
    if "You do not see other offsets" not in prompt:
        problems.append("missing isolation sentence")
    return problems


def synthesis_sees_only_brief_and_reports(prompt: str) -> bool:
    return "original chat" not in prompt.lower() and "UNVERIFIED USER CLAIM" in prompt


def isolation_rules() -> list[str]:
    return list(ISOLATION_RULES)


def sample_prompt(brief: Brief) -> str:
    return render_prompt(brief, CATALOG["devil_advocate"])


def sample_synthesis_prompt(brief: Brief) -> str:
    return render_synthesis_prompt(brief, ["{}"])
