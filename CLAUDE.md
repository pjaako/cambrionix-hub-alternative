# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Build a Python web application (GUI) to monitor and control charging processes for devices connected to Cambrionix hubs via the Cambrionix Hub REST API (v4.0).

## Environment

Always activate and use the virtual environment:

```bash
source venv/bin/activate
pip install -r requirements.txt
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
python test_api.py                                        # basic REST API smoke test
python test_api.py backends                               # compare all three backends side-by-side
python test_api.py port-info <port_id>                    # full state + supported modes for one port
python test_api.py mode-test <port_id>                    # toggle off/on via JSON-RPC (bug diagnostic)
python test_api.py fw-mode-test <hub_id> <port_id>        # toggle via firmware CLI
python test_api.py sync-wakeup-test <hub_id> <port_id>    # nudge stuck-off port via sync
```

The default invocation calls `check_api()` first and exits early with a clear message if the service is unreachable.

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

- **Serial port exclusivity**: `CambrionixApiService` holds `/dev/ttyUSB0` exclusively. Using `SerialTransport` directly while the service is running will conflict — the service will log "Unresponsive hub" errors and lose the hub. Only use `SerialTransport` when the service is stopped, or use `ApiProxyTransport` to go through the service instead.
- **Hub unresponsive state**: If the hub's serial input buffer gets corrupted (e.g. commands sent without the required CR+LF terminator, or a partial write during a conflict), the hub enters an unresponsive state. A USB replug does not recover it — only a full **power cycle** (unplug from power supply) clears the firmware buffer.
- **CR+LF terminator**: The firmware CLI requires commands terminated with `\r\n` (CR+LF). Sending `\r` alone leaves the hub waiting for LF, causing the unresponsive state described above. `SerialTransport` sends `\r\n`; `ApiProxyTransport` and the service handle this correctly.
- `GET /api/v1/hubs/{hubId}/ports/{portId}` does not return the `energy` field (`power.charge.charging.energy`) despite it being marked `required` in the OpenAPI schema. Confirmed ≥4.0.0, still present in 4.0.1. **Workaround implemented:** `RestApiClient._fetch_energies()` fetches energy for all ports in one `state` CLI command via the `/command` proxy and merges it into REST responses. Full report: `bugs/bug_report_rest_api_missing_energy_wh.md`.
- `POST /api/v1/hubs/{hubId}/ports/{portId}/mode` with `{"mode": "on"}` returns `{"result": true}` while the port stays stuck on `"off"`. Confirmed ≥4.0.0, still present in 4.0.1. **Workaround implemented:** `RestApiClient.set_mode("on")` bypasses the broken endpoint and sends `mode c <portId>` via the firmware CLI `/command` proxy. Full report: `bugs/bug_report_rest_api_mode_off_unrecoverable.md`. Reproduction script: `bugs/reproduce_mode_off_bug.py`.

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
- Key files:
  - `hub_backends.py` — `HubClient` ABC and all three backend implementations (see below)
  - `hub_client.py` — thin shim: `RestApiClient as CambrionixClient`
  - `app.py` — FastAPI routes
  - `models.py` — `PortState` dataclass (shared across all backends)
  - `templates/index.html`, `static/main.js` — frontend

## Hub Backends

All three backends implement the same `HubClient` interface defined in `hub_backends.py`:

```
hub_id() -> str
supported_modes() -> list[str]
get_ports() -> list[PortState]
get_port(port_id: int) -> PortState
set_mode(port_id: int, mode: str) -> None
```

| Class | Protocol | Notes |
|---|---|---|
| `RestApiClient` | REST v4.0 | Used by the web app; modes are `"on"`/`"off"` |
| `JsonRpcClient` | JSON-RPC v3.9 | TCP socket to port 43424; lazy-connects, keeps socket alive; `get_ports()` uses `PortsInfo` + batch RPC for speed, `get_port()` fetches full vitals including energy |
| `CliClient` | Firmware CLI | Use `CliClient.via_serial(tty)` for direct serial or `CliClient.via_http(hub_id)` to proxy through the REST service |

Mode strings are normalized across all backends: `"on"`, `"off"`, `"sync"`, `"biased"`. JSON-RPC and CLI translate to/from their native single-char codes (`c`/`o`/`s`/`b`) internally.

`PortState.energy_wh` is populated by all three backends. `RestApiClient` fetches it via a firmware CLI `state` command through the `/command` proxy (workaround for a known REST API bug — see Known issues).

### Discovery

Each backend provides a classmethod to enumerate available hubs:

```python
RestApiClient.discover(base)      # GET /hubs — returns list[RestApiClient]
JsonRpcClient.discover(host, port)# cbrx_discover — returns list[JsonRpcClient]
CliClient.discover_serial()       # scans USB serial ports by FTDI VID — returns list[CliClient]
```

Returned instances have hub identity pre-seeded (no extra network/serial call on first use).

### Supported port modes

All three backends determine supported modes dynamically from the hub's firmware class (`fc` field):

| Firmware class (`fc`) | Hardware | Modes |
|---|---|---|
| `ps` | PDSync (e.g. PDSync-4) | `on`, `off` |
| `sm` | SMART (TS3-C10) | `on`, `off` |
| `un` | Universal | `on`, `off`, `sync`, `biased` |

`RestApiClient` queries `GET /api/v1/hubs/{hubId}/ports/modes/supported`. `JsonRpcClient` reads the `Hardware` property and maps it through `_hw_to_fc()`. `CliClient` parses the `fc:` field from the `id` command. All three return `["on", "off"]` for a PDSync hub.

### Hub ID

The hub ID is the FTDI chip's USB serial number (e.g. `DK0F9SOT`), not the firmware `sn` field (which is zeroed on some hubs). `RestApiClient` and `JsonRpcClient` receive it directly from the service. `CliClient` reads it from the OS via `udevadm info` (`ID_SERIAL_SHORT`) for `SerialTransport`, or uses the stored hub ID for `ApiProxyTransport`.
