# Parallax

Parallax is a small, host-agnostic tool for **independent judgment**. You give it a planning or design question. It interviews until the brief is usable, **chooses N isolated viewpoints from that query** (not a standing five-seat table), runs each viewpoint with **no shared context**, and returns **one decision with explicit dissent**.

It is meant to be called from Cursor, Claude Code, Codex, other IDEs, shell agents, chatbots, and CI. The product is a **CLI + protocol + skill**. Wrappers (MCP, slash commands) should shell out to `parallax` rather than reimplementing selection.

Parallax is not [llm-council](https://github.com/karpathy/llm-council). That design is a fixed council. This one **casts a roster from the query**, can grow the catalog without changing the orchestrator, and caps how many seats sit on any one run.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Install

```bash
git clone <this-repository>
cd parallax
uv sync
source .venv/bin/activate
parallax --help
```

Install the command onto your PATH:

```bash
uv tool install .
```

## Quick start

```bash
# 1. See what the brief still needs
parallax interview --question "Should we rewrite the API in Rust this quarter?"

# 2. Write a brief. Use --user-claim none when you have no preferred answer.
parallax brief \
  --question "Should we rewrite the API in Rust this quarter?" \
  --domain software \
  --user-claim "Yes, full rewrite next quarter." \
  --criterion "p99 under 100ms" \
  --constraint "Team of four" \
  --fact "Current service is Python" \
  --out brief.json

# 3. Preview the roster the query would sit
parallax select --question "Should we rewrite the API in Rust this quarter?" --domain software --upto 4

# 4. Materialize one prompt file per isolated offset
parallax prepare --brief brief.json --out .parallax/work --upto 4

# 5. Run each file in .parallax/work/perspectives/ in a brand-new chat, subagent, or process.
#    Save JSON to .parallax/work/reports/<perspective_id>.json

# 6. Reduce to one decision
parallax synthesize .parallax/work
```

`synthesize` writes `decision.json` (a structured merge of the reports) and refreshes `synthesis_prompt.md`. For a stronger write-up, run that prompt in a **fresh** model session that has not seen the original chat. Show the user the decision — recommendation, action, dissent, risks — not the raw debate, unless they ask.

### Roster size

| Flag | Behavior |
| --- | --- |
| `--upto N` (default **4**) | Cue-match the query. Never more than N seats, never fewer than 2. |
| `--exactly N` | Always N seats. If the query matches fewer, fill from catalog priority. |

Hard cap is **12**. That is a ceiling against bloat, not a target.

```bash
parallax prepare --brief brief.json --out .parallax/work --upto 4
parallax prepare --brief brief.json --out .parallax/work --exactly 3
```

## How a run works

```text
question
  → interview until the brief is ready
  → select offsets from the catalog (upto N or exactly N)
  → N isolated model calls (one fresh context each)
  → reports/*.json
  → synthesize → decision.json
```

**Isolation is the point.** Do not paste offset A into offset B. Do not give the synthesizer the original chat — only `brief.json` plus finished reports. The requester’s preferred answer is an **unverified claim**, not an instruction to agree.

## CLI

| Command | Purpose |
| --- | --- |
| `parallax interview` | Remaining questions before work may start |
| `parallax brief` | Write `brief.json` |
| `parallax select` | Show which offsets the query would sit |
| `parallax prepare` | Write isolated prompt packets |
| `parallax synthesize` | Merge reports into one decision |
| `parallax catalog` | List builtin and drop-in offsets |

`--catalog DIR` (repeatable) and `PARALLAX_CATALOG_DIR` add extra offset directories. A later source **overrides** the same `id`.

## Use it from an agent

Copy [`skills/parallax/SKILL.md`](skills/parallax/SKILL.md) into the host’s skill slot:

| Host | Path |
| --- | --- |
| Cursor | `.cursor/skills/parallax/SKILL.md` |
| Claude Code | `.claude/skills/parallax/SKILL.md` |
| Codex / others | `AGENTS.md` or that product’s skill directory |

The host must still run each `perspectives/*.md` file in a **separate** subagent or session. MCP or tool wrappers should expose `interview`, `prepare`, and `synthesize` as shells around this CLI — they must not run every offset in one model context.

Host notes: [`adapters/README.md`](adapters/README.md). Wire format: [`protocol/PROTOCOL.md`](protocol/PROTOCOL.md).

## Builtin offsets

These ship in [`src/parallax/offsets/`](src/parallax/offsets/). A run only sits the subset the query warrants.

| id | Title | Required | Priority | Example cues |
| --- | --- | --- | --- | --- |
| `accessibility` | Accessibility | no | 48 | a11y, accessibility, disability, wcag |
| `beneficiary` | End beneficiary | no | 30 | product, ux, customer, user |
| `cost` | Cost and constraints | no | 40 | budget, cost, headcount, roi |
| `devil_advocate` | Devil's advocate | yes | 0 | (always seated) |
| `domain_practitioner` | Domain practitioner | no | 10 | practice, craft, implementation |
| `ethics` | Ethics | no | 45 | ethics, bias, fairness, harm |
| `evidence` | Evidence reviewer | no | 35 | research, data, study, experiment |
| `legal` | Legal and policy | no | 40 | legal, policy, regulation, gdpr |
| `operator` | Operator | no | 20 | software, api, infra, deploy, sre |
| `performance` | Performance | no | 45 | latency, throughput, scale, p99 |
| `risk` | Risk and security | no | 25 | security, auth, privacy, compliance |
| `science` | Scientific method | no | 48 | science, lab, clinical, hypothesis |
| `teaching` | Teacher / learner | no | 50 | education, teaching, curriculum |

`required` should stay rare. Almost every new offset should be **opt-in via cues**, not permanently seated.

## Contribute a perspective

The catalog is JSON. You do not need to change the orchestrator to add a voice.

### 1. Check that it is a new seat

```bash
parallax catalog
parallax select --question "YOUR TYPICAL QUERY" --domain YOUR_DOMAIN --upto 4
```

If an existing offset already covers the mandate, **tighten that file** (same `id` overrides) instead of adding a near-duplicate.

### 2. Add one JSON file

Builtin contributions go in `src/parallax/offsets/<id>.json`. Project-local experiments can live in `.parallax/offsets/` (gitignored) or a directory passed with `--catalog`.

```json
{
  "id": "regulator",
  "title": "Regulator",
  "stance": "legal",
  "mandate": "Ask whether a supervisor would allow this. Do not assume permission exists.",
  "cues": ["bank", "capital", "basel", "supervisor"],
  "required": false,
  "priority": 15
}
```

| Field | Rules |
| --- | --- |
| `id` | `snake_case`, unique, filename stem must match |
| `title` | Short human name |
| `stance` | One word for the kind of pressure this seat applies |
| `mandate` | Imperative. Tell the model what to **refuse**, not only what to prefer. Independent judgment, not helpfulness. |
| `cues` | Whole-word matches against `domain + question`. Prefer specific terms (`basel`, `p99`) over words that match everything (`system`, `make`). |
| `required` | `true` only if this seat must run on **every** query. Default `false`. |
| `priority` | Integer, lower wins ties and empty-seat fills. Leave 10 for the practitioner; use 15–50 for specialists. |

### 3. Prove it sits when it should — and stays out otherwise

```bash
# Should appear
parallax select --question "Does this meet Basel capital rules for the bank?" --upto 4 --catalog src/parallax/offsets

# Should not steal seats on an unrelated query
parallax select --question "What color should the icon be?" --upto 4
```

Add a test in `tests/test_roster.py` that loads your file through `load_catalog` and asserts the id appears on a representative question.

```bash
uv sync --group dev
uv run pytest
```

### 4. Open a change

One offset per change is easier to review. Include:

- Why this seat is not already covered
- Two example questions: one that **must** sit it, one that **must not**
- Confirmation you did not set `required: true` unless the whole project needs that seat on every run

Field-level notes: [`catalog/README.md`](catalog/README.md). Contributor checklist: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Development

```bash
uv sync --group dev
uv run pytest
uv run parallax catalog
```

Python package: `src/parallax`. Protocol id: `parallax/v1`.
