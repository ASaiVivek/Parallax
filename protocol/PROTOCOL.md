# Perspective Council protocol v1

The council is a **portable contract**, not a Cursor-only agent.

Any host (chatbot, CLI, IDE, cloud agent, CI) can implement it by:

1. Interviewing until a brief is ready.
2. Running each perspective in a **fresh context**.
3. Synthesizing one decision that preserves dissent.

The `council` CLI materializes the packets so hosts do not have to invent the format.

## Why this shape

| Surface | Role |
| --- | --- |
| Protocol (this file) | Stable I/O and isolation rules |
| CLI (`council`) | Universal tool: any agent can shell out |
| Skill (`skills/perspective-council/SKILL.md`) | Teaches a host agent when and how to use the CLI |
| Dedicated agent | **Not** the primary surface — it would trap the behavior in one product |

MCP, slash commands, and IDE wrappers should call the same CLI. Do not fork the logic per host.

## Isolation invariants

These are mandatory. A host that cannot spawn isolated contexts must still run perspectives sequentially in **new** sessions.

1. Perspectives never see each other's reasoning or outputs.
2. The synthesizer sees only `brief.json` plus finished reports — not the original chat transcript.
3. `user_claim` is labeled unverified. It is never an instruction to agree.
4. No shared scratchpad, memory, or "previous assistant message" across perspectives.

## Objects

### Brief

```json
{
  "question": "string (required)",
  "domain": "string | null",
  "user_claim": "string | null",
  "claim_status": "unknown | none | stated",
  "constraints": ["string"],
  "success_criteria": ["string"],
  "facts": ["string"],
  "unknowns": ["string"],
  "audience": "string | null",
  "extra_perspective_ids": ["devil_advocate"]
}
```

`user_claim: null` means the requester has no preferred answer. That is valid.

### Perspective report

```json
{
  "perspective_id": "devil_advocate",
  "title": "Devil's advocate",
  "position": "support | revise | reject | abstain",
  "recommendation": "string",
  "key_arguments": ["string"],
  "risks": ["string"],
  "dissent_from_user_claim": "string | null",
  "confidence": "low | medium | high"
}
```

### Decision

```json
{
  "protocol": "perspective-council/v1",
  "recommendation": "string",
  "action": "proceed | proceed_with_changes | do_not_proceed | need_more_info",
  "confidence": "low | medium | high",
  "rationale": ["string"],
  "dissent": ["string"],
  "risks": ["string"],
  "changes_required": ["string"],
  "open_questions": ["string"],
  "perspective_tally": {"devil_advocate": "reject"},
  "synthesis_mode": "heuristic | prompt_only"
}
```

The user-facing artifact is this **single decision**. Raw debate stays in `reports/`.

## Flow

```text
User query
    -> interview (host agent or `council interview`)
    -> brief.json
    -> council prepare
    -> N isolated runs (host subagents, new chats, or separate CLI LLM calls)
    -> reports/*.json
    -> council synthesize   (heuristic merge)
       and/or fresh-context LLM on synthesis_prompt.md
    -> decision.json
```

## When to invoke

Invoke explicitly when the work is a plan, design, architecture, or policy choice — especially when the requester already has an opinion.

Do not invoke for trivia, lookups, or mechanical edits.

## Perspective selection

Hybrid:

- Always: `devil_advocate`
- Always: a practitioner voice for the domain
- Then 1–3 of: `operator`, `risk`, `beneficiary`, `evidence` from the question
- Cap: 5
