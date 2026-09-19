# Cursor

Copy [../../skills/perspective-council/SKILL.md](../../skills/perspective-council/SKILL.md) to `.cursor/skills/perspective-council/SKILL.md` in a project, or into your user skills directory.

Install the CLI so the agent can shell out:

```bash
uv sync
source .venv/bin/activate
```

Cursor subagents (`Task`) are the right way to run each `perspectives/*.md` file. One subagent per file. Do not share their transcripts.

# Claude Code

Copy the same `SKILL.md` into `.claude/skills/perspective-council/SKILL.md`.

Use separate Task/subagent turns, or sequential new sessions, for each perspective file.

# Codex / other IDE agents

Add the skill text to `AGENTS.md` or the product's skill slot. The contract is still:

```bash
council interview ...
council prepare --brief brief.json --out .council/work
# isolated runs
council synthesize .council/work
```

# Generic MCP / tool wrapper

Do not reimplement selection or prompts. Expose three tools that wrap the CLI:

1. `council_interview` → `council interview --brief ...`
2. `council_prepare` → `council prepare ...`
3. `council_synthesize` → `council synthesize ...`

The host remains responsible for isolated model calls. The tool must not run all perspectives inside one LLM context.

# Chatbot with no tools

Paste `skills/perspective-council/SKILL.md` into the system prompt, and either:

- attach this repo so the bot can run `council`, or
- have the bot follow PROTOCOL.md by hand (weaker, easier to leak context).
