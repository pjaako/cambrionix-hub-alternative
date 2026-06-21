# Bug Report: REST API v4 port endpoint omits `energy` field required by its own OpenAPI schema

## Environment

| | |
|---|---|
| CambrionixApiService version | 4.0.0 (build 1227) |
| Commit | `74288a86d3d64cc9ff6c9c8729540c8e80e503f1` |
| Branch | release |
| OS | Debian GNU/Linux 13 (trixie), x64 |
| Hub | PDSync-C4, serial `DK0F9SOT`, firmware 1.0.4 → **1.3.0 (still affected)** |

## Summary

`GET /api/v1/hubs/{hubId}/ports/{portId}` returns a `power.charge` object that is missing the `energy` field. This field is declared **`required`** in the service's own OpenAPI schema (`/api/v1/hubs/hubId/ports/schemas.json`, `Charging` and `Charged` schemas). The implementation does not comply with the specification shipped with the same build.

The same energy data is available and accurate via the JSON-RPC API (`Port.N.Energy_Wh`), confirming the service computes it correctly — it is simply not surfaced in the REST response.

## OpenAPI schema (from `/api/v1/hubs/hubId/ports/schemas.json`)

The `Charging` schema marks `energy` as required alongside `charging`:

```json
"Charging": {
  "type": "object",
  "properties": {
    "charging": { "$ref": "#/components/schemas/Seconds" },
    "energy":   { "$ref": "#/components/schemas/Energy"  }
  },
  "required": ["charging", "energy"]
}
```

The `Charged` schema likewise marks `energy` as required:

```json
"Charged": {
  "type": "object",
  "properties": {
    "charging": { "$ref": "#/components/schemas/Seconds" },
    "finished": { "$ref": "#/components/schemas/Seconds" },
    "energy":   { "$ref": "#/components/schemas/Energy"  }
  },
  "required": ["charging", "finished", "energy"]
}
```

The `Energy` schema:

```json
"Energy": {
  "type": "object",
  "properties": {
    "used": { "type": "number", "description": "The energy consumed in milliwatt-hours" },
    "unit": { "type": "string", "enum": ["mWh"] }
  },
  "required": ["used", "unit"]
}
```

## Actual vs. expected response

**Request:**

```bash
curl http://localhost:43424/api/v1/hubs/DK0F9SOT/ports/1
```

Port 1 is actively charging (~14 W, 26 minutes into session).

**Actual response** (`energy` absent, schema violation):

```json
{
  "result": {
    "id": 1,
    "state": { "attached": true, "mode": "on" },
    "sensors": [
      { "type": "milliamps", "value": 1543 },
      { "type": "volts",     "value": 9.24  }
    ],
    "power": {
      "state": "charging",
      "charge": {
        "charging": { "seconds": 1603 }
      }
    }
  }
}
```

**Expected response** (per schema):

```json
{
  "result": {
    "id": 1,
    "state": { "attached": true, "mode": "on" },
    "sensors": [
      { "type": "milliamps", "value": 1543 },
      { "type": "volts",     "value": 9.24  }
    ],
    "power": {
      "state": "charging",
      "charge": {
        "charging": { "seconds": 1603 },
        "energy":   { "used": 5510, "unit": "mWh" }
      }
    }
  }
}
```

## Proof the value is computed correctly

The same service returns the correct accumulated energy via JSON-RPC at the same moment:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "cbrx_connection_get",
  "params": [<handle>, "Port.1.Energy_Wh"] }
```

```json
{ "jsonrpc": "2.0", "id": 1, "result": 5.51 }
```

5.51 Wh = 5510 mWh. The value accumulates correctly (observed growing from 0.73 → 1.09 → 5.51 Wh across three samples over ~26 minutes). The data exists; it is not being included in the REST response.

## Impact

Energy tracking per charging session is the primary use case for third-party applications building on this API. Because the REST API is the current recommended interface (v4.0), and because the schema explicitly promises this field, clients written against the published spec will receive invalid responses. The only workaround is to maintain a parallel JSON-RPC client solely for this one field.

## Workaround

Query `Port.N.Energy_Wh` via JSON-RPC over TCP on port 43424 in parallel with REST API calls.
