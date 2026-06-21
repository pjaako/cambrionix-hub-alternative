# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Build a Python web application (GUI) to monitor and control charging processes for devices connected to Cambrionix hubs via the Cambrionix Hub API.

## Environment

Always activate and use the virtual environment:

```bash
source venv/bin/activate
pip install -r requirements.txt  # once requirements.txt exists
```

## Running the test script

```bash
source venv/bin/activate
python test_api.py
```

This requires `CambrionixApiService` running locally (default port `43424`).

## Architecture

The Cambrionix Hub API is a **JSON-RPC 2.0 service** (`CambrionixApiService`) that listens on `localhost:43424`. It can be reached via:
- Raw TCP socket (as in `test_api.py`)
- HTTP GET (`http://localhost:43424/?{json}`)
- WebSocket (`ws://localhost:43424`, protocol `jsonrpc`)

The application layer sits on top of this daemon. The typical call sequence is:
1. `cbrx_discover("local")` → get hub serial numbers
2. `cbrx_connection_open(hub_serial)` → get a connection handle (integer)
3. `cbrx_connection_get(handle, key)` / `cbrx_connection_set(handle, key, value)` → read/write hub state
4. `cbrx_connection_close(handle)` → release handle

Connection handles expire after **30 seconds of inactivity** unless notifications are registered.

## API Reference

All API documentation lives in `docs/cambrionix-hub-api-reference-v3.9/`:
- `01-overview-and-methods.md` — connection methods, all 34 API calls (5.1–5.34), notifications, deprecated methods, device string, API management, logging, docks
- `02-get-dictionary.md` — readable keys (hub properties, per-port data)
- `03-set-dictionary-and-misc.md` — writeable keys, LED control, battery info, error codes

**Always consult these docs before implementing any API call** to get correct method names, parameter order, and return shapes.

Key API calls for charging control:
- `cbrx_connection_set(handle, "Port.N.mode", value)` — set port charging mode
- `cbrx_connection_get(handle, "Port.N.CurrentLimit_mA")` — read port current
- `cbrx_notifications` — subscribe to async events (USB attach/detach, over-temp, over-voltage)

## Tech Stack (to be decided)

- Language: Python 3.8+
- GUI: Web-based (Flask or FastAPI + frontend TBD)
- API transport: JSON-RPC over TCP or WebSocket
