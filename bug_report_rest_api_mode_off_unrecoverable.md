# Bug Report: REST API port mode cannot be set back to `on` after `off`

## Environment

| | |
|---|---|
| CambrionixApiService version | 4.0.0 |
| OS | Debian GNU/Linux 13 (trixie), x64 |
| Hub | PDSync-C4, serial `DK0F9SOT`, firmware 1.3.0 |

## Summary

`POST /api/v1/hubs/{hubId}/ports/{portId}/mode` with body `{"mode": "off"}` correctly turns the port off — the port's `state.mode` updates to `"off"` and sensors drop to 0. A subsequent call to the same endpoint with `{"mode": "on"}` returns a successful response (`{"result": true}`), but the port's `state.mode` remains `"off"` and the port does not resume charging. Retrying the `"on"` call multiple times, including after a delay, does not change the outcome.

The only way found to restore the port to `"on"` is to reboot the entire hub via `POST /api/v1/hubs/{hubId}/reboot`.

## Steps to reproduce

1. Confirm port 2 is on and charging:
   ```bash
   curl -s http://localhost:43424/api/v1/hubs/DK0F9SOT/ports/2 | python3 -m json.tool
   ```
   ```json
   { "result": { "id": 2, "state": { "attached": true, "mode": "on" },
     "sensors": [{"type":"milliamps","value":1226},{"type":"volts","value":9.14}],
     "power": { "state": "charging", "charge": { "charging": { "seconds": 41 } } } } }
   ```

2. Turn the port off:
   ```bash
   curl -s -X POST http://localhost:43424/api/v1/hubs/DK0F9SOT/ports/2/mode \
     -H "Content-Type: application/json" -d '{"mode":"off"}'
   ```
   ```json
   { "result": true }
   ```
   Verified state:
   ```json
   { "result": { "id": 2, "state": { "attached": true, "mode": "off" },
     "sensors": [{"type":"milliamps","value":0},{"type":"volts","value":0.0}] } }
   ```

3. Attempt to turn the port back on:
   ```bash
   curl -s -X POST http://localhost:43424/api/v1/hubs/DK0F9SOT/ports/2/mode \
     -H "Content-Type: application/json" -d '{"mode":"on"}'
   ```
   ```json
   { "result": true }
   ```
   Verified state immediately afterward — **still off**:
   ```json
   { "result": { "id": 2, "state": { "attached": true, "mode": "off" },
     "sensors": [{"type":"milliamps","value":0},{"type":"volts","value":0.0}] } }
   ```

4. Repeating step 3 (including with a delay between request and verification) produces the same result: `{"result": true}` from the API, `mode: "off"` on re-query.

5. Reboot the hub:
   ```bash
   curl -s -X POST http://localhost:43424/api/v1/hubs/DK0F9SOT/reboot
   ```
   First attempt failed:
   ```json
   { "error": { "code": "reboot-failed", "message": "The hub is not ready" } }
   ```
   Retried immediately, succeeded. After reboot, port 2 came back as:
   ```json
   { "result": { "id": 2, "state": { "attached": true, "mode": "on" },
     "sensors": [{"type":"milliamps","value":1193},{"type":"volts","value":9.14}],
     "power": { "state": "charging", "charge": { "charging": { "seconds": 52 } } } } }
   ```

## Root cause isolation: firmware vs. service layer

To determine whether the fault is in the hub's firmware or in `CambrionixApiService`, the same off→on cycle was repeated using the hub's raw firmware CLI via `POST /api/v1/hubs/{hubId}/command` (`text/plain` body, sent straight to the hub over serial — bypassing both the REST and JSON-RPC layers of the service):

Check state, then turn the port off:

```bash
curl -s -X POST http://localhost:43424/api/v1/hubs/DK0F9SOT/command \
  -H "Content-Type: text/plain" --data-binary $'state 2\nmode o 2\nstate 2\n'
```
```
>> state 2
 2, 0918, 1079, P C -, 43, x, 0.11

>> mode o 2

>> state 2
 2, 0918, 0000, A O -, 0, x, 0.00
```

Wait 5s, then turn the port back on:

```bash
curl -s -X POST http://localhost:43424/api/v1/hubs/DK0F9SOT/command \
  -H "Content-Type: text/plain" --data-binary $'mode c 2\n'
```

Wait 5s, then check state again:

```bash
curl -s -X POST http://localhost:43424/api/v1/hubs/DK0F9SOT/command \
  -H "Content-Type: text/plain" --data-binary $'state 2\n'
```
```
>> state 2
 2, 0917, 1142, P C -, 3, x, 0.00
```

The port turns off (`A O -`, 0 mA) and back **on** (`P C -`, 1142 mA) correctly via the firmware CLI alone, with no hub reboot required. This rules out a firmware/hardware fault: the hub is fully capable of toggling the port back on. The bug is therefore confined to `CambrionixApiService` — specifically, its REST mode endpoint fails to (or refuses to) issue the equivalent "on" command down to the firmware after an "off" has been set, even though it reports `{"result": true}`.

A reusable diagnostic for this test was added to `test_api.py` as `firmware_mode_toggle_diagnostic(hub_id, port_id)` (CLI: `python test_api.py fw-mode-test <hubId> <portId>`), with a configurable pause between steps for visual observation.

### Ruled-out workaround: nudging through "sync" mode

One hypothesis was that transitioning the stuck port through an intermediate mode — JSON-RPC `Port.N.Mode = 's'` (sync+charge) — before requesting `on` again might unstick the service's internal state tracking. This was tested as `off (REST) -> pause -> sync (JSON-RPC) -> pause -> on (REST)`:

1. `POST .../mode {"mode":"off"}` → port goes off (0 mA, 0 V, confirmed after a short settle delay).
2. JSON-RPC `cbrx_connection_set [handle, "Port.2.Mode", "s"]` → returned `null` (rejected); read-back `Port.2.Mode` was `'o'`, i.e. the JSON-RPC layer also sees the port as off and refuses the sync transition.
3. `POST .../mode {"mode":"on"}` → port **stayed off** (`mode: "off"`, 0 mA, 0 V).

The sync-mode nudge does not work. The stuck state appears to be enforced consistently across both the REST and JSON-RPC layers of `CambrionixApiService`, not just one. Only the raw firmware CLI command (`mode c <portId>` via `/command`) was found to restore the port.

This test is available as `sync_wakeup_diagnostic(hub_id, port_id)` in `test_api.py` (CLI: `python test_api.py sync-wakeup-test <hubId> <portId>`).

## Impact

Any application built on this REST API that exposes an "off" control (as this project's web app does, via the port mode dropdown) cannot recover a port without rebooting the entire hub, which disconnects all other attached devices/ports. This is a one-way control for what the OpenAPI schema and `ports/modes/supported` endpoint advertise as a freely toggleable `on`/`off` mode.

## Workaround

A full hub reboot (`POST /api/v1/hubs/{hubId}/reboot`) restores the port but interrupts every other attached device on that hub.

A better, port-scoped workaround exists: send `mode c <portId>` directly to the hub's firmware CLI via `POST /api/v1/hubs/{hubId}/command` (see isolation test above). This restores the single port without touching any other port or rebooting the hub, and confirms the REST mode endpoint — not the firmware — is where the fix is needed.
