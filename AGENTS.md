# Agent Instructions and Project Context

This file provides context and instructions for AI agents working on the Cambrionix Hub Alternative project. It is maintained alongside `CLAUDE.md`, which contains equivalent guidance for Claude Code. Keep both files in sync when making decisions that affect project direction.

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

**Always fetch the live OpenAPI spec rather than relying on the local `docs/` folder.** The `docs/` directory contains:
- `docs/cambrionix-cli-reference/` — **active** firmware CLI reference (commands, column formats, flag meanings). Use this when working on `CliClient`.
- Older v3.9 JSON-RPC documentation — outdated and has known inaccuracies against the v4.0 service.

`deref_openapi.py` is a utility that fetches the fragmented OpenAPI spec and resolves all `$ref` sub-specs into a single flat JSON file (useful for MCP tools): `python deref_openapi.py` → writes `cambrionix_openapi_flat.json`.

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

## Tech Stack

- Language: Python 3.11+
- Framework: FastAPI + Jinja2 + vanilla JS (polling)
- Key files:
  - `hub_backends.py` — `HubClient` ABC and all three backend implementations (see below)
  - `hub_client.py` — thin shim: `RestApiClient as CambrionixClient`
  - `app.py` — FastAPI routes
  - `models.py` — `PortState` dataclass (shared across all backends)
  - `templates/index.html`, `static/main.js` — frontend

**`hub.py` is legacy code** — a low-level `CambrionixHub` class that predates `hub_backends.py`. It is not used by the app or any tests. Do not use it; it also contains the `\r`-only terminator bug that causes hub unresponsive state (see Known issues).

There is no formal test framework (no pytest). `test_api.py` is a standalone diagnostic/smoke-test script with a manual CLI dispatch (`if __name__ == "__main__"`).

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

### CliClient transport layer

`CliClient` is split into two layers: a `CliTransport` ABC (defines `send_command(cmd) -> str`) and the `CliClient` hub logic on top. Two transports exist:

- `SerialTransport` — opens the TTY directly, sends `cmd\r\n`, reads until `>>` prompt
- `ApiProxyTransport` — sends `POST /api/v1/hubs/{hubId}/command` with plain-text body; hub serial is the hub ID passed at construction

The named constructors `CliClient.via_serial()` and `CliClient.via_http()` select the transport. `SerialTransport.hub_serial()` calls `udevadm info` to read `ID_SERIAL_SHORT`; `ApiProxyTransport.hub_serial()` returns the stored hub ID.

### JsonRpcClient connection lifecycle

`JsonRpcClient` lazy-connects on first use (`_connect()`). Connection sequence: open TCP socket → `cbrx_discover` → `cbrx_connection_open(unit)` → returns a `handle`. All subsequent `cbrx_connection_get/set` calls pass this handle. The socket is kept alive across calls (`_sock` stored on instance). Call `close()` to release it. Batch RPC (`_rpc_batch()`) sends a JSON array in one socket write and parses the array response.

### Port state flags

Both `CliClient` and `JsonRpcClient` decode flags from the `state` command / `PortsInfo.Flags`:

| Flag | Meaning |
|------|---------|
| `O`  | Off |
| `D`  | Detached |
| `S`  | Sync mode |
| `B`  | Biased mode |
| absence of O/S/B | On (charging) |

The `state` command CSV column order (PDSync): `port, voltage_10mV, current_mA, flags, time_s, time_charged_or_x, energy_Wh_or_x, power_W`. `energy_Wh` is in column index 6 (0-based); `"x"` means still charging (treated as `None`).

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

## Development Guidelines

- Always use `venv` — all packages must be installed and run within the virtual environment
- Consult the live OpenAPI spec before implementing any API call
- Keep changes focused and minimal; do not refactor code outside the scope of the current task
- Commit messages should be concise and explain *why*, not just *what*
