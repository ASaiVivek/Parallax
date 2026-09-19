from typing import Literal

from pydantic import BaseModel, Field

Position = Literal["support", "revise", "reject", "abstain"]
Action = Literal["proceed", "proceed_with_changes", "do_not_proceed", "need_more_info"]
Confidence = Literal["low", "medium", "high"]
Stance = Literal["challenge", "build", "operate", "risk", "beneficiary", "evidence"]


class Brief(BaseModel):
    """Neutral packet of work. The user's opinion is a claim, not a fact."""

    question: str
    domain: str | None = None
    user_claim: str | None = None
    claim_status: Literal["unknown", "none", "stated"] = "unknown"
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    audience: str | None = None
    extra_perspective_ids: list[str] = Field(default_factory=list)


class InterviewGap(BaseModel):
    field: str
    question: str


class InterviewResult(BaseModel):
    ready: bool
    gaps: list[InterviewGap]
    brief: Brief


class PerspectiveSpec(BaseModel):
    id: str
    title: str
    stance: Stance
    mandate: str


class PerspectivePacket(BaseModel):
    spec: PerspectiveSpec
    prompt: str
    filename: str


class WorkManifest(BaseModel):
    protocol: str = "perspective-council/v1"
    brief: Brief
    perspectives: list[PerspectiveSpec]
    isolation_rules: list[str]


class PerspectiveReport(BaseModel):
    perspective_id: str
    title: str = ""
    position: Position
    recommendation: str
    key_arguments: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    dissent_from_user_claim: str | None = None
    confidence: Confidence = "medium"


class Decision(BaseModel):
    protocol: str = "perspective-council/v1"
    recommendation: str
    action: Action
    confidence: Confidence
    rationale: list[str]
    dissent: list[str]
    risks: list[str]
    changes_required: list[str]
    open_questions: list[str]
    perspective_tally: dict[str, str]
    synthesis_mode: Literal["heuristic", "prompt_only"] = "heuristic"
