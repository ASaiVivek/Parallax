# Perspective Council

A portable way to **stop rubber-stamping**. You ask a planning or design question; the council interviews you, runs several **isolated** perspectives (no shared context), and returns **one decision** with explicit dissent.

This is for any host: Cursor, Claude Code, Codex, other IDEs, shell agents, chatbots, CI. The product is a **protocol + CLI + skill**, not a Cursor-only agent.

## Why not a dedicated agent?

A dedicated agent would only exist where that agent type exists. A CLI is a tool every agent already knows how to call. A skill teaches *when* to call it. MCP or slash commands should wrap the same CLI.

## Install

```bash
uv sync
source .venv/bin/activate
council --help
```

Or install the command:

```bash
uv tool install .
```

## Usage

```bash
# 1. See what is still missing
council interview --question "Should we rewrite the API in Rust this quarter?"

# 2. Write a brief. user-claim 'none' means you have no preferred answer.
council brief \
  --question "Should we rewrite the API in Rust this quarter?" \
  --domain software \
  --user-claim "Yes, full rewrite next quarter." \
  --criterion "p99 under 100ms" \
  --constraint "Team of four" \
  --fact "Current service is Python" \
  --out brief.json

# 3. Materialize isolated prompts
council prepare --brief brief.json --out .council/work

# 4. Run each file in .council/work/perspectives/ in a BRAND-NEW context.
#    Save JSON reports to .council/work/reports/<id>.json

# 5. Merge
council synthesize .council/work
```

`synthesize` writes `decision.json` (deterministic merge of structured reports) and refreshes `synthesis_prompt.md`. For a stronger write-up, run that prompt in a fresh model session that has not seen the original chat.

## Skill for agents

Canonical skill: [skills/perspective-council/SKILL.md](skills/perspective-council/SKILL.md)

Host-specific copy instructions: [adapters/README.md](adapters/README.md)

Protocol: [protocol/PROTOCOL.md](protocol/PROTOCOL.md)

## Isolation rules

- One perspective per fresh context
- Never feed perspective A’s output into perspective B
- The synthesizer sees brief + reports only
- `user_claim` is an unverified claim, not an order to agree

## Tests

```bash
uv sync --group dev
uv run pytest
```
