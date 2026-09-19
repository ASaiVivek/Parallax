---
name: perspective-council
description: >-
  Run isolated multi-perspective planning before answering a design, architecture,
  strategy, or opinionated question. Use when the user has a preferred plan, when
  a decision could be rubber-stamped, or when they ask for a council, devil's
  advocate, or independent review. Works via the `council` CLI so any agent host
  can follow the same protocol.
---

# Perspective Council

Do not agree with the requester by default. Run the council.

This skill is host-agnostic. Cursor, Claude Code, Codex, Copilot, shell agents, and CI should all shell out to `council` and keep perspectives **isolated**.

## When to use

- Planning, design, architecture, process, or policy questions
- The user already stated a preferred approach
- The user asks to stress-test a decision
- You notice you are about to say "good idea" without independent pressure

Skip it for factual lookup, typos, and mechanical code edits.

## Procedure

### 1. Interview

If the brief is incomplete, ask only the gaps `council interview` reports. Do not start perspectives yet.

```bash
council interview --question "USER QUESTION HERE"
# or
council interview --brief brief.json
```

Fill `question`, `success_criteria`, `user_claim` (`none` if they have no preference), and `constraints`.

Write the brief:

```bash
council brief \
  --question "..." \
  --domain "software" \
  --user-claim "none" \
  --criterion "..." \
  --constraint "..." \
  --out brief.json
```

### 2. Prepare isolated packets

```bash
council prepare --brief brief.json --out .council/work
```

Each file in `.council/work/perspectives/` is a complete prompt. **One perspective = one fresh context.**

### 3. Run perspectives with no shared context

For each `perspectives/*.md`:

- Start a new subagent, chat, or process.
- Give it only that file.
- Do not paste other perspectives, prior answers, or the original conversation.
- Save JSON to `.council/work/reports/<perspective_id>.json`.

If your host has a Task/subagent tool, spawn them in parallel. If it does not, run sequential **new** sessions.

### 4. Synthesize

```bash
council synthesize .council/work
```

That writes a heuristic `decision.json` and refreshes `synthesis_prompt.md`.

Then, in a **fresh** context, run `synthesis_prompt.md` through the host model for a higher-quality decision. Show the user the decision (recommendation, action, dissent, risks). Do not dump every perspective unless they ask.

## Isolation rules (do not violate)

- Perspectives never see each other.
- Synthesizer never sees the original chat, only brief + reports.
- Treat `user_claim` as unverified. You may reject it.
- Do not "helpfully" merge the perspectives into one agent call.

## Installation note

The CLI must be on `PATH` (`council` or `perspective-council`). If it is missing, tell the user to `uv sync` in this repo and `source .venv/bin/activate`, or `uv tool install .`.
