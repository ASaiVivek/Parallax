from typing import Literal

from pydantic import BaseModel, Field, field_validator

Position = Literal["support", "revise", "reject", "abstain"]
Action = Literal["proceed", "proceed_with_changes", "do_not_proceed", "need_more_info"]
Confidence = Literal["low", "medium", "high"]
RosterMode = Literal["upto", "exactly"]

MAX_ROSTER = 12
DEFAULT_N = 4
MIN_N = 2


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
    roster_mode: RosterMode = "upto"
    roster_n: int = DEFAULT_N

    @field_validator("roster_n")
    @classmethod
    def _clamp_n(cls, value: int) -> int:
        if value < 1:
            raise ValueError("roster_n must be at least 1")
        if value > MAX_ROSTER:
            raise ValueError(f"roster_n must be <= {MAX_ROSTER} to avoid bloat")
        return value


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
    stance: str
    mandate: str
    cues: list[str] = Field(default_factory=list)
    required: bool = False
    priority: int = 50


class PerspectivePacket(BaseModel):
    spec: PerspectiveSpec
    prompt: str
    filename: str


class WorkManifest(BaseModel):
    protocol: str = "parallax/v1"
    brief: Brief
    perspectives: list[PerspectiveSpec]
    isolation_rules: list[str]
    roster_mode: RosterMode = "upto"
    roster_n: int = DEFAULT_N


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
    protocol: str = "parallax/v1"
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
