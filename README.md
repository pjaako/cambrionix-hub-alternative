# Cambrionix Hub Alternative

A Python-based application with a web GUI to control and log the charging process of devices connected to a Cambrionix Hub via the Cambrionix Hub REST API (v4.0).

## Prerequisites

- Python 3.11+
- Cambrionix Hub (with network or USB access for API calls)
- [CambrionixApiService](https://connect.cambrionix.com) v4.0+ installed and running on the host machine

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd cambrionix-hub-alternative
   ```

2. **Set up the virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

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

Open `http://localhost:8000` in your browser. The app polls `/api/ports` every 2 seconds and updates the UI live. Port mode can be set via the dropdown on each port card.

## Architecture

The app is built around a pluggable backend system in `hub_backends.py`. All three backends implement the same `HubClient` interface (`hub_id`, `supported_modes`, `get_ports`, `get_port`, `set_mode`):

| Class | Protocol | Instantiation |
|---|---|---|
| `RestApiClient` | REST v4.0 | `RestApiClient()` or `RestApiClient.discover()` |
| `JsonRpcClient` | JSON-RPC v3.9 | `JsonRpcClient()` or `JsonRpcClient.discover()` |
| `CliClient` | Firmware CLI | `CliClient.via_serial(tty)` / `CliClient.via_http(hub_id)` / `CliClient.discover_serial()` |

All three expose the same `HubClient` interface: `hub_id()`, `supported_modes()`, `get_ports()`, `get_port()`, `set_mode()`. The `discover()` classmethods return a list of ready-to-use instances, one per connected hub.

The web app (`app.py`) uses `RestApiClient` (aliased as `CambrionixClient` in `hub_client.py`). The other backends can be used directly in scripts or swapped in if needed.

Key files:
- `hub_backends.py` — `HubClient` ABC and all three backend implementations
- `hub_client.py` — thin shim: `RestApiClient as CambrionixClient`
- `app.py` — FastAPI routes
- `models.py` — `PortState` dataclass (shared across all backends)
- `templates/index.html`, `static/main.js` — frontend

## Which backend to use?

| Backend | `CambrionixApiService` | Hub scope | Verdict |
|---|---|---|---|
| `RestApiClient` | Required | Local + remote | Default choice |
| `CliClient.via_serial` | Not needed | Local only | Preferred for security-sensitive or service-free setups |
| `CliClient.via_http` | Required | Local only | CLI robustness with multi-client access |
| `JsonRpcClient` | Required | Local only | Discouraged — legacy/experimentation only |

**`RestApiClient`** is the officially endorsed Cambrionix API. It supports remote hub access via [Cambrionix Connect](https://connect.cambrionix.com) and is the right default for most use. Be aware that the service runs as root by default, contacts Cambrionix servers, and auto-downloads and installs service updates. Early versions (≤4.0.1) have known bugs; workarounds are implemented transparently in this client.

**`CliClient.via_serial`** talks directly to the hub firmware over the serial port with no background service involved — the smallest possible attack surface and the fewest moving parts. Local hubs only. Because it parses firmware CLI text output, a firmware update could silently break compatibility.

**`CliClient.via_http`** routes firmware CLI commands through the REST service's `/command` proxy endpoint, combining CLI-level directness with the multi-client access and optional cloud features the service provides. `RestApiClient` already uses this path internally for its workarounds (energy fetch, mode "on" fix), so this variant is most useful when you need to send firmware commands not exposed by the REST API.

**`JsonRpcClient`** exists for compatibility with pre-4.0 service versions and for experimentation. It has never been validated against an actual older API version. Use `RestApiClient` instead for all new code.

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
