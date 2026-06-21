# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Build a Python web application (GUI) to monitor and control charging processes for devices connected to Cambrionix hubs via the Cambrionix Hub REST API (v4.0).

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

`CambrionixApiService` runs locally and exposes a **REST HTTP API (v4.0)** at `http://localhost:43424/api/v1/`. This is the API to use for all new development.

Typical call pattern:
1. `GET /api/v1/hubs` → list connected hubs (returns serial numbers)
2. `GET /api/v1/hubs/{hubId}/ports` → all port states for a hub
3. `GET /api/v1/hubs/{hubId}/ports/{portId}` → single port state
4. `POST /api/v1/hubs/{hubId}/ports/{portId}/mode` → set port mode

Port numbering note: port 0 is the hub's own FTDI serial interface, not a device port. Device ports start at 1.

## API Reference

The authoritative, always-current API reference is self-hosted by the running service:

- **Swagger UI**: `http://localhost:43424/api/v1/swagger`
- **OpenAPI JSON**: `http://localhost:43424/openapi.json` (45 endpoints, with per-endpoint sub-specs and schemas resolvable under the same host)

**Always fetch the live OpenAPI spec rather than relying on the local `docs/` folder.** The `docs/` directory contains a v3.9 JSON-RPC reference that is outdated and has known inaccuracies against the v4.0 service.

## Known issues

- `GET /api/v1/hubs/{hubId}/ports/{portId}` does not return the `energy` field (`power.charge.charging.energy`) despite it being marked `required` in the OpenAPI schema (`Charging` and `Charged` types). Bug reported to Cambrionix; confirmed on firmware 1.0.4 and 1.3.0. As a workaround, `Port.N.Energy_Wh` is available via the legacy JSON-RPC interface (see `test_api.py`).

## Tech Stack (to be decided)

- Language: Python 3.8+
- GUI: Web-based (Flask or FastAPI + frontend TBD)
- API transport: HTTP (REST)
