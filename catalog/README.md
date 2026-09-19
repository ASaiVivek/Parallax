# Adding perspectives

Parallax is not a fixed five-seat table. The catalog can grow; each run only
uses a subset.

## Drop in a new offset

Write a JSON file (one perspective per file):

```json
{
  "id": "regulator",
  "title": "Regulator",
  "stance": "legal",
  "mandate": "Ask whether a supervisor would allow this.",
  "cues": ["bank", "capital", "basel"],
  "required": false,
  "priority": 15
}
```

Load it from any of:

1. `src/parallax/offsets/*.json` (shipped with the package)
2. `.parallax/offsets/*.json` in the working directory
3. `PARALLAX_CATALOG_DIR=/path/to/dir` (colon-separated)
4. `parallax select --catalog /path/to/dir ...`

Same `id` in a later source overrides the builtin. That is how you tighten a mandate without forking the code.

`cues` are whole-word matches against `domain + question`. Higher match count ranks first. `priority` (lower wins) breaks ties and fills empty seats. `required: true` always takes a seat (keep this rare — usually only the devil's advocate).

## How many seats

| Flag | Behavior |
| --- | --- |
| `--upto N` (default N=4) | Query-matched seats, never more than N, never fewer than 2 |
| `--exactly N` | Always N seats; fill from priority if the query matches fewer |

Hard cap is 12. That is the bloat ceiling, not a target.

```bash
parallax select --question "Design the API rollout" --domain software --upto 4
parallax select --question "Design the API rollout" --domain software --exactly 3
parallax prepare --brief brief.json --out .parallax/work --upto 4
```
