# MakeHuman MCP Server

An [MCP](https://modelcontextprotocol.io) server that lets an AI assistant build
MakeHuman characters from natural language: set body properties, equip
clothes/hair/skin, and save/export the result.

It runs against one of two backends:

- **`local` (default)** — the GUI-free [`mhcore`](https://github.com/vidya-hub/makehuman-core)
  library, in-process. No running MakeHuman, no Qt, no OpenGL.
- **`socket`** — a running MakeHuman GUI over its socket bridge
  (`plugins/8_server_socket`). Use this to drive an interactive session.

```
local :  MCP client ──stdio──▶ makehuman-mcp ──in-process──▶ mhcore
socket:  MCP client ──stdio──▶ makehuman-mcp ──TCP JSON──▶ MakeHuman (Socket plugin) ──▶ mhapi
```

The backend is chosen by `MAKEHUMAN_BACKEND` (`local` | `socket`); when unset it
is `local` if `mhcore` is importable, otherwise `socket`.

## Install

This project lives inside the `makehuman-core` repo, so `mhcore` (the local
backend) is the sibling package at the repo root:

```bash
cd mcp-server
python3 -m venv .venv
./.venv/bin/pip install -e .        # the MCP server
./.venv/bin/pip install -e ..       # mhcore (local backend), from the repo root
```

That is all the `local` backend needs. To use the `socket` backend instead, set
`MAKEHUMAN_BACKEND=socket` and install the socket bridge into your own MakeHuman
(see `socket-bridge/README.md`), then:

1. Launch MakeHuman: `python makehuman/makehuman.py`
2. Go to the **Socket** task and tick **Accept connections** (default
   `127.0.0.1:12345`).

## Register the MCP server with a client

Command to run the server (stdio transport):

```bash
/absolute/path/to/mcp-server/.venv/bin/makehuman-mcp
```

Example Claude Desktop / Claude Code MCP config entry:

```json
{
  "mcpServers": {
    "makehuman": {
      "command": "/absolute/path/to/mcp-server/.venv/bin/makehuman-mcp"
    }
  }
}
```

Environment variables (optional):

- `MAKEHUMAN_BACKEND` — `local` or `socket` (default: `local` if `mhcore` is
  installed, else `socket`).
- `MAKEHUMAN_HOST` (default `127.0.0.1`), `MAKEHUMAN_PORT` (default `12345`) —
  socket backend only.
- `MHCORE_VERBOSE=1` — keep MakeHuman's full log output on stderr (local backend).

## Tools

- Status: `ping`, `new_character` (local backend: start a fresh base human)
- Body macros (0.0–1.0): `set_gender`, `set_age`, `set_weight`, `set_muscle`,
  `set_height`
- Detail: `list_modifiers`, `apply_modifier`, `get_applied_targets`
- Asset discovery: `list_available_clothes`, `list_available_hair`,
  `list_available_skins`, `list_available_eyebrows`, `list_available_eyelashes`
- Equip: `equip_clothes`, `unequip_clothes`, `unequip_all_clothes`,
  `equip_hair`, `equip_eyebrows`, `equip_eyelashes`, `set_skin`,
  `get_equipped_clothes`
- Persist/export: `save_character`, `load_character`, `export_character`
  (`format` = obj | fbx | dae; `mhx2` requires the socket backend)

## Develop / inspect

```bash
./.venv/bin/mcp dev makehuman_mcp/server.py
```

## Skill

A Claude Code skill describing the recommended workflow lives in
`skills/makehuman-character/`. Copy or symlink it into `~/.claude/skills/` to
make it available to Claude Code.
