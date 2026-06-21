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

## Checking API accessibility

Before running anything, confirm `CambrionixApiService` is up:

```bash
curl -s http://localhost:43424/api/v1/details | python3 -m json.tool
```

A healthy response returns the service version under `result.semver`. A connection error means the service is not running. From Python, use `check_api()` in `test_api.py` which returns `(True, version)` or `(False, error)`.

## Running the test script

```bash
source venv/bin/activate
python test_api.py
```

The script calls `check_api()` first and exits early with a clear message if the service is unreachable.

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

See `bugs/README.md` for the full index. Summary:

- `GET /api/v1/hubs/{hubId}/ports/{portId}` does not return the `energy` field (`power.charge.charging.energy`) despite it being marked `required` in the OpenAPI schema (`Charging` and `Charged` types). Bug reported to Cambrionix; confirmed on firmware 1.0.4 and 1.3.0. As a workaround, `Port.N.Energy_Wh` is available via the legacy JSON-RPC interface (see `test_api.py`). Full report: `bugs/bug_report_rest_api_missing_energy_wh.md`.
- `POST /api/v1/hubs/{hubId}/ports/{portId}/mode` with `{"mode": "off"}` works, but a subsequent call with `{"mode": "on"}` returns `{"result": true}` while the port state stays stuck on `"off"`. The port mode is effectively a one-way trip via this endpoint. The only confirmed port-scoped recovery is sending `mode c <portId>` to the hub's firmware CLI via `POST /api/v1/hubs/{hubId}/command`; a full hub reboot also works but disrupts every other port. Confirmed on firmware 1.3.0. Full report: `bugs/bug_report_rest_api_mode_off_unrecoverable.md`. Reproduction script: `bugs/reproduce_mode_off_bug.py`.

## Running the web app

```bash
source venv/bin/activate
uvicorn app:app --reload
# Open http://localhost:8000
```

The app polls `/api/ports` every 2 seconds and updates the UI live. Port mode can be set via the dropdown on each port card.

## Tech Stack

- Language: Python 3.11+
- Framework: FastAPI + Jinja2 + vanilla JS (polling)
- API transport: HTTP (REST via httpx)
- Key files: `app.py` (routes), `hub_client.py` (API client), `models.py` (PortState dataclass), `templates/index.html`, `static/main.js`

### Supported port modes

The hub advertises its supported modes via `GET /api/v1/hubs/{hubId}/ports/modes/supported`. The PDSync-C4 supports `on` and `off` only. `charge` and `detect` are legacy-hub-only modes. The app fetches supported modes dynamically at startup via `CambrionixClient.supported_modes()`.
