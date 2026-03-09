# Running cozi_mcp Locally

The original `server.py` is wired to Smithery's cloud platform for credential
injection.  `server_local.py` is a drop-in replacement that reads credentials
from environment variables and exposes the same tools over stdio — the standard
transport for local MCP clients like Claude Desktop or Claude Code.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | `python --version` |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Recommended; `pip install uv` works too |
| A Cozi Family Organizer account | https://www.cozi.com |

---

## 1 — Install dependencies

```bash
# From the repo root
uv sync
```

`uv sync` reads `pyproject.toml` and creates a local `.venv`.  
The `smithery` package is still installed (it's a dependency of `mcp`), but
`server_local.py` never imports or calls it.

---

## 2 — Set your credentials

```bash
cp .env.example .env
# Edit .env:
#   COZI_USERNAME=your-email@example.com
#   COZI_PASSWORD=your-password
```

---

## 3 — Start script

A convenience script is included that loads `.env` and starts the server:

```bash
./start_local.sh
```

The script uses the `.venv/bin/python` created by `uv sync`, so you don't need
to activate the venv or worry about `python` vs `python3` on your system.

You can also run the server manually:

```bash
# Option A: use uv run (handles the venv automatically)
uv run python3 -m cozi_mcp.server_local

# Option B: activate the venv first
source .venv/bin/activate
python3 -m cozi_mcp.server_local
```

You won't see output until an MCP client connects, which is expected.
Press Ctrl-C to stop.

---

## 4 — Connect to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "cozi": {
      "command": "uv",
      "args": [
        "run",
        "--project", "/ABSOLUTE/PATH/TO/cozi_mcp",
        "python3", "-m", "cozi_mcp.server_local"
      ],
      "env": {
        "COZI_USERNAME": "your-email@example.com",
        "COZI_PASSWORD": "your-password"
      }
    }
  }
}
```

Replace `/ABSOLUTE/PATH/TO/cozi_mcp` with the actual path where you cloned
the repo.  Restart Claude Desktop — you should see the Cozi tools listed in
the tools panel.

### Alternative: use a .env file instead of inline env

If you prefer not to store credentials in the config file:

```json
{
  "mcpServers": {
    "cozi": {
      "command": "bash",
      "args": [
        "-c",
        "cd /ABSOLUTE/PATH/TO/cozi_mcp && source .env && uv run python3 -m cozi_mcp.server_local"
      ]
    }
  }
}
```

---

## 5 — Connect to Claude Code

The server uses **stdio** transport (stdin/stdout), not HTTP — there is no port.
Claude Code spawns the process itself, so you do **not** need to start the server
first.

```bash
claude mcp add --transport stdio cozi \
  --env COZI_USERNAME=your-email@example.com \
  --env COZI_PASSWORD=your-password \
  -- /ABSOLUTE/PATH/TO/cozi_mcp/start_local.sh
```

Or without the start script:

```bash
claude mcp add --transport stdio cozi \
  --env COZI_USERNAME=your-email@example.com \
  --env COZI_PASSWORD=your-password \
  -- uv run --project /ABSOLUTE/PATH/TO/cozi_mcp python3 -m cozi_mcp.server_local
```

---

## What changed vs. the original server.py

| Original (`server.py`) | Local (`server_local.py`) |
|---|---|
| `from smithery.decorators import smithery` | Removed |
| `@smithery.server(config_schema=...)` decorator | Removed |
| Credentials via `ctx.session_config.username / .password` | Credentials via `os.environ["COZI_USERNAME"]` / `["COZI_PASSWORD"]` |
| `ctx: Context` parameter on every tool | Removed (not needed for stdio) |
| Entry point via Smithery CLI | `if __name__ == "__main__": mcp.run()` |

No business logic was changed — all 13 tools are identical.

---

## Troubleshooting

**`AuthenticationError: COZI_USERNAME and COZI_PASSWORD must be set`**  
→ The env vars aren't reaching the process.  Double-check the `env` block in
your MCP client config, or `export` them in your shell before running.

**`ModuleNotFoundError: No module named 'cozi_client'`**  
→ Run `uv sync` from the repo root first.  Make sure you're using the venv
created by uv (`uv run ...` handles this automatically).

**`ModuleNotFoundError: No module named 'smithery'`**  
→ `uv sync` should install it; it's still listed in `pyproject.toml`.  
`server_local.py` doesn't import it, so this only matters if the `mcp`
package itself pulls it in as a hard dependency.