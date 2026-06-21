import socket
import json

HOST = '127.0.0.1'
PORT = 43424


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


if __name__ == "__main__":
    test_cambrionix_api()
