# Backlog

Planned improvements, in roughly natural build order. Items 1–2 are independent UI polish; 3–4 depend on 5; 6 builds on 5; 7 builds on 3/4.

## 1. Hub nicknames
Serials like `DK0F9SOT` are non-human tags. Users need editable display names per hub serial.
- Store nickname → serial mapping in the controller config (item 5)
- Show nickname in hub header; serial visible but secondary

## 2. Energy (Wh) in port stats
`PortState.energy_wh` is already populated by all backends but not displayed in the UI.
- Add a `Wh` column to the port tile stats grid
- Check column width budget in the CSS grid template

## 3. Connected device model selector
When a port is `attached` and `mode === 'on'`, show a dropdown to select the device model being charged.
- Values come from the known-devices list in the controller config (item 5)
- Stored per port in controller state; persists across polls

## 4. Connected device serial number input
Same visibility conditions as item 3 (attached + on).
- Free-text input, value sent to controller and stored per port
- Feeds the charge log (item 7)

## 5. Controller config file
TOML config file read by `HubController` on startup, watched for changes. Proposed sections:
- `[hubs]` — nickname mapping (serial → display name, item 1)
- `[devices]` — known device models (item 3 dropdown)
- `[charging]` — per-device-model rules: stop condition (Wh target, time limit), preferred mode for USB 2.0 vs 3.0
- `[ports]` — per-port overrides: locked controls (disable mode toggle in UI), default mode on connect

## 6. Config editor in web UI
Edit the controller config (item 5) via the web UI — no SSH needed for operators.
- `GET /api/config` — returns current config as JSON
- `POST /api/config` — validates and writes; controller reloads
- Simple form or JSON editor in a settings panel/modal

## 7. Charge log
Write a per-port log: device model, device SN, start time, end time, Wh delivered.
- Research whether the Cambrionix Recorder API is useful here or whether to write own CSV/SQLite log
- One row per charge session (connect → disconnect or manual stop)
- Log viewer in UI is a stretch goal; file download is sufficient first
