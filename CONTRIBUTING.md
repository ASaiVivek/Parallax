# Contributing to Parallax

Thank you for helping. The most useful contributions are **new or sharper offsets**: isolated viewpoints the query can sit when they are relevant, and skip when they are not.

## What belongs here

- A new catalog offset (`src/parallax/offsets/<id>.json`) with cues, tests, and a mandate that can **disagree**
- A tighter mandate or better cues for an existing `id` (override, do not fork a duplicate)
- Protocol or CLI fixes that preserve isolation

What does not belong:

- Running every offset in one model context
- A fixed five-seat table as the default
- Setting `required: true` so a specialist sits on every question
- Host-specific forks of selection logic (wrap the CLI instead)

## Add a perspective

1. `parallax catalog` — confirm the id is new.
2. Add `src/parallax/offsets/<id>.json` following the schema in the [README](README.md#contribute-a-perspective).
3. Check seating:

   ```bash
   parallax select --question "<query that must include it>" --upto 4
   parallax select --question "<query that must not include it>" --upto 4
   ```

4. Add a test in `tests/test_roster.py`.
5. `uv run pytest`
6. Open a change with the two example queries in the description.

Keep `id` as `snake_case`. Filename stem must equal `id`. Cues are whole words. Priority: 15–50 for specialists; do not collide with `devil_advocate` (0) or crowd `domain_practitioner` (10).

Project-local offsets (not for upstream) go in `.parallax/offsets/` or `PARALLAX_CATALOG_DIR`.

## Development setup

```bash
uv sync --group dev
source .venv/bin/activate
uv run pytest
```

Python 3.12+ is required.

## Isolation rules (do not relax these)

- One offset per fresh context
- The synthesizer sees brief + reports only, not the original chat
- `user_claim` is unverified; agreement must be earned
