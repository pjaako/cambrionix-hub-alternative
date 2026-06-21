# Cambrionix Hub Alternative

A Python-based application with a web GUI to control and log the charging process of devices connected to a Cambrionix Hub via the Cambrionix Hub REST API (v4.0).

## Prerequisites

- Python 3.8+
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
   *(Dependencies will be added as development progresses)*
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

## Documentation

The primary API reference is served live by `CambrionixApiService` itself:

- **Swagger UI**: `http://localhost:43424/api/v1/swagger`
- **OpenAPI JSON**: `http://localhost:43424/openapi.json`

The `docs/` directory contains an older v3.9 JSON-RPC reference, kept for historical context only.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
*(Note: Cambrionix API documentation content is property of Cambrionix Ltd.)*
