# Parallax

A portable way to **stop rubber-stamping**. You ask a planning or design question. Parallax interviews you, chooses **N isolated offsets from that query** (not a fixed five-seat council), and returns **one decision** with explicit dissent.

This is for any host: Cursor, Claude Code, Codex, other IDEs, shell agents, chatbots, CI. The product is a **protocol + CLI + skill**, not a Cursor-only agent.

## Why this name

The same question is read from offset seats. How many seats, and which ones, depends on the query. That is parallax, not a standing council.

## Install

```bash
uv sync
source .venv/bin/activate
parallax --help
```

Or install the command:

```bash
uv tool install .
```

## Usage

```bash
# 1. See what is still missing
parallax interview --question "Should we rewrite the API in Rust this quarter?"

# 2. Write a brief. user-claim 'none' means you have no preferred answer.
parallax brief \
  --question "Should we rewrite the API in Rust this quarter?" \
  --domain software \
  --user-claim "Yes, full rewrite next quarter." \
  --criterion "p99 under 100ms" \
  --constraint "Team of four" \
  --fact "Current service is Python" \
  --out brief.json

# 3. Materialize isolated prompts (query picks up to 4; use --exactly N for a fixed table)
parallax prepare --brief brief.json --out .parallax/work --upto 4
# parallax prepare --brief brief.json --out .parallax/work --exactly 3

Add more perspectives as JSON: [catalog/README.md](catalog/README.md).

# 4. Run each file in .parallax/work/perspectives/ in a BRAND-NEW context.
#    Save JSON reports to .parallax/work/reports/<id>.json

# 5. Merge
parallax synthesize .parallax/work
```

`synthesize` writes `decision.json` (deterministic merge of structured reports) and refreshes `synthesis_prompt.md`. For a stronger write-up, run that prompt in a fresh model session that has not seen the original chat.

## Skill for agents

Canonical skill: [skills/parallax/SKILL.md](skills/parallax/SKILL.md)

Host-specific copy instructions: [adapters/README.md](adapters/README.md)

Protocol: [protocol/PROTOCOL.md](protocol/PROTOCOL.md)

## Isolation rules

- One offset per fresh context
- Never feed offset A’s output into offset B
- The synthesizer sees brief + reports only
- `user_claim` is an unverified claim, not an order to agree

## Tests

```bash
uv sync --group dev
uv run pytest
```
