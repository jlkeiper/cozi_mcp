#!/usr/bin/env bash
# Start the Cozi MCP server locally using the .venv created by `uv sync`.
# Loads credentials from .env if present.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Prefer the venv python; fall back to uv run
if [ -x .venv/bin/python ]; then
    exec .venv/bin/python -m cozi_mcp.server_local
else
    exec uv run python3 -m cozi_mcp.server_local
fi
