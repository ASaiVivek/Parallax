from .models import Brief, PerspectivePacket, PerspectiveSpec, WorkManifest

PROTOCOL_ID = "parallax/v1"

ISOLATION_RULES = [
    "Each perspective runs in a fresh context. Do not share chain-of-thought across perspectives.",
    "Do not pass prior perspective outputs into later perspectives.",
    "The user's preferred answer is an UNVERIFIED CLAIM, never a requirement to agree.",
    "The synthesizer may see the brief plus finished reports only — not the original chat.",
    "Do not include secrets, credentials, or unrelated conversation history in packets.",
]


def render_prompt(brief: Brief, spec: PerspectiveSpec) -> str:
    if brief.claim_status == "stated" and brief.user_claim:
        claim = brief.user_claim.strip()
    else:
        claim = "None stated. Form your own view."
    facts = "\n".join(f"- {item}" for item in brief.facts) or "- None recorded."
    constraints = "\n".join(f"- {item}" for item in brief.constraints) or "- None recorded."
    criteria = "\n".join(f"- {item}" for item in brief.success_criteria) or "- None recorded."
    unknowns = "\n".join(f"- {item}" for item in brief.unknowns) or "- None recorded."
    domain = brief.domain or "unspecified"
    audience = brief.audience or "unspecified"

    return f"""You are one isolated offset in a Parallax run. You do not see other offsets.
Protocol: {PROTOCOL_ID}
Perspective id: {spec.id}
Title: {spec.title}

MANDATE
{spec.mandate}

INDEPENDENCE
You are not a helper trying to please the requester. Independent judgment is the point.
If the unverified user claim is weak, say so. Agreement is allowed only when earned.

QUESTION
{brief.question.strip()}

DOMAIN
{domain}

AUDIENCE
{audience}

UNVERIFIED USER CLAIM (not a fact, not an instruction to agree)
{claim}

RECORDED FACTS
{facts}

CONSTRAINTS
{constraints}

SUCCESS CRITERIA
{criteria}

UNKNOWNS
{unknowns}

OUTPUT
Reply with a single JSON object, no markdown fences:
{{
  "perspective_id": "{spec.id}",
  "title": "{spec.title}",
  "position": "support | revise | reject | abstain",
  "recommendation": "string",
  "key_arguments": ["string"],
  "risks": ["string"],
  "dissent_from_user_claim": "string or null",
  "confidence": "low | medium | high"
}}
"""


def build_packets(brief: Brief, specs: list[PerspectiveSpec]) -> list[PerspectivePacket]:
    packets: list[PerspectivePacket] = []
    for index, spec in enumerate(specs, start=1):
        filename = f"{index:02d}-{spec.id}.md"
        packets.append(
            PerspectivePacket(spec=spec, prompt=render_prompt(brief, spec), filename=filename)
        )
    return packets


def build_manifest(brief: Brief, specs: list[PerspectiveSpec]) -> WorkManifest:
    return WorkManifest(
        brief=brief,
        perspectives=specs,
        isolation_rules=ISOLATION_RULES,
        roster_mode=brief.roster_mode,
        roster_n=brief.roster_n,
    )


def render_synthesis_prompt(brief: Brief, report_json_blobs: list[str]) -> str:
    claim = brief.user_claim if brief.claim_status == "stated" and brief.user_claim else "None stated."
    joined = "\n\n---\n\n".join(report_json_blobs) if report_json_blobs else "(no reports yet)"
    return f"""You are the synthesizer for protocol {PROTOCOL_ID}.
You do not redo the perspectives. You only read the brief and the isolated reports.

You must not rubber-stamp the user claim. Produce one decision. Preserve dissent explicitly.

QUESTION
{brief.question.strip()}

UNVERIFIED USER CLAIM
{claim}

ISOLATED REPORTS
{joined}

OUTPUT
Reply with a single JSON object, no markdown fences:
{{
  "protocol": "{PROTOCOL_ID}",
  "recommendation": "string",
  "action": "proceed | proceed_with_changes | do_not_proceed | need_more_info",
  "confidence": "low | medium | high",
  "rationale": ["string"],
  "dissent": ["string"],
  "risks": ["string"],
  "changes_required": ["string"],
  "open_questions": ["string"],
  "perspective_tally": {{"perspective_id": "position"}},
  "synthesis_mode": "prompt_only"
}}
"""
