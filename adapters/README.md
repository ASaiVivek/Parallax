# Cursor

Copy [../../skills/parallax/SKILL.md](../../skills/parallax/SKILL.md) to `.cursor/skills/parallax/SKILL.md` in a project, or into your user skills directory.

Install the CLI so the agent can shell out:

```bash
uv sync
source .venv/bin/activate
```

Cursor subagents (`Task`) are the right way to run each `perspectives/*.md` file. One subagent per file. Do not share their transcripts.

# Claude Code

Copy the same `SKILL.md` into `.claude/skills/parallax/SKILL.md`.

Use separate Task/subagent turns, or sequential new sessions, for each offset file.

# Codex / other IDE agents

Add the skill text to `AGENTS.md` or the product's skill slot. The contract is still:

```bash
parallax interview ...
parallax prepare --brief brief.json --out .parallax/work
# isolated runs
parallax synthesize .parallax/work
```

# Generic MCP / tool wrapper

Do not reimplement selection or prompts. Expose three tools that wrap the CLI:

1. `parallax_interview` → `parallax interview --brief ...`
2. `parallax_prepare` → `parallax prepare ...`
3. `parallax_synthesize` → `parallax synthesize ...`

The host remains responsible for isolated model calls. The tool must not run all offsets inside one LLM context.

# Chatbot with no tools

Paste `skills/parallax/SKILL.md` into the system prompt, and either:

- attach this repo so the bot can run `parallax`, or
- have the bot follow PROTOCOL.md by hand (weaker, easier to leak context).
