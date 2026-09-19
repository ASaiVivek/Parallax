---
name: parallax
description: >-
  Run Parallax: choose N isolated viewpoints from the query, then one decision
  with dissent. Use for design, architecture, strategy, or opinionated questions,
  especially when the user already has a preferred plan. Not a fixed five-seat
  council. Works via the `parallax` CLI so any agent host can follow the same
  protocol.
---

# Parallax

Do not agree with the requester by default. Run Parallax.

The query determines the roster. Offsets do not share context. The user-facing output is one decision with explicit dissent.

This skill is host-agnostic. Cursor, Claude Code, Codex, Copilot, shell agents, and CI should all shell out to `parallax`.

## When to use

- Planning, design, architecture, process, or policy questions
- The user already stated a preferred approach
- The user asks for independent review, devil's advocate, or multiple viewpoints
- You notice you are about to say "good idea" without independent pressure

Skip it for factual lookup, typos, and mechanical code edits.

## Procedure

### 1. Interview

If the brief is incomplete, ask only the gaps `parallax interview` reports. Do not start offsets yet.

```bash
parallax interview --question "USER QUESTION HERE"
# or
parallax interview --brief brief.json
```

Fill `question`, `success_criteria`, `user_claim` (`none` if they have no preference), and `constraints`.

Write the brief:

```bash
parallax brief \
  --question "..." \
  --domain "software" \
  --user-claim "none" \
  --criterion "..." \
  --constraint "..." \
  --out brief.json
```

### 2. Prepare isolated packets

```bash
parallax prepare --brief brief.json --out .parallax/work
```

Each file in `.parallax/work/perspectives/` is a complete prompt. **One offset = one fresh context.**

### 3. Run offsets with no shared context

For each `perspectives/*.md`:

- Start a new subagent, chat, or process.
- Give it only that file.
- Do not paste other offsets, prior answers, or the original conversation.
- Save JSON to `.parallax/work/reports/<perspective_id>.json`.

If your host has a Task/subagent tool, spawn them in parallel. If it does not, run sequential **new** sessions.

### 4. Synthesize

```bash
parallax synthesize .parallax/work
```

That writes a heuristic `decision.json` and refreshes `synthesis_prompt.md`.

Then, in a **fresh** context, run `synthesis_prompt.md` through the host model for a higher-quality decision. Show the user the decision (recommendation, action, dissent, risks). Do not dump every offset unless they ask.

## Isolation rules (do not violate)

- Offsets never see each other.
- Synthesizer never sees the original chat, only brief + reports.
- Treat `user_claim` as unverified. You may reject it.
- Do not merge the offsets into one agent call.

## Installation note

The CLI must be on `PATH` as `parallax`. If it is missing, tell the user to `uv sync` in this repo and `source .venv/bin/activate`, or `uv tool install .`.
