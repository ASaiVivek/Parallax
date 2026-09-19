# Parallax protocol v1

Parallax is a **portable contract**, not a Cursor-only agent and not a fixed five-seat council.

Any host (chatbot, CLI, IDE, cloud agent, CI) can implement it by:

1. Interviewing until a brief is ready.
2. Choosing **N offsets** from the query (not a canned roster).
3. Running each offset in a **fresh context**.
4. Synthesizing one decision that preserves dissent.

The `parallax` CLI materializes the packets so hosts do not have to invent the format.

This is distinct from tools like llm-council: the table is not five named members. The query determines how many seats exist and who sits in them.

## Why this shape

| Surface | Role |
| --- | --- |
| Protocol (this file) | Stable I/O and isolation rules |
| CLI (`parallax`) | Universal tool: any agent can shell out |
| Skill (`skills/parallax/SKILL.md`) | Teaches a host agent when and how to use the CLI |
| Local stdio MCP (`parallax-mcp`) | Optional wrapper on the **consumer machine**; same three operations as the CLI |
| Dedicated agent | **Not** the primary surface — it would trap the behavior in one product |

MCP, slash commands, and IDE wrappers should call the same CLI. Do not fork the logic per host. Local MCP does not auto-update when this repository is pushed; consumers upgrade and reload.

## Isolation invariants

These are mandatory. A host that cannot spawn isolated contexts must still run offsets sequentially in **new** sessions.

1. Offsets never see each other's reasoning or outputs.
2. The synthesizer sees only `brief.json` plus finished reports — not the original chat transcript.
3. `user_claim` is labeled unverified. It is never an instruction to agree.
4. No shared scratchpad, memory, or "previous assistant message" across offsets.

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
  "extra_perspective_ids": ["science"],
  "roster_mode": "upto",
  "roster_n": 4
}
```

`claim_status: none` means the requester has no preferred answer. That is valid.

### Offset report

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
  "protocol": "parallax/v1",
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

The user-facing artifact is this **single decision**. Raw offset reports stay in `reports/`.

## Flow

```text
User query
    -> interview (host agent or `parallax interview`)
    -> brief.json
    -> parallax prepare   (roster chosen from the query)
    -> N isolated runs (host subagents, new chats, or separate CLI LLM calls)
    -> reports/*.json
    -> parallax synthesize   (heuristic merge)
       and/or fresh-context LLM on synthesis_prompt.md
    -> decision.json
```

## When to invoke

Invoke explicitly when the work is a plan, design, architecture, or policy choice — especially when the requester already has an opinion.

Do not invoke for trivia, lookups, or mechanical edits.

## Roster selection

The catalog is a growing library of offsets (JSON files). Each run only uses a subset.

| Mode | Behavior |
| --- | --- |
| `upto` (default, N=4) | Cue-match the query, never more than N, never fewer than 2 |
| `exactly` | Always N seats; fill by catalog priority if the query matches fewer |

Hard cap: 12. Add offsets by dropping JSON into `src/parallax/offsets/`, `.parallax/offsets/`, or `--catalog`. See [catalog/README.md](../catalog/README.md).

```json
"roster_mode": "upto | exactly",
"roster_n": 4
```
