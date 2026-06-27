import socket
import json
import sys
import time
import urllib.request
import urllib.error

HOST = '127.0.0.1'
PORT = 43424


def firmware_command(hub_id, command_text, host=HOST, port=PORT):
    """Send raw text command(s) straight to the hub's own firmware CLI via
    POST /api/v1/hubs/{hubId}/command, bypassing both REST and JSON-RPC service logic.
    Returns the raw text output from the hub."""
    url = f"http://{host}:{port}/api/v1/hubs/{hub_id}/command"
    req = urllib.request.Request(url, data=command_text.encode('utf-8'), method='POST',
                                  headers={'Content-Type': 'text/plain'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode('utf-8')


def rest_list_hubs(host=HOST, port=PORT):
    """Return the serial numbers of all hubs the REST API currently sees."""
    url = f"http://{host}:{port}/api/v1/hubs"
    with urllib.request.urlopen(url, timeout=5) as resp:
        return [hub["serialNumber"] for hub in json.load(resp)["result"]]


def rest_get_port(hub_id, port_id, host=HOST, port=PORT):
    """GET a port's state via the REST API."""
    url = f"http://{host}:{port}/api/v1/hubs/{hub_id}/ports/{port_id}"
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.load(resp)["result"]


def rest_set_mode(hub_id, port_id, mode, host=HOST, port=PORT):
    """POST a port mode ('on'/'off') via the REST API."""
    url = f"http://{host}:{port}/api/v1/hubs/{hub_id}/ports/{port_id}/mode"
    req = urllib.request.Request(url, data=json.dumps({"mode": mode}).encode('utf-8'), method='POST',
                                  headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.load(resp)


def check_api(host=HOST, port=PORT):
    """Return (True, version_string) if the REST API is reachable, else (False, error_message)."""
    url = f"http://{host}:{port}/api/v1/details"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.load(resp)
            v = data["result"]["semver"]
            return True, v
    except urllib.error.URLError as e:
        return False, str(e.reason)
    except Exception as e:
        return False, str(e)


def rpc(sock, req_id, method, params=None):
    """Send a JSON-RPC request and return the result, or None on error."""
    req = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        req["params"] = params
    sock.sendall(json.dumps(req).encode('utf-8'))
    data = b""
    while True:
        chunk = sock.recv(65536)
        data += chunk
        try:
            resp = json.loads(data.decode('utf-8'))
            if 'error' in resp:
                return None
            return resp.get('result')
        except json.JSONDecodeError:
            if not chunk:
                return None


def get_port_mode(sock, handle, port):
    """Return the current Port.N.Mode value via JSON-RPC ('c', 's', 'b', or 'o')."""
    return rpc(sock, 200, "cbrx_connection_get", [handle, f"Port.{port}.Mode"])


def set_port_mode(sock, handle, port, mode):
    """Set Port.N.Mode via JSON-RPC. mode: 'c' charge, 's' sync+charge, 'b' biased, 'o' off."""
    return rpc(sock, 201, "cbrx_connection_set", [handle, f"Port.{port}.Mode", mode])


def get_port_vitals(sock, handle, port):
    """Request and print Voltage, Current, Energy, and Time-charging for a port."""
    ids = iter(range(10, 30))

    current_mA = rpc(sock, next(ids), "cbrx_connection_get", [handle, f"Port.{port}.Current_mA"])
    energy_Wh  = rpc(sock, next(ids), "cbrx_connection_get", [handle, f"Port.{port}.Energy_Wh"])
    time_sec   = rpc(sock, next(ids), "cbrx_connection_get", [handle, f"Port.{port}.TimeCharging_sec"])
    # Voltage requires PD feature set — returns None on standard hubs
    raw_10mV   = rpc(sock, next(ids), "cbrx_connection_get", [handle, f"Port.{port}.Voltage_10mV"])
    voltage_V  = raw_10mV / 100.0 if raw_10mV is not None else None

    print(f"\n=== Port {port} vitals ===")
    print(f"  V = {f'{voltage_V:.2f} V' if voltage_V is not None else 'N/A (PD feature set not available)'}")
    print(f"  I = {f'{current_mA} mA'   if current_mA is not None else 'N/A'}")
    print(f"  E = {f'{energy_Wh:.3f} Wh' if energy_Wh is not None else 'N/A'}")
    print(f"  T = {f'{time_sec} s'       if time_sec   is not None else 'N/A'}")


def test_cambrionix_api(host=HOST, port=PORT):
    ok, info = check_api(host, port)
    if not ok:
        print(f"CambrionixApiService not reachable at {host}:{port} — {info}")
        return False
    print(f"CambrionixApiService {info} reachable.")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((host, port))

            version = rpc(sock, 1, "cbrx_apiversion")
            if version:
                print(f"API Version: {version[0]}.{version[1]}")

            units = rpc(sock, 2, "cbrx_discover", ["local"])
            if not units:
                print("No Cambrionix units found.")
                return False
            print(f"Discovered {len(units)} unit(s): {units}")

            handle = rpc(sock, 3, "cbrx_connection_open", [units[0]])
            if handle is None:
                print("Could not open connection to hub.")
                return False

            ports_info = rpc(sock, 4, "cbrx_connection_get", [handle, "PortsInfo"])
            if not ports_info:
                print("Could not retrieve PortsInfo.")
                rpc(sock, 5, "cbrx_connection_close", [handle])
                return False

            # Port 0 is the hub's own FTDI serial chip, not a device port — skip it.
            # PDSync/PD hubs expose attachment via a boolean field rather than the 'A' flag.
            attached = [
                info for info in ports_info.values()
                if info.get('Port', 0) != 0 and info.get('Attached', False)
            ]

            print(f"\nAttached devices: {len(attached)}")
            for info in attached:
                print(f"  Port {info['Port']}: {info.get('Current_mA', 0)} mA  flags={info.get('Flags', '')}")

            if attached:
                # Prefer a port drawing current; fall back to the first attached port
                charging = [i for i in attached if i.get('Current_mA', 0) > 0]
                target = (charging or attached)[0]['Port']
                print(f"\nRunning vitals on port {target} (powerbank):")
                get_port_vitals(sock, handle, target)

            rpc(sock, 9, "cbrx_connection_close", [handle])
            return True

    except ConnectionRefusedError:
        print(f"Connection refused at {host}:{port}. Is the CambrionixApiService running?")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def mode_toggle_diagnostic(port_id, host=HOST, port=PORT):
    """Toggle a port off then on via JSON-RPC (bypassing the REST API) and report the resulting mode/current.

    Used to isolate whether a stuck-off port is a REST API layer bug or a deeper
    firmware/service issue: if JSON-RPC can restore 'on' state, the fault is in the REST layer.
    """
    ok, info = check_api(host, port)
    if not ok:
        print(f"CambrionixApiService not reachable at {host}:{port} — {info}")
        return False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect((host, port))

        units = rpc(sock, 1, "cbrx_discover", ["local"])
        if not units:
            print("No Cambrionix units found.")
            return False

        handle = rpc(sock, 2, "cbrx_connection_open", [units[0]])
        if handle is None:
            print("Could not open connection to hub.")
            return False

        print(f"Port.{port_id}.Mode before: {get_port_mode(sock, handle, port_id)!r}")

        print(f"\nSetting Port.{port_id}.Mode = 'o' (off) via JSON-RPC...")
        print(f"  set result: {set_port_mode(sock, handle, port_id, 'o')!r}")
        print(f"  mode after: {get_port_mode(sock, handle, port_id)!r}")
        print(f"  current_mA after: {rpc(sock, 3, 'cbrx_connection_get', [handle, f'Port.{port_id}.Current_mA'])!r}")

        print(f"\nSetting Port.{port_id}.Mode = 'c' (charge/on) via JSON-RPC...")
        print(f"  set result: {set_port_mode(sock, handle, port_id, 'c')!r}")
        print(f"  mode after: {get_port_mode(sock, handle, port_id)!r}")
        print(f"  current_mA after: {rpc(sock, 4, 'cbrx_connection_get', [handle, f'Port.{port_id}.Current_mA'])!r}")

        rpc(sock, 5, "cbrx_connection_close", [handle])
        return True


def firmware_mode_toggle_diagnostic(hub_id, port_id, host=HOST, port=PORT, pause=5):
    """Toggle a port off then on via the hub's raw firmware CLI (the /command endpoint),
    bypassing REST and JSON-RPC entirely. This is the most direct way to tell whether a
    stuck port is a firmware/hardware fault or a bug introduced by the service layers above it:
    if the firmware CLI can restore charging, the fault lives in CambrionixApiService, not the hub.

    `pause` seconds are held between each step so the change can be observed visually on the hub.
    """
    print(f"--- before ---\n{firmware_command(hub_id, f'state {port_id}\n', host, port)}")

    print(f"--- mode o {port_id} (off) ---\n{firmware_command(hub_id, f'mode o {port_id}\n', host, port)}")
    print(f"--- after off ---\n{firmware_command(hub_id, f'state {port_id}\n', host, port)}")

    print(f"(waiting {pause}s)")
    time.sleep(pause)

    print(f"--- mode c {port_id} (charge/on) ---\n{firmware_command(hub_id, f'mode c {port_id}\n', host, port)}")

    print(f"(waiting {pause}s)")
    time.sleep(pause)

    print(f"--- after on ---\n{firmware_command(hub_id, f'state {port_id}\n', host, port)}")


def sync_wakeup_diagnostic(hub_id, port_id, host=HOST, port=PORT, pause=5):
    """Test whether nudging a stuck-off port into JSON-RPC 'sync' mode wakes it back up to 'on'.

    Sequence: REST off -> pause -> JSON-RPC Port.N.Mode='s' -> pause -> REST on -> pause -> check.
    Reports REST port state at each step so it's clear whether the sync nudge had any effect.
    """
    print(f"--- before ---\n{rest_get_port(hub_id, port_id, host, port)}")

    print(f"\n--- REST mode=off ---\n{rest_set_mode(hub_id, port_id, 'off', host, port)}")
    print(f"after off: {rest_get_port(hub_id, port_id, host, port)}")
    print(f"(waiting {pause}s)")
    time.sleep(pause)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect((host, port))
        units = rpc(sock, 1, "cbrx_discover", ["local"])
        handle = rpc(sock, 2, "cbrx_connection_open", [units[0]])
        print(f"\n--- JSON-RPC Port.{port_id}.Mode = 's' (sync) ---")
        print(f"set result: {set_port_mode(sock, handle, port_id, 's')!r}")
        print(f"mode after: {get_port_mode(sock, handle, port_id)!r}")
        rpc(sock, 3, "cbrx_connection_close", [handle])
    print(f"after sync nudge: {rest_get_port(hub_id, port_id, host, port)}")
    print(f"(waiting {pause}s)")
    time.sleep(pause)

    print(f"\n--- REST mode=on ---\n{rest_set_mode(hub_id, port_id, 'on', host, port)}")
    print(f"(waiting {pause}s)")
    time.sleep(pause)
    print(f"after on: {rest_get_port(hub_id, port_id, host, port)}")


def port_info(port_id, host=HOST, port=PORT):
    """Show full state and supported modes for a specific port across all three backends."""
    from hub_backends import RestApiClient, JsonRpcClient, CliClient, ApiProxyTransport

    ok, info = check_api(host, port)
    if not ok:
        print(f"CambrionixApiService not reachable at {host}:{port} — {info}")
        return False
    print(f"CambrionixApiService {info} reachable.\n")

    rest = RestApiClient(f"http://{host}:{port}/api/v1")
    rpc  = JsonRpcClient(host, port)
    cli  = CliClient(ApiProxyTransport(rest.hub_id(), f"http://{host}:{port}/api/v1"))

    backends = [("REST", rest), ("RPC ", rpc), ("CLI ", cli)]

    print(f"--- port {port_id} state ---")
    for label, b in backends:
        p = b.get_port(port_id)
        print(f"  {label}: attached={p.attached} mode={p.mode} "
              f"V={p.voltage_v} mA={p.current_ma} s={p.charging_seconds} Wh={p.energy_wh}")

    print("\n--- supported modes ---")
    for label, b in backends:
        print(f"  {label}: {b.supported_modes()}")

    rpc.close()
    return True


def test_backends(host=HOST, port=PORT):
    """Exercise all three HubClient backends and print a comparison of their output."""
    from hub_backends import RestApiClient, JsonRpcClient, CliClient, ApiProxyTransport

    ok, info = check_api(host, port)
    if not ok:
        print(f"CambrionixApiService not reachable at {host}:{port} — {info}")
        return False
    print(f"CambrionixApiService {info} reachable.\n")

    rest = RestApiClient(f"http://{host}:{port}/api/v1")
    rpc = JsonRpcClient(host, port)
    cli = CliClient(ApiProxyTransport(rest.hub_id(), f"http://{host}:{port}/api/v1"))

    backends = [("REST", rest), ("RPC ", rpc), ("CLI ", cli)]

    print("--- hub_id ---")
    for label, b in backends:
        print(f"  {label}: {b.hub_id()}")

    print("\n--- supported_modes ---")
    for label, b in backends:
        print(f"  {label}: {b.supported_modes()}")

    print("\n--- get_ports ---")
    for label, b in backends:
        ports = b.get_ports()
        print(f"  {label}:")
        for p in ports:
            print(f"    port {p.id}: attached={p.attached} mode={p.mode} "
                  f"V={p.voltage_v} mA={p.current_ma} s={p.charging_seconds} Wh={p.energy_wh}")

    attached_ids = [p.id for p in rest.get_ports() if p.attached]
    if attached_ids:
        port_id = attached_ids[0]
        print(f"\n--- get_port({port_id}) ---")
        for label, b in backends:
            p = b.get_port(port_id)
            print(f"  {label}: attached={p.attached} mode={p.mode} "
                  f"V={p.voltage_v} mA={p.current_ma} s={p.charging_seconds} Wh={p.energy_wh}")

    rpc.close()
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "mode-test":
        mode_toggle_diagnostic(int(sys.argv[2]))
    elif len(sys.argv) > 1 and sys.argv[1] == "fw-mode-test":
        firmware_mode_toggle_diagnostic(sys.argv[2], int(sys.argv[3]))
    elif len(sys.argv) > 1 and sys.argv[1] == "sync-wakeup-test":
        sync_wakeup_diagnostic(sys.argv[2], int(sys.argv[3]))
    elif len(sys.argv) > 1 and sys.argv[1] == "backends":
        test_backends()
    elif len(sys.argv) > 2 and sys.argv[1] == "port-info":
        port_info(int(sys.argv[2]))
    else:
        test_cambrionix_api()
