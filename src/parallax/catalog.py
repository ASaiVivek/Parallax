from .models import PerspectiveSpec

CATALOG: dict[str, PerspectiveSpec] = {
    "devil_advocate": PerspectiveSpec(
        id="devil_advocate",
        title="Devil's advocate",
        stance="challenge",
        mandate=(
            "Assume the leading idea is wrong until evidence says otherwise. "
            "Hunt confirmation bias, hidden costs, and failure modes. "
            "You may support the claim only if you cannot honestly break it."
        ),
    ),
    "domain_practitioner": PerspectiveSpec(
        id="domain_practitioner",
        title="Domain practitioner",
        stance="build",
        mandate=(
            "Answer as a practitioner who has shipped this kind of work. "
            "Prefer the approach that would survive contact with reality, not the most elegant one."
        ),
    ),
    "operator": PerspectiveSpec(
        id="operator",
        title="Operator",
        stance="operate",
        mandate=(
            "Judge operability: rollout, ownership, observability, rollback, and day-2 cost. "
            "Reject designs that cannot be run by a tired on-call."
        ),
    ),
    "risk": PerspectiveSpec(
        id="risk",
        title="Risk and security",
        stance="risk",
        mandate=(
            "Treat abuse, safety, privacy, legal exposure, and irreversible mistakes as first-class. "
            "Do not trade those away for convenience."
        ),
    ),
    "beneficiary": PerspectiveSpec(
        id="beneficiary",
        title="End beneficiary",
        stance="beneficiary",
        mandate=(
            "Speak for the person who lives with the result. "
            "If the plan serves the builder more than the user, say so."
        ),
    ),
    "evidence": PerspectiveSpec(
        id="evidence",
        title="Evidence reviewer",
        stance="evidence",
        mandate=(
            "Separate known facts from inferences. "
            "Flag where the brief is under-determined and what would change the decision."
        ),
    ),
}

_SOFTWARE = ("software", "code", "api", "app", "infra", "backend", "frontend", "devops", "sre")
_SECURITY = ("security", "auth", "privacy", "threat", "compliance", "secret")
_PRODUCT = ("product", "ux", "ui", "customer", "user", "marketplace")
_POLICY = ("legal", "policy", "regulation", "governance", "medical", "finance")


def _haystack(brief_domain: str | None, question: str) -> str:
    return f"{brief_domain or ''} {question}".lower()


def select_perspectives(
    question: str,
    domain: str | None = None,
    extra_ids: list[str] | None = None,
    max_perspectives: int = 5,
) -> list[PerspectiveSpec]:
    """Hybrid roster: always challenge + a domain voice; fill the rest from the query."""
    text = _haystack(domain, question)
    chosen: list[str] = ["devil_advocate"]

    if any(token in text for token in _SOFTWARE):
        chosen.append("operator")
        chosen.append("domain_practitioner")
    elif any(token in text for token in _POLICY):
        chosen.append("risk")
        chosen.append("domain_practitioner")
    else:
        chosen.append("domain_practitioner")

    if any(token in text for token in _SECURITY) and "risk" not in chosen:
        chosen.append("risk")
    if any(token in text for token in _PRODUCT) and "beneficiary" not in chosen:
        chosen.append("beneficiary")
    if "evidence" not in chosen:
        chosen.append("evidence")

    for extra in extra_ids or []:
        if extra in CATALOG and extra not in chosen:
            chosen.append(extra)

    # Keep order stable and cap size, but never drop the devil's advocate.
    unique: list[str] = []
    for pid in chosen:
        if pid not in unique:
            unique.append(pid)
    if len(unique) > max_perspectives:
        unique = unique[:max_perspectives]
        if "devil_advocate" not in unique:
            unique[-1] = "devil_advocate"
            unique = ["devil_advocate", *[p for p in unique if p != "devil_advocate"]][:max_perspectives]
    return [CATALOG[pid] for pid in unique]
