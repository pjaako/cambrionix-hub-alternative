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

| Class | Protocol | Transport |
|---|---|---|
| `RestApiClient` | REST v4.0 | HTTP (`httpx`) |
| `JsonRpcClient` | JSON-RPC v3.9 | TCP socket |
| `CliClient` | Firmware CLI | `SerialTransport` (pyserial) or `ApiProxyTransport` (REST `/command` endpoint) |

The web app (`app.py`) uses `RestApiClient` (aliased as `CambrionixClient` in `hub_client.py`). The other backends can be used directly in scripts or swapped in if needed.

Key files:
- `hub_backends.py` — `HubClient` ABC and all three backend implementations
- `hub_client.py` — thin shim: `RestApiClient as CambrionixClient`
- `app.py` — FastAPI routes
- `models.py` — `PortState` dataclass (shared across all backends)
- `templates/index.html`, `static/main.js` — frontend

## Documentation

The primary API reference is served live by `CambrionixApiService` itself:

- **Swagger UI**: `http://localhost:43424/api/v1/swagger`
- **OpenAPI JSON**: `http://localhost:43424/openapi.json`

The `docs/` directory contains an older v3.9 JSON-RPC reference, kept for historical context only.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
*(Note: Cambrionix API documentation content is property of Cambrionix Ltd.)*
