# Cambrionix Hub Alternative

A Python-based application with a web GUI to control and log the charging process of devices connected to a Cambrionix Hub via the Cambrionix Hub REST API (v4.0).

## Prerequisites

- Python 3.11+
- Cambrionix Hub (with network or USB access for API calls)
- [CambrionixApiService](https://connect.cambrionix.com) v4.0+ installed and running on the host machine — required by every backend **except** `CliClient.via_serial`, which needs the service *stopped* (see [Freeing the serial port](#freeing-the-serial-port-for-cliclientvia_serial))

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd cambrionix-hub-alternative
   ```

2. **Set up the virtual environment**:

   Linux/macOS:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   Windows (PowerShell):
   ```powershell
   py -3 -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   The commands below show the Linux activation form; on Windows substitute
   `.\venv\Scripts\Activate.ps1` throughout.

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

Make sure `CambrionixApiService` is running and reachable before starting the app:

```bash
curl -s http://localhost:43424/api/v1/details | python3 -m json.tool
```

Then start the web app:

```bash
source venv/bin/activate
uvicorn app:app --reload
```

Open `http://localhost:8000` in your browser. The app polls `/api/hubs` every 2 seconds and updates the UI live. Each port tile has a radio-button toggle to set its mode; a padlock icon in the hub header unlocks buttons to set every port on that hub at once.

## Architecture

The app is built around a pluggable backend system in `hub_backends.py`. All three backends implement the same `HubClient` interface (`hub_id`, `supported_modes`, `get_ports`, `get_port`, `set_mode`):

| Class | Protocol | Instantiation |
|---|---|---|
| `RestApiClient` | REST v4.0 | `RestApiClient()` or `RestApiClient.discover()` |
| `JsonRpcClient` | JSON-RPC v3.9 | `JsonRpcClient()` or `JsonRpcClient.discover()` |
| `CliClient` | Firmware CLI | `CliClient.via_serial(tty)` / `CliClient.via_http(hub_id)` / `CliClient.discover_serial()` |

All three expose the same `HubClient` interface: `hub_id()`, `supported_modes()`, `get_ports()`, `get_port()`, `set_mode()`. The `discover()` classmethods return a list of ready-to-use instances, one per connected hub.

The web app (`app.py`, via `controller.py`) uses `hub_client.discover_hubs()`, currently wired to `CliClient.discover_serial()`. The other backends can be used directly in scripts or swapped in if needed.

Key files:
- `hub_backends.py` — `HubClient` ABC and all three backend implementations
- `hub_client.py` — `discover_hubs()` factory, currently returns `CliClient.discover_serial()`
- `controller.py` — `HubController`: background worker thread that owns serial access, polls hubs, and queues mode/discovery commands from the web routes
- `app.py` — FastAPI routes
- `models.py` — `PortState` dataclass plus `Attachment`/`Status` `StrEnum`s (shared across all backends)
- `templates/index.html`, `static/main.js` — frontend

## Which backend to use?

| Backend | `CambrionixApiService` | Hub scope | Verdict |
|---|---|---|---|
| `RestApiClient` | Required | Local + remote | Default choice |
| `CliClient.via_serial` | Not needed | Local only | Preferred for security-sensitive or service-free setups |
| `CliClient.via_http` | Required | Local + remote | CLI robustness with multi-client access |
| `JsonRpcClient` | Required | Local only | Discouraged — legacy/experimentation only |

**`RestApiClient`** is the officially endorsed Cambrionix API. It supports remote hub access via [Cambrionix Connect](https://connect.cambrionix.com) and is the right default for most use. Be aware that the service runs as root by default, contacts Cambrionix servers, and auto-downloads and installs service updates. Early versions (≤4.0.1) have known bugs; workarounds are implemented transparently in this client.

**`CliClient.via_serial`** talks directly to the hub firmware over the serial port with no background service involved — the smallest possible attack surface and the fewest moving parts. Local hubs only. Because it parses firmware CLI text output, a firmware update could silently break compatibility.

**`CliClient.via_http`** routes firmware CLI commands through the REST service's `/command` proxy endpoint, combining CLI-level directness with the multi-client access and optional cloud features the service provides. `RestApiClient` already uses this path internally for its workarounds (energy fetch, mode "on" fix), so this variant is most useful when you need to send firmware commands not exposed by the REST API.

**`JsonRpcClient`** exists for compatibility with pre-4.0 service versions and for experimentation. It has never been validated against an actual older API version. Use `RestApiClient` instead for all new code.

### Freeing the serial port for `CliClient.via_serial`

`CambrionixApiService` holds the hub's serial port **exclusively** while it runs. `CliClient.via_serial` opens the same port directly, so the two cannot coexist — `SerialTransport` opens with `exclusive=True` and will fail immediately with `SerialException`, and the service, for its part, logs "Unresponsive hub" errors and drops the hub. **Stop the service before using the serial backend.**

This affects only `CliClient.via_serial`. The other three backends (`RestApiClient`, `CliClient.via_http`, `JsonRpcClient`) all require the service to be running, so stopping it takes them offline.

**Linux:**

```bash
sudo systemctl stop CambrionixApiService
sudo systemctl start CambrionixApiService   # restore afterwards
```

**Windows** — the installer registers three separate services, all set to start automatically:

| Service | Display name | Holds the serial port? |
|---|---|---|
| `CambrionixApiService` | Cambrionix Hub API | **Yes** |
| `CambrionixRecorderService` | Cambrionix Recorder API | No — polls the API service |
| `CambrionixRelayService` | Cambrionix Relay Service | No — Cambrionix Connect tunnel |

Only `CambrionixApiService` claims the COM port, but the Recorder will spam reconnect errors once the API service is down, so stop all three. Run in an **Administrator** PowerShell (a non-elevated shell cannot control services):

```powershell
Stop-Service CambrionixApiService, CambrionixRecorderService, CambrionixRelayService

# Optional: also prevent them restarting at boot while working on the serial backend
Set-Service CambrionixApiService      -StartupType Manual
Set-Service CambrionixRecorderService -StartupType Manual
Set-Service CambrionixRelayService    -StartupType Manual
```

To restore:

```powershell
Set-Service CambrionixApiService      -StartupType Automatic
Set-Service CambrionixRecorderService -StartupType Automatic
Set-Service CambrionixRelayService    -StartupType Automatic
Start-Service CambrionixApiService, CambrionixRecorderService, CambrionixRelayService
```

macOS uses `sudo /usr/bin/CambrionixApiService --remove` to stop and `--install` to start.

**Verifying the port is free** (no admin needed). Replace `COM3` with your hub's port — find it under Device Manager → Ports, or via `Get-ItemProperty 'HKLM:\HARDWARE\DEVICEMAP\SERIALCOMM'`:

```powershell
Get-Service Cambrionix* | Select-Object Name, Status   # all should read Stopped
Test-NetConnection localhost -Port 43424               # should fail once the API service is down
$p = New-Object System.IO.Ports.SerialPort 'COM3',115200,'None',8,'One'; $p.Open(); $p.Close()
```

On Linux the equivalent check is `sudo lsof /dev/ttyUSB0` returning nothing.

If the port opens but the hub never answers, it may be stuck in the unresponsive state described in `AGENTS.md` — a corrupted firmware input buffer, usually from a command sent without the required `\r\n` terminator. A USB replug does not clear it; only unplugging the hub from its power supply does.

## Error indication

When something is wrong the UI says so instead of failing silently: the affected port tiles
and the hub header turn red, their controls are disabled, and the header carries a plain-text
explanation. Three things can trigger it:

- **A command the hub refused** — the firmware answers `*E<nnn>` (for example
  `*E422: Refused: an error flag is set`) and the tile shows that code.
- **A port error flag** — `E` in the firmware `state` output, meaning the hub will refuse
  mode changes on that port.
- **Hub health flags** — `UV`/`OV`/`OT` from the `health` command, or the hub failing to poll
  at all. A failing hub keeps its tiles, dimmed, showing the last known readings.

Health flags latch: a hub that dipped below the under-voltage threshold keeps `UV` set, and
refuses every mode change, until it is power-cycled — `cef` does not clear it.

To see the error states without waiting for real hardware to fail, set `CAMBRIONIX_DEV_TOOLS`
and use the injection route (absent entirely when the variable is unset):

```powershell
$env:CAMBRIONIX_DEV_TOOLS="1"; .\venv\Scripts\python.exe -m uvicorn app:app
$h = (Invoke-RestMethod http://localhost:8000/api/hubs)[0].hub_id
$u = "http://localhost:8000/api/debug/inject-error"
Invoke-RestMethod -Method Post $u -ContentType application/json -Body (@{hub_id=$h; port_id=3; kind="command"} | ConvertTo-Json)
Invoke-RestMethod -Method Post $u -ContentType application/json -Body (@{hub_id=$h; kind="health"; flags=@("UV")} | ConvertTo-Json)
Invoke-RestMethod -Method Post $u -ContentType application/json -Body (@{hub_id=$h; clear=$true} | ConvertTo-Json)
```

`kind` is one of `command`, `port_flag`, `health` or `poll`. `verify_ui.py` runs all four
automatically and checks both renderers agree.

## Testing and Debugging

`test_api.py` is the main diagnostic script:

```bash
source venv/bin/activate
python test_api.py                                        # basic REST API smoke test
python test_api.py backends                               # compare all three backends side-by-side
python test_api.py port-info <port_id>                    # full state + supported modes for one port
python test_api.py mode-test <port_id>                    # toggle off/on via JSON-RPC (bug diagnostic)
python test_api.py fw-mode-test <hub_id> <port_id>        # toggle via firmware CLI
python test_api.py sync-wakeup-test <hub_id> <port_id>    # nudge stuck-off port via sync
```

## Documentation

The primary API reference is served live by `CambrionixApiService` itself:

- **Swagger UI**: `http://localhost:43424/api/v1/swagger`
- **OpenAPI JSON**: `http://localhost:43424/openapi.json`

The `docs/` directory contains:
- `docs/cambrionix-cli-reference/` — the official firmware CLI reference (commands, column formats, flag meanings). Active reference for `CliClient` development.
- Older v3.9 JSON-RPC documentation, kept for historical context only.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
*(Note: Cambrionix API documentation content is property of Cambrionix Ltd.)*
