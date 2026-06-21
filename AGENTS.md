# Agent Instructions and Project Context

This file provides context and instructions for AI agents working on the Cambrionix Hub Alternative project. It is maintained alongside `CLAUDE.md`, which contains equivalent guidance for Claude Code. Keep both files in sync when making decisions that affect project direction.

## Project Goal

Build a Python web application (GUI) to monitor and control charging processes for devices connected to Cambrionix hubs.

## Technical Stack

- **Language**: Python 3.8+
- **Environment**: Python virtual environment (`venv/`) — always activate before running or installing anything
- **GUI**: Web-based (framework TBD — Flask or FastAPI + frontend)
- **API**: Cambrionix Hub **REST API v4.0** over HTTP

## API

The application talks to `CambrionixApiService`, a locally installed daemon that listens on port `43424`. Use the **REST API** (`/api/v1/`) for all new development — not the legacy JSON-RPC interface.

### Checking the service is running

```bash
curl -s http://localhost:43424/api/v1/details | python3 -m json.tool
```

A healthy response returns `result.semver`. If the connection is refused, the service is not running (install from https://connect.cambrionix.com).

### API reference

The authoritative documentation is self-hosted by the running service:

- **Swagger UI**: `http://localhost:43424/api/v1/swagger`
- **OpenAPI JSON**: `http://localhost:43424/openapi.json` (45 endpoints; sub-specs and schemas resolve under the same host)

Do not rely on the `docs/` folder as a reference — it documents the legacy JSON-RPC API (v3.9) and has known inaccuracies against the v4.0 service that is actually running.

### Key REST endpoints

- `GET /api/v1/hubs` — list connected hubs
- `GET /api/v1/hubs/{hubId}/ports` — all port states
- `GET /api/v1/hubs/{hubId}/ports/{portId}` — single port state
- `POST /api/v1/hubs/{hubId}/ports/{portId}/mode` — set port mode

Port 0 is the hub's internal FTDI serial interface, not a device port. Device ports start at 1. Attachment state is exposed as a boolean field (`"attached": true/false`) in the port object, not via a flag character.

### Known API bugs

See `bugs/README.md` for the index of reported bugs and reproduction scripts.

`GET /api/v1/hubs/{hubId}/ports/{portId}` omits the `energy` field (`power.charge.charging.energy`) from its response despite it being marked `required` in the service's own OpenAPI schema (`Charging` and `Charged` types). Bug reported to Cambrionix; confirmed unfixed on firmware 1.0.4 and 1.3.0. See `bugs/bug_report_rest_api_missing_energy_wh.md` for the full report. As a workaround, energy is available via the legacy JSON-RPC interface — see `test_api.py` (`get_port_vitals`).

## Running the test script

```bash
source venv/bin/activate
python test_api.py
```

`test_api.py` checks API accessibility first (`check_api()`), then discovers hubs and ports via JSON-RPC and prints voltage, current, energy, and charge time for any attached device. It will be superseded by the main application once development begins.

## Development Guidelines

- Always use `venv` — all packages must be installed and run within the virtual environment
- Consult the live OpenAPI spec before implementing any API call
- Keep changes focused and minimal; do not refactor code outside the scope of the current task
- Commit messages should be concise and explain *why*, not just *what*
