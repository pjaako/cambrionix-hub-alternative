# Known CambrionixApiService bugs

Bug reports found while building this app against the v4.0 REST API, kept separately from the
main docs since they describe defects in the upstream service, not this project. Each report
includes environment details, exact repro steps (request/response pairs), and a workaround
where one exists.

| Report | Summary | Workaround |
|---|---|---|
| [bug_report_rest_api_missing_energy_wh.md](bug_report_rest_api_missing_energy_wh.md) | `GET .../ports/{portId}` omits the `energy` field required by its own OpenAPI schema. Confirmed ≥4.0.0, still present in 4.0.1. | **Implemented:** `RestApiClient._fetch_energies()` sends a `state` CLI command via `/command` and merges the result into REST responses. |
| [bug_report_rest_api_mode_off_unrecoverable.md](bug_report_rest_api_mode_off_unrecoverable.md) | `POST .../ports/{portId}/mode {"mode":"on"}` reports success while the port stays off after a prior `"off"`. Root-caused to the service layer, not the firmware. Confirmed ≥4.0.0, still present in 4.0.1. | **Implemented:** `RestApiClient.set_mode("on")` bypasses the broken endpoint and sends `mode c <portId>` via the firmware CLI `/command` proxy directly. |

## Reproduction scripts

- `reproduce_mode_off_bug.py` — demonstrates the mode-off bug end to end: toggles a port via the
  firmware CLI (works), then via the REST API (fails to come back on), then revives it via the
  firmware CLI again. Run from the project root:
  ```bash
  source venv/bin/activate
  python bugs/reproduce_mode_off_bug.py [hubId] [portId]
  ```
  If `hubId` is omitted, the first hub from `GET /api/v1/hubs` is used. `portId` defaults to 2.

`test_api.py` (project root) also has interactive diagnostics used while isolating these bugs —
see its `mode-test`, `fw-mode-test`, and `sync-wakeup-test` CLI subcommands.
