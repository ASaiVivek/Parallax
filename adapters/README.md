# Cursor

Copy [../../skills/parallax/SKILL.md](../../skills/parallax/SKILL.md) to `.cursor/skills/parallax/SKILL.md` in a project, or into your user skills directory.

Install the CLI so the agent can shell out:

```bash
uv sync --extra mcp --group dev
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
parallax brief ... --out brief.json
parallax prepare --brief brief.json --out .parallax/work
# isolated runs
parallax synthesize .parallax/work
```

# Local stdio MCP (v1)

Parallax can also be a **local** MCP server on the consumer's machine. It wraps the CLI. It does **not** call models and does **not** reimplement roster selection.

A GitHub push does **not** update anyone's install. Each consumer upgrades on their machine, then reloads the MCP process in the host.

**Cwd matters.** Relative paths (`brief.json`, `.parallax/work`) are resolved in the MCP process working directory. That should be the **user project**, not the Parallax clone.

Do **not** use `uv --directory` / `uv run --directory`. That **changes the process cwd into the clone**, so `brief.json` and `.parallax/work` are written into Parallax itself. Use `uv run --project` (discovers the package, keeps the host cwd) or exec `.venv/bin/parallax-mcp`.

GUI hosts (Cursor, Claude Desktop) often have a thin `PATH`. If `uv` is not found, use the absolute path to `uv` (or to `.venv/bin/parallax-mcp` after `uv sync --extra mcp`).

## What to add to the host

Cursor (`~/.cursor/mcp.json` or project `.cursor/mcp.json`) and Claude Code use the same stdio shape.

From a clone (`--project` keeps the host project as cwd):

```json
{
  "mcpServers": {
    "parallax": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/absolute/path/to/Parallax",
        "--extra",
        "mcp",
        "parallax-mcp"
      ]
    }
  }
}
```

After `uv sync --extra mcp` in the clone, you can skip `uv run` and exec the venv script (still do **not** set `cwd` to the clone):

```json
{
  "mcpServers": {
    "parallax": {
      "command": "/absolute/path/to/Parallax/.venv/bin/parallax-mcp"
    }
  }
}
```

Without cloning, `uvx` can fetch the repo. This is **cached**, not a live feed of `main`:

```json
{
  "mcpServers": {
    "parallax": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ASaiVivek/Parallax.git[mcp]",
        "parallax-mcp"
      ]
    }
  }
}
```

To pick up new commits: `git pull` in the clone, or `uvx --refresh --from git+https://github.com/ASaiVivek/Parallax.git[mcp] parallax-mcp`, then **reload MCP** in the host. Later, a published PyPI version (`uvx --from parallax[mcp] parallax-mcp` with a version pin) is the honest path for many consumers.

## Tools (CLI only)

1. `parallax_interview` → remaining brief gaps
2. `parallax_brief` → write `brief.json` (use `user_claim` `"none"` when there is no preference)
3. `parallax_prepare` → isolated packets under `out` (prefer `.parallax/work` in the **user** project)
4. `parallax_synthesize` → `decision.json` from `reports/`

The host remains responsible for isolated model calls. The tool must not run all offsets inside one LLM context.

Remote / hosted HTTP MCP is deferred. Briefs should stay on the consumer machine.

# Chatbot with no tools

Paste `skills/parallax/SKILL.md` into the system prompt, and either:

- attach this repo so the bot can run `parallax`, or
- have the bot follow PROTOCOL.md by hand (weaker, easier to leak context).
