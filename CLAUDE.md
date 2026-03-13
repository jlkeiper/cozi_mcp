# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based MCP (Model Context Protocol) server that exposes Cozi Family Organizer API functionality as tools for AI assistants like Claude Desktop and Claude Code. The server provides comprehensive access to Cozi lists, calendar, and family management features.

There are two server entry points:
- `src/cozi_mcp/server.py` - Cloud version using Smithery session config for credentials
- `src/cozi_mcp/server_local.py` - Local stdio version using environment variables for credentials

## Development Commands

- `uv sync` - Install dependencies and sync virtual environment
- `uv run playground` - Start interactive Smithery playground for testing tools
- `uv run dev` - Start Smithery development server
- `./start_local.sh` - Start the local stdio server (loads `.env` automatically)
- `uv run python3 -m cozi_mcp.server_local` - Start the local stdio server directly

## Environment Variables

The local server (`server_local.py`) requires these environment variables:
- `COZI_USERNAME` - Your Cozi account username/email
- `COZI_PASSWORD` - Your Cozi account password

Store them in `.env` (copied from `.env.example`). The `start_local.sh` script loads `.env` automatically.

## Architecture

### Core Components

- `src/cozi_mcp/server.py` - FastMCP server for Smithery cloud deployment (uses `ctx.session_config` for credentials)
- `src/cozi_mcp/server_local.py` - FastMCP server for local stdio usage (uses `os.environ` for credentials)
- `src/cozi_mcp/__init__.py` - Package initialization and exports
- `start_local.sh` - Convenience script that loads `.env` and starts `server_local.py`
- `debug_appointment.py` - Debug script for testing appointment functionality

### Dependencies

- `py-cozi-client>=1.3.0` - Published Cozi API client library
- `mcp>=1.0.0` - Model Context Protocol framework (using FastMCP)
- `smithery` - Required by `server.py` for cloud deployment

### Available MCP Tools (14 total)

**Family Management:**
- `get_family_members` - Get all family members in the account

**List Management:**
- `get_lists` - Get all lists (shopping and todo)
- `get_lists_by_type` - Filter lists by type (shopping/todo)
- `create_list` - Create new lists
- `delete_list` - Delete existing lists
- `update_list` - Update a list (e.g. reorder items)

**Item Management:**
- `add_item` - Add items to lists
- `update_item_text` - Update item text
- `mark_item` - Mark items complete/incomplete
- `remove_items` - Remove items from lists

**Calendar Management:**
- `get_calendar` - Get appointments for a specific month
- `create_appointment` - Create new calendar appointments
- `update_appointment` - Update existing appointments
- `delete_appointment` - Delete appointments

## Integration

### Claude Code

```bash
claude mcp add --transport stdio cozi \
  --env COZI_USERNAME=your-email@example.com \
  --env COZI_PASSWORD=your-password \
  -- /path/to/cozi_mcp/start_local.sh
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cozi": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/cozi_mcp", "python3", "-m", "cozi_mcp.server_local"],
      "env": {
        "COZI_USERNAME": "your-email@example.com",
        "COZI_PASSWORD": "your-password"
      }
    }
  }
}
```

### mcporter

Add to your `mcporter.json` config:

```json
{
  "mcpServers": {
    "cozi": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/cozi_mcp", "python3", "-m", "cozi_mcp.server_local"],
      "env": {
        "COZI_USERNAME": "${COZI_USERNAME}",
        "COZI_PASSWORD": "${COZI_PASSWORD}"
      }
    }
  }
}
```

### Smithery.ai

Cloud deployment uses `server.py` with `smithery.yaml` and `pyproject.toml` configuration. Credentials are managed through Smithery's interface.
