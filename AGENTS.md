# Agent Instructions and Project Context

This file provides context and instructions for AI agents working on the Cambrionix Hub Alternative project. It is the single source of truth for project guidance.

## Project Goal

Build a Python web application (GUI) to monitor and control charging processes for devices connected to Cambrionix hubs via the Cambrionix Hub REST API (v4.0).

## Environment

The project runs on both Linux and Windows from a single codebase — platform-specific
behaviour belongs behind a cross-platform API, not in a fork or a parallel code path.

Always activate and use the virtual environment:

```bash
source venv/bin/activate          # Linux/macOS
pip install -r requirements.txt
```

```powershell
.\venv\Scripts\Activate.ps1       # Windows (PowerShell)
pip install -r requirements.txt
```

Examples throughout this file use the Linux activation form; substitute the Windows
one as needed. Serial ports are `/dev/ttyUSB0`-style on Linux and `COM3`-style on
Windows — `CliClient.via_serial()` takes whichever the OS uses, and
`CliClient.discover_serial()` finds them without either being hardcoded.

## Git/SSH Configuration

When working with SSH remotes that require a passphrase, Git may fail in non-interactive sessions. To enable GUI passphrase prompts (e.g., in a KDE environment), use the following configuration:

1. **Git Configuration**:
   ```bash
   git config --global core.askpass /usr/bin/ksshaskpass
   ```

2. **Environment Variables**:
   Ensure `SSH_ASKPASS` and `SSH_ASKPASS_REQUIRE` are set:
   ```bash
   export SSH_ASKPASS=/usr/bin/ksshaskpass
   export SSH_ASKPASS_REQUIRE=force
   export DISPLAY=:0
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

- **Serial port exclusivity**: `CambrionixApiService` holds `/dev/ttyUSB0` exclusively. Using `SerialTransport` directly while the service is running will conflict — the service will log "Unresponsive hub" errors and lose the hub. Only use `SerialTransport` when the service is stopped, or use `ApiProxyTransport` to go through the service instead. `SerialTransport` itself now opens with `exclusive=True` (TIOCEXCL), so any second concurrent open on the same tty — from the REST service, or from our own rediscovery racing an active poll — fails immediately with `SerialException` instead of silently interleaving reads and corrupting/dropping port lines.
- **Hub unresponsive state**: If the hub's serial input buffer gets corrupted (e.g. commands sent without the required CR+LF terminator, or a partial write during a conflict), the hub enters an unresponsive state. A USB replug does not recover it — only a full **power cycle** (unplug from power supply) clears the firmware buffer.
- **CR+LF terminator**: The firmware CLI requires commands terminated with `\r\n` (CR+LF). Sending `\r` alone leaves the hub waiting for LF, causing the unresponsive state described above. `SerialTransport` sends `\r\n`; `ApiProxyTransport` and the service handle this correctly.
- `GET /api/v1/hubs/{hubId}/ports/{portId}` does not return the `energy` field (`power.charge.charging.energy`) despite it being marked `required` in the OpenAPI schema. Confirmed ≥4.0.0 through 4.0.1; **appears fixed in 4.1.2** (field now present, verified 2026-08-03). Workaround (`RestApiClient._fetch_energies()`, merges energy from a `state` CLI command via the `/command` proxy) is left in place pending more soak time on 4.1.2 — it's a no-op once the native field is populated. Full report: `bugs/bug_report_rest_api_missing_energy_wh.md`.
- `POST /api/v1/hubs/{hubId}/ports/{portId}/mode` with `{"mode": "on"}` returns `{"result": true}` while the port stays stuck on `"off"`. Confirmed ≥4.0.0 through 4.0.1; **appears fixed in 4.1.2** (two clean off→on round trips verified 2026-08-03, previously 100% reproducible). Workaround (`RestApiClient.set_mode("on")` bypasses the REST endpoint, sends `mode c <portId>` via the firmware CLI `/command` proxy) is left in place pending more soak time. Full report: `bugs/bug_report_rest_api_mode_off_unrecoverable.md`. Reproduction script: `bugs/reproduce_mode_off_bug.py`.

- **`JsonRpcClient` residual gap**: `set_mode` now raises `CommandRefused` when the JSON-RPC reply carries an `error` member, but a `cbrx_connection_set` that returns a falsy *result* with no `error` member still passes silently. Not fixable without an older service to characterise it against.

## Pending verification on Linux

Commit `4f3c496` ("Run the CLI serial backend on Windows as well as Linux") was tested
**only on Windows** — a U16S on Universal firmware 1.83, Python 3.14. It changes code paths
Linux already depended on, so the items below need confirming on a Linux host with a hub.
**Delete this section once they pass.**

Setup: stop `CambrionixApiService` first (see README, "Freeing the serial port"), then
activate the venv.

1. **`hub_id` must be unchanged.** `SerialTransport.hub_serial()` no longer shells out to
   `udevadm info`; it reads `serial_number` from `serial.tools.list_ports.comports()`.
   Confirm both agree:
   ```bash
   udevadm info --query=property /dev/ttyUSB0 | grep ID_SERIAL_SHORT
   python -c "from hub_backends import CliClient; print([h.hub_id for h in CliClient.discover_serial()])"
   ```
   If pyserial's sysfs read differs from `ID_SERIAL_SHORT`, every hub's ID shifts. IDs key
   `HubController._hubs` and must match what the REST service reports for the same hub, so a
   mismatch is a silent breakage, not a cosmetic one.
2. **No suffix stripped on Linux.** `_normalize_usb_serial()` removes a trailing A–D only
   when `sys.platform == "win32"` (Windows' FTDI driver appends a channel letter). The Linux
   ID should come through untouched.
3. **`CliClient.via_serial()` lost its `/dev/ttyUSB0` default** — the argument is now
   required. No in-repo caller relied on the default; check any local scripts that might.
4. **Known edge case, deliberately not fixed:** `udevadm` used to resolve
   `/dev/serial/by-id/...` symlinks. The `comports()` lookup matches on `info.device`, so a
   by-id path now finds no match and `hub_id` falls back to the firmware `sn` (zeroed on some
   hubs). Pass the real `/dev/ttyUSB*` node, or teach the lookup to resolve symlinks.
5. **End to end:** `python test_api.py backends`, then the web app toggling a port
   off → on → off.
6. **`health` now runs on every firmware class**, not just Universal. Only a PDSync or
   TS3-C10 hub can confirm that its per-port voltage still comes from the `state` column and
   is not overwritten by the health reading, and that the extra round trip per poll does not
   hurt responsiveness. Unit-guarded by `test_pdsync_voltage_comes_from_state_not_health`,
   but never run against that hardware.

Unverified on any platform: the `OV` and `OT` health flags, and whether they block mode
changes the way `UV` does — see `docs/cambrionix-cli-reference/01-introduction-and-commands-a-m.md` §3.6.

## Running the web app

```bash
source venv/bin/activate
uvicorn app:app --reload
# Open http://localhost:8000
```

The app polls `/api/hubs` every 2 seconds and updates the UI live. Each port is a tile showing attachment/status, voltage, current, energy delivered, and charging time; the tile stats display the raw `PortState` units directly (`mV`/`mA`/`mWh`, unit printed after the value, correctly cased — no V/Wh conversion, no uppercasing). Mode is set via a radio-button toggle on the tile (off/data/power, or off/data+power on hubs without sync). A padlock icon in each hub's header gates hub-wide mode buttons that apply a mode to every port on that hub at once. A "Refresh Hubs" button triggers on-demand rediscovery.

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

All commands support a `--debug` flag to show raw backend communication (JSON bodies, JSON-RPC strings, and CLI text).

The default invocation calls `check_api()` first and exits early with a clear message if the service is unreachable.

```bash
source venv/bin/activate
python -m unittest test_cli_parsing test_controller_errors -v   # no hardware needed
python verify_ui.py      # end-to-end error UI check; needs a hub and chromium
```

`verify_ui.py` starts its own server, injects each error kind through the dev route, and
asserts that the SSR markup and the browser DOM agree, failing on any console error. It
needs `python -m playwright install chromium` once. Named `verify_*` rather than `test_*`
so pytest does not collect it — it starts a server at import time.

## Debug Logging

All backends in `hub_backends.py` include `logger.debug()` calls to capture raw communication. This is useful for diagnosing parsing errors or firmware bugs.

### Enabling in tools

Pass the `--debug` flag to `test_api.py`:
```bash
python test_api.py backends --debug
```

### Enabling in code

The logging level is controlled by the standard Python `logging` module. To enable it globally in your script/app:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Alternatively, set the `CAMBRIONIX_DEBUG` environment variable, which `test_api.py` checks:
```bash
export CAMBRIONIX_DEBUG=1
python test_api.py
```

## Tech Stack

- Language: Python 3.11+
- Framework: FastAPI + Jinja2 + vanilla JS (polling)
- Key files:
  - `hub_backends.py` — `HubClient` ABC and all three backend implementations (see below)
  - `hub_client.py` — `discover_hubs()` factory; currently returns `CliClient.discover_serial()`
  - `controller.py` — `HubController`: background polling layer (see below)
  - `app.py` — FastAPI routes; reads from `HubController` cache, never touches serial directly
  - `models.py` — `PortState` dataclass (shared across all backends) plus the `Attachment`/`Status` `StrEnum`s. Electrical readings are integers in their smallest unit (`voltage_mv`, `current_ma`, `energy_mwh`) rather than floats, to avoid float rounding drift. `voltage_mv` and `charging_seconds` are typed `| None` (a backend that genuinely has no reading, e.g. `set_mode` racing a poll, leaves it `None`); `current_ma` and `energy_mwh` are never `None` — backends coerce missing/unparseable readings to `0`
  - `templates/index.html`, `static/main.js` — frontend

**Do not introduce a `hub.py`** — this name was used by an early prototype `CambrionixHub` class that predates `hub_backends.py`. It had the `\r`-only terminator bug that causes hub unresponsive state (see Known issues). All hub logic now lives in `hub_backends.py`.

`test_api.py` is a standalone diagnostic/smoke-test script with a manual CLI dispatch (`if __name__ == "__main__"`). `test_cli_parsing.py` and `test_controller_errors.py` are `unittest` suites that mock the transport and the hub client respectively, so they run anywhere. `verify_ui.py` drives a real browser against a real hub.

## Hub Backends

All three backends implement the same `HubClient` interface defined in `hub_backends.py`:

```
hub_id: str  # property
supported_modes() -> list[str]
get_ports() -> list[PortState]
get_port(port_id: int) -> PortState
set_mode(port_id: int, mode: str) -> None
```

| Class | Protocol | Notes |
|---|---|---|
| `RestApiClient` | REST v4.0 | Modes are `"on"`/`"off"` |
| `JsonRpcClient` | JSON-RPC v3.9 | TCP socket to port 43424; lazy-connects, keeps socket alive; `get_ports()` uses `PortsInfo` + batch RPC for speed, `get_port()` fetches full vitals including energy |
| `CliClient` | Firmware CLI | Use `CliClient.via_serial(tty)` for direct serial or `CliClient.via_http(hub_id)` to proxy through the REST service |

Backend selection tradeoffs (service dependency, hub scope, security) are documented in `README.md` under "Which backend to use?".

Mode strings are normalized across all backends: `"on"`, `"off"`, `"sync"`, `"biased"`. JSON-RPC and CLI translate to/from their native single-char codes (`c`/`o`/`s`/`b`) internally.

### CliClient transport layer

`CliClient` is split into two layers: a `CliTransport` ABC (defines `send_command(cmd) -> str`) and the `CliClient` hub logic on top. Two transports exist:

- `SerialTransport` — opens the TTY directly, sends `cmd\r\n`, reads until `>>` prompt. Local hubs only. `send_command()` uses an idle timeout: the read deadline is pushed out each time a chunk arrives (capped by a hard overall deadline), so multi-line `state` responses aren't truncated mid-transmission on hubs with more ports.
- `ApiProxyTransport` — sends `POST /api/v1/hubs/{hubId}/command` with plain-text body; hub serial is the hub ID passed at construction. Inherits the service's hub scope (local + remote via Cambrionix Connect).

The named constructors `CliClient.via_serial()` and `CliClient.via_http()` select the transport. `SerialTransport.hub_serial()` looks its own port up in `serial.tools.list_ports.comports()` and returns the USB serial number, normalized by `_normalize_usb_serial()` (see Hub ID below); `ApiProxyTransport.hub_serial()` returns the stored hub ID.

### JsonRpcClient connection lifecycle

`JsonRpcClient` lazy-connects on first use (`_connect()`). Connection sequence: open TCP socket → `cbrx_discover` → `cbrx_connection_open(unit)` → returns a `handle`. All subsequent `cbrx_connection_get/set` calls pass this handle. The socket is kept alive across calls (`_sock` stored on instance). Call `close()` to release it. Batch RPC (`_rpc_batch()`) sends a JSON array in one socket write and parses the array response.

### Port state flags

Both `CliClient` and `JsonRpcClient` decode flags from the `state` command / `PortsInfo.Flags`.
On PDSync/TS3-C10 firmware (`fc` `ps`/`sm`) the flags are **positional**: up to 3
space-separated tokens — Attachment, Status, Quick-Charge — e.g. `"A C -"`. Column
position matters: `C` means *Type-C cable, no device* in Attachment but *Charging* in
Status, so the tokens must be read by position, not pooled into a set.

Column 1 (Attachment) → `PortState.attachment`:

| Flag | Meaning |
| :--- | :--- |
| `A` | Attached |
| `D` | Detached |
| `P` | PD contract established |
| `C` | Type-C cable detected (but no device) |

Column 2 (Status) → `PortState.status`:

| Flag | Meaning |
| :--- | :--- |
| `I` | Idle |
| `S` | Host port connected |
| `C` | Charging |
| `F` | Finished charging |
| `O` | Off |
| `c` | Power enabled, no device detected |

Column 3 (Quick Charge, not currently exposed on `PortState`): `-`/`_` disallowed, `+` allowed, `q` enabled, `Q` in use.

Universal firmware (`fc` `un`) instead reports a single combined flag set (order doesn't
matter, letters are mutually exclusive per firmware docs): `A`/`D` (attachment) plus one
of `O`/`S`/`B`/`I`/`P`/`C`/`F` (status: off/sync/biased/idle/profiling/charging/finished).
`E`/`R`/`T`/`r` (error/rebooted/theft/vbus-reset) may also appear, plus an undocumented
lowercase `e`. Two of them are surfaced, and **they are deliberately kept apart**:

| Flag | Scope | Surfaced as | Effect |
|---|---|---|---|
| `E` | **Hub** — printed on every port line, but means "system errors present, check `health`" | `HubHealth.error_flags`, alongside `UV`/`OV`/`OT` | Hub refuses all mode changes with `*E422`; hub header goes red and every control is disabled |
| `e` | **Port** — undocumented, see `docs/cambrionix-cli-reference` | `PortState.port_error` | That port will not detect or charge a device, though it still accepts mode commands. Only that tile goes red |

`E` is folded into the health reading by `CliClient._note_system_error()` rather than stored
per port. Putting it on `PortState` would mean sixteen "port errors" for one hub condition,
which would then paint every tile red and hide a genuinely broken port among them.

`R`/`T`/`r` are not surfaced; `R` in particular is deliberately *not* an error, since it
blocks nothing and `crf` clears it. PDSync/TS3-C10 have no error column at all, so
`port_error` is always `False` there and `health` is the only source.

Full reference: `docs/cambrionix-cli-reference/02-commands-n-z-and-deprecated.md:66-112`.

A port has exactly one attachment value and one status value at a time, typed as the
`Attachment`/`Status` `StrEnum`s in `models.py` (each has an `UNKNOWN` fallback member;
`Status` also covers `sync`/`biased`/`profiling` for universal firmware, beyond the six
PDSync/TS3-C10 values above). Both serialize as plain strings over JSON — a caller of
`hub_backend` (e.g. `GET /api/hubs`) sees `attachment`/`status` as strings per port, e.g.
`"status": "finished"`.

The `state` command CSV column order (PDSync): `port, voltage_10mV, current_mA, flags, time_s, time_charged_or_x, energy_Wh_or_x, power_W`. `energy_Wh` is in column index 6 (0-based); `"x"` means still charging (treated as `None`).

`PortState.energy_mwh` (milliwatt-hours) is populated by all three backends. `RestApiClient` fetches it via a firmware CLI `state` command through the `/command` proxy (workaround for a known REST API bug — see Known issues).

**Universal-firmware voltage**: the `state` command's Universal variant has no voltage column (see CSV order above `## Controller`) — these are USB2 hubs with every port paralleled onto one supply rail, so per-port voltage isn't a meaningful firmware concept. `CliClient._probe_health()` instead runs the hub-wide `health` command and applies the one reading to every port. **`health` now runs on every firmware class**, not just Universal, because it is the only source of hub error flags (`UV`/`OV`/`OT`) — but only Universal takes its *voltage* from it. `get_ports()` passes `supply_mv=None` for `ps`/`sm`, so health can never overwrite the per-port reading those products report in `state` (guarded by `test_pdsync_voltage_comes_from_state_not_health`). Note this costs `ps`/`sm` hubs one extra CLI round trip per poll; if serial latency becomes a problem, run it every Nth poll for those classes only — Universal must stay every-poll since its voltage depends on it. A product without `health` answers `*E400`, which is treated as "no reading", not a failure. The live-hub output format (`5V Now:   5.13`, in volts) differs from what `docs/cambrionix-cli-reference` documents (`5V_V1: 5042`, in mV) — `_parse_health()` parses both, but only the `5V Now` volts format has been confirmed against real hardware (verified 2026-08-17 against a real Universal-firmware hub, PSU-adjustment-verified). `RestApiClient` doesn't need this workaround — the REST API's per-port `sensors` array already reports `volts` correctly on Universal hubs.

### Discovery

Each backend provides a classmethod to enumerate available hubs:

```python
RestApiClient.discover(base)       # GET /hubs — returns list[RestApiClient]
JsonRpcClient.discover(host, port) # cbrx_discover — returns list[JsonRpcClient]
CliClient.discover_http(base)      # GET /hubs, wraps each in ApiProxyTransport — returns list[CliClient]
CliClient.discover_serial()        # probes all USB serial ports, confirms via `id` command — returns list[CliClient]
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

The hub ID is the USB serial number assigned by the OS (e.g. `DK0F9SOT`), not the firmware `sn` field (which is zeroed on some hubs). `RestApiClient` and `JsonRpcClient` receive it directly from the service. `CliClient` reads it from `list_ports.comports()` (pyserial reads sysfs on Linux and the PnP registry on Windows — no external tools) for `SerialTransport`, or uses the stored hub ID for `ApiProxyTransport`.

Windows' FTDI driver appends the chip's channel letter to the serial number it reports
per port instance (`FTDIBUS\VID_0403+PID_6015+ABCDEFGHA\0000` → `ABCDEFGHA`), whereas
Linux reports the bare USB device serial (`ABCDEFGH`). `_normalize_usb_serial()` in
`hub_backends.py` strips that suffix on Windows for FTDI VIDs, so the same hub yields
the same `hub_id` on either platform — important because the ID keys `HubController._hubs`
and must match what the REST service reports for the same hub.

## Controller

`HubController` (`controller.py`) owns all serial port access via a single worker thread — a producer/consumer design that decouples HTTP requests from hardware I/O latency. Web routes never touch serial directly.

- `_hubs` — registry of live `HubClient` instances, keyed by hub ID; rebuilt by `_discover()` on a 60s interval, or immediately on a `discover` command
- `_command_queue` — `set_mode`, `set_mode_all`, and `discover` requests enqueued by web routes; the worker drains it before each poll, and also services it during the inter-poll wait so a queued command doesn't sit until the next cycle
- `_raw_state` — undecorated poll output; `_cache` is this plus error decoration, so a refusal can be folded in without re-reading hardware
- `_cache` / `_cache_lock` — last-known state per hub (`hub_id`, `modes`, `ports`, `error`, `health`, `stale`, `blocked`, `error_detail`); web reads take `_cache_lock` only for the list swap and never wait for hardware
- `_command_errors` — `(hub_id, port_id | None)` → `CommandError`, for commands the hub refused. `port_id=None` is a hub-wide command
- A hub that fails to poll gets an `error` entry in the cache and forces rediscovery on the next loop iteration. Its **last-known ports are retained** and flagged `stale` rather than blanked, so the UI can keep showing what the ports were doing when it dropped

### Error propagation

Errors are split by lifetime, which is the whole design:

| Source | Lifetime | Lives in | Cleared by |
|---|---|---|---|
| Firmware `E` flag, `health` flags (`UV`/`OV`/`OT`), poll failure | **State** — re-derived every poll | the poll output itself | the hardware no longer reporting it |
| A refused command (`*E<nnn>`) | **Event** — happened once | `_command_errors` | a later success, or `_COMMAND_ERROR_TTL` (30 s), or the hub being removed |

A refused command only ever *explains a click*; the reason it was refused is polled state that persists on its own, so the event can expire without the tile losing its red.

`_refresh_cache_view()` is the single decoration point, called by `_poll()` **and** by the command handlers so a refusal appears immediately rather than up to 2 s later. It computes, per port, `command_error` / `blocked` / `error_detail`, and per hub `blocked` / `error_detail` / `stale`. Both renderers (the Jinja SSR loop and `renderPort()` in `main.js`) consume `blocked` and `error_detail` rather than deciding for themselves what counts as an error — that is what keeps them from drifting.

Red and disabled are **two** concepts, per port:

- `faulted` — this port's own problem: a refused command, or the firmware `e` flag. Drives the red tile and the badge.
- `blocked` — its control is dead. `faulted` implies it, and so does a hub-wide fault.

So a hub error disables all sixteen controls but reddens only the hub header. Painting every tile red would hide the one port that is actually broken — which is exactly the case this hub produces, with five real `e` faults sitting under an otherwise healthy hub.

A refused command counts as `faulted` because whatever refused it will almost certainly refuse the retry; the 30 s TTL re-enables the button so a retry is never permanently barred. The client-side pending timeout in `main.js` (`PENDING_TTL_MS`, 10 s) must stay **below** that TTL, or a tile could return to normal while its explanation is still on screen.

A refused `set_mode_all` is recorded under `(hub_id, None)` and paints the hub header only — sixteen red tiles from one click is noise.

`set_mode(hub_id, port_id, mode)` and `set_mode_all(hub_id, mode)` just enqueue a command and return immediately (202-style, fire-and-forget); the worker applies it via `h.set_mode(port_id, mode)` — all three backends accept `port_id=None` to mean "every port on the hub" (see `HubClient.set_mode` in `hub_backends.py`).

## Web app API endpoints

The FastAPI app (`app.py`) exposes:

- `GET /` — renders `index.html` with initial hub/port state (SSR from cache)
- `GET /api/hubs` — returns `list[HubDict]` as JSON; polled every 2 s by the frontend
- `POST /api/hubs/discover` (202) — enqueues on-demand rediscovery
- `POST /api/hubs/{hub_id}/ports/{port_id}/mode` (202) — body `{"mode": "..."}`, validates against cached modes, enqueues a single-port `set_mode`
- `POST /api/hubs/{hub_id}/ports/mode` (202) — body `{"mode": "..."}`, validates against cached modes, enqueues a hub-wide `set_mode_all` (every port on the hub)
- `POST /api/debug/inject-error` (202) — **dev only**, see below

Each hub in `GET /api/hubs` carries `health` (`supply_mv`, `temperature_mc`, `error_flags`, `rebooted`), `stale`, `command_error`, `blocked` and `error_detail`; each port carries `port_error`, `command_error`, `faulted`, `blocked` and `error_detail`. All additive — nothing was removed.

### Injecting errors (dev only)

`POST /api/debug/inject-error` is registered **only** when `CAMBRIONIX_DEV_TOOLS` is set, so in a normal run it is absent from the app and from `/docs` — not merely refused. It is a separate variable from `CAMBRIONIX_DEBUG` on purpose: turning on debug logging must never open a mutation endpoint.

Body: `{hub_id?, port_id?, kind, code?, message?, flags?, clear?}` where `kind` is one of `command` (a refused set_mode — expires on the TTL), `port_fault` (the per-port `e` flag — polled, persists), `health` (hub flags: `UV`/`OV`/`OT`, or `E` for the hub-wide firmware error), or `poll` (the hub failing to poll). `{"clear": true}` removes everything injected for that hub.

Injected faults go through the same `_refresh_cache_view()` decoration as real ones, so what you see is what a genuine failure looks like — not a parallel rendering path that could diverge.

`app.py` holds a module-level `HubController` instance. Routes are read-only views of the cache except mode writes/discovery, which enqueue work for the controller's worker thread (see Controller above).

## Commit conventions

Every commit must include a `Co-Authored-By` line crediting the agent that made the change (using that agent's own name and contact).

Before every commit, check the staged diff (including commit message body) for the owner's sensitive data — not just hub serial numbers, but anything else identifying, private, or otherwise not meant for a public repo (hardware IDs, hostnames/IPs, credentials, personal file paths, etc.). This repo is public on GitHub; nothing sensitive should reach it, including in commit messages, not just file contents. If something slips into a commit that hasn't been pushed yet, fix it before it goes out rather than pushing and cleaning up after — see `git log origin/main..HEAD -p | grep <term>` to check what's actually still local. If it's already public, ask before rewriting shared history.
