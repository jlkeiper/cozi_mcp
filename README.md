# Cozi MCP Server

An unofficial Model Context Protocol (MCP) server that provides AI assistants like Claude Desktop and Claude Code with access to [Cozi Family Organizer](https://www.cozi.com/) functionality. This server exposes Cozi's lists, calendar, and family management features through a standardized MCP interface so you can ask your AI to manage events and lists for you.

Also deployable on [Smithery.ai](https://smithery.ai) for cloud-hosted usage.

## Features

### Family Management
- Get family members and their information

### List Management
- View all lists (shopping and todo lists)
- Filter lists by type
- Create and delete lists

### Item Management
- Add items to lists
- Update item text
- Mark items as complete/incomplete
- Remove items from lists

### Calendar Management
- View appointments for any month
- Create new appointments
- Update existing appointments
- Delete appointments

## Installation

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip
- A [Cozi Family Organizer](https://www.cozi.com/) account

### 1. Clone and install

```bash
git clone https://github.com/mjucius/cozi-mcp.git
cd cozi-mcp
uv sync
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your Cozi email and password
```

## Usage

The server provides two entry points:

| File | Transport | Credentials | Use case |
|---|---|---|---|
| `server_local.py` | stdio | Environment variables / `.env` | Local MCP clients (Claude Desktop, Claude Code) |
| `server.py` | Smithery | Smithery session config | Cloud deployment on Smithery.ai |

### Claude Code

```bash
claude mcp add --transport stdio cozi \
  --env COZI_USERNAME=your-email@example.com \
  --env COZI_PASSWORD=your-password \
  -- /path/to/cozi_mcp/start_local.sh
```

Or without the start script:

```bash
claude mcp add --transport stdio cozi \
  --env COZI_USERNAME=your-email@example.com \
  --env COZI_PASSWORD=your-password \
  -- uv run --project /path/to/cozi_mcp python3 -m cozi_mcp.server_local
```

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "cozi": {
      "command": "uv",
      "args": [
        "run",
        "--project", "/path/to/cozi_mcp",
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

Alternatively, use the start script with a `.env` file to avoid storing credentials in the config:

```json
{
  "mcpServers": {
    "cozi": {
      "command": "bash",
      "args": ["-c", "cd /path/to/cozi_mcp && source .env && uv run python3 -m cozi_mcp.server_local"]
    }
  }
}
```

### mcporter

Add to your `mcporter.json` (or `~/.mcporter/config.json`):

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

Or using the start script:

```json
{
  "mcpServers": {
    "cozi": {
      "command": "bash",
      "args": ["/path/to/cozi_mcp/start_local.sh"],
      "cwd": "/path/to/cozi_mcp"
    }
  }
}
```

Replace `/path/to/cozi_mcp` with your actual clone path. Set `COZI_USERNAME` and `COZI_PASSWORD` in your shell environment, or replace `${COZI_USERNAME}` / `${COZI_PASSWORD}` with literal values.

You can also discover and test the server ad-hoc via the CLI:

```bash
npx mcporter list --stdio "uv run --project /path/to/cozi_mcp python3 -m cozi_mcp.server_local" \
  --env COZI_USERNAME=your-email@example.com \
  --env COZI_PASSWORD=your-password
```

### Smithery.ai (Cloud)

Deploy on Smithery.ai for cloud-hosted usage:

**[Deploy on Smithery.ai](https://smithery.ai/server/@mjucius/cozi_mcp)**

Credentials are configured through Smithery's interface.

### Smithery Playground (Development)

```bash
uv run playground
```

Opens a browser-based testing interface for all MCP tools.

## Available MCP Tools

### Family Management
- `get_family_members` - Get all family members in the account

### List Management
- `get_lists` - Get all lists (shopping and todo)
- `get_lists_by_type` - Filter lists by type (shopping/todo)
- `create_list` - Create new lists
- `delete_list` - Delete existing lists
- `update_list` - Update a list (e.g. reorder items)

### Item Management
- `add_item` - Add items to lists
- `update_item_text` - Update item text
- `mark_item` - Mark items complete/incomplete
- `remove_items` - Remove items from lists

### Calendar Management
- `get_calendar` - Get appointments for a specific month
- `create_appointment` - Create new calendar appointments
- `update_appointment` - Update existing appointments
- `delete_appointment` - Delete appointments

## Project Structure

```
cozi-mcp/
├── pyproject.toml                # Dependencies and metadata
├── smithery.yaml                 # Smithery.ai deployment config
├── start_local.sh                # Convenience script for local stdio usage
├── .env.example                  # Credential template
├── src/
│   └── cozi_mcp/
│       ├── __init__.py           # Package exports
│       ├── server.py             # MCP server (Smithery cloud)
│       └── server_local.py       # MCP server (local stdio)
└── debug_appointment.py          # Debug script for appointments
```

## Architecture

This MCP server is built using:
- **FastMCP** - Simplified MCP server framework
- **py-cozi-client** - Python client library for Cozi's API
- **Pydantic models** - All API responses use structured data models

The server maintains a single authenticated session with Cozi and exposes all functionality through the MCP protocol.

## Troubleshooting

**`AuthenticationError: COZI_USERNAME and COZI_PASSWORD must be set`**
The env vars aren't reaching the process. Check the `env` block in your MCP client config, or ensure your `.env` file is populated.

**`ModuleNotFoundError: No module named 'cozi_client'`**
Run `uv sync` from the repo root first. Use `uv run ...` to ensure the correct venv is active.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.