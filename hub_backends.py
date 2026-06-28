from __future__ import annotations

import json
import socket
import time
from abc import ABC, abstractmethod

import httpx
import serial

from models import PortState

_REST_BASE = "http://localhost:43424/api/v1"
_RPC_HOST = "127.0.0.1"
_RPC_PORT = 43424

# CLI uses single-char mode codes; interface uses human-readable strings
_MODE_TO_CLI = {"on": "c", "off": "o", "sync": "s", "biased": "b"}
_MODE_FROM_CLI = {"c": "on", "o": "off", "s": "sync", "b": "biased"}

# Supported modes by firmware class (fc field from `id` command / Hardware property)
_FC_MODES: dict[str, list[str]] = {
    "un": ["on", "off", "sync", "biased"],  # Universal firmware
    "ps": ["on", "off"],                     # PDSync firmware
    "sm": ["on", "off"],                     # SMART firmware (TS3-C10)
}


def _hw_to_fc(hw: str) -> str:
    """Derive firmware class from the Hardware property returned by JSON-RPC."""
    if hw.startswith("PDSync"):
        return "ps"
    if hw == "TS3-C10":
        return "sm"
    return "un"


class HubClient(ABC):
    @property
    @abstractmethod
    def hub_id(self) -> str: ...

    @abstractmethod
    def supported_modes(self) -> list[str]: ...

    @abstractmethod
    def get_ports(self) -> list[PortState]: ...

    @abstractmethod
    def get_port(self, port_id: int) -> PortState: ...

    @abstractmethod
    def set_mode(self, port_id: int, mode: str) -> None: ...


# ---------------------------------------------------------------------------
# REST API v4.0
# ---------------------------------------------------------------------------

class RestApiClient(HubClient):
    @classmethod
    def discover(cls, base: str = _REST_BASE) -> list["RestApiClient"]:
        try:
            data = httpx.get(f"{base}/hubs", timeout=5).raise_for_status().json()
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise RuntimeError(f"CambrionixApiService not reachable at {base} — is it running?") from e
        return [cls(base, h["serialNumber"]) for h in data["result"]]

    def __init__(self, base: str = _REST_BASE, hub_id: str | None = None):
        self._base = base
        self._client = httpx.Client(timeout=5)
        self._hub: str | None = hub_id
        self._modes: list[str] | None = None

    @property
    def hub_id(self) -> str:
        if not self._hub:
            data = self._client.get(f"{self._base}/hubs").raise_for_status().json()
            self._hub = data["result"][0]["serialNumber"]
        return self._hub

    def supported_modes(self) -> list[str]:
        if self._modes is None:
            hub = self.hub_id
            data = self._client.get(
                f"{self._base}/hubs/{hub}/ports/modes/supported"
            ).raise_for_status().json()
            self._modes = [m["mode"] for m in data["result"]]
        return self._modes

    def _fetch_energies(self) -> dict[int, float | None]:
        # REST API bug (confirmed ≥4.0.0, still present in 4.0.1): energy field missing
        # from port response. Fetch via firmware CLI state command as workaround.
        hub = self.hub_id
        resp = self._client.post(
            f"{self._base}/hubs/{hub}/command",
            content="state\n",
            headers={"Content-Type": "text/plain"},
        ).raise_for_status()
        energies: dict[int, float | None] = {}
        for line in resp.text.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 7:
                continue
            try:
                port_id = int(parts[0])
            except ValueError:
                continue
            try:
                energies[port_id] = float(parts[6]) if parts[6] not in ("", "x") else None
            except ValueError:
                energies[port_id] = None
        return energies

    def get_ports(self) -> list[PortState]:
        hub = self.hub_id
        data = self._client.get(f"{self._base}/hubs/{hub}/ports").raise_for_status().json()
        energies = self._fetch_energies()
        ports = [self._parse(p, energies.get(p["id"])) for p in data["result"] if p["id"] != 0]
        return sorted(ports, key=lambda p: p.id)

    def get_port(self, port_id: int) -> PortState:
        hub = self.hub_id
        data = self._client.get(
            f"{self._base}/hubs/{hub}/ports/{port_id}"
        ).raise_for_status().json()
        energies = self._fetch_energies()
        return self._parse(data["result"], energies.get(port_id))

    def set_mode(self, port_id: int, mode: str) -> None:
        hub = self.hub_id
        # REST API bug (confirmed ≥4.0.0, still present in 4.0.1): POST mode "on"
        # returns success but port stays off. Always use firmware CLI for "on".
        if mode == "on":
            self._client.post(
                f"{self._base}/hubs/{hub}/command",
                content=f"mode c {port_id}\n",
                headers={"Content-Type": "text/plain"},
            ).raise_for_status()
            return
        self._client.post(
            f"{self._base}/hubs/{hub}/ports/{port_id}/mode",
            json={"mode": mode},
        ).raise_for_status()

    def _parse(self, raw: dict, energy_wh: float | None = None) -> PortState:
        state = raw.get("state", {})
        sensors = {s["type"]: s["value"] for s in raw.get("sensors", [])}
        charging = raw.get("power", {}).get("charge", {}).get("charging", {})
        return PortState(
            id=raw["id"],
            attached=state.get("attached", False),
            mode=state.get("mode", "unknown"),
            voltage_v=sensors.get("volts"),
            current_ma=sensors.get("milliamps"),
            charging_seconds=charging.get("seconds"),
            energy_wh=energy_wh,
        )


# ---------------------------------------------------------------------------
# JSON-RPC API v3.9
# ---------------------------------------------------------------------------

class JsonRpcClient(HubClient):
    @classmethod
    def discover(cls, host: str = _RPC_HOST, port: int = _RPC_PORT) -> list["JsonRpcClient"]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect((host, port))
        except (ConnectionRefusedError, socket.timeout) as e:
            sock.close()
            raise RuntimeError(f"CambrionixApiService not reachable at {host}:{port} — is it running?") from e
        req_id = 1
        req = {"jsonrpc": "2.0", "id": req_id, "method": "cbrx_discover", "params": ["local"]}
        sock.sendall(json.dumps(req).encode())
        buf = b""
        while True:
            chunk = sock.recv(65536)
            buf += chunk
            try:
                units = json.loads(buf.decode()).get("result") or []
                break
            except json.JSONDecodeError:
                if not chunk:
                    units = []
                    break
        sock.close()
        return [cls(host, port, unit) for unit in units]

    def __init__(self, host: str = _RPC_HOST, port: int = _RPC_PORT, unit: str | None = None):
        self._host = host
        self._port = port
        self._sock: socket.socket | None = None
        self._handle: str | None = None
        self._unit: str | None = unit
        self._req_id = 0
        self._modes: list[str] | None = None

    def _connect(self) -> None:
        if self._sock is not None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((self._host, self._port))
        self._sock = sock
        if self._unit is None:
            units = self._rpc("cbrx_discover", ["local"])
            if not units:
                raise RuntimeError("No Cambrionix units found via JSON-RPC")
            self._unit = units[0]
        self._handle = self._rpc("cbrx_connection_open", [self._unit])

    def close(self) -> None:
        if self._sock:
            try:
                self._rpc("cbrx_connection_close", [self._handle])
            except Exception:
                pass
            self._sock.close()
            self._sock = None
            self._handle = None

    def _rpc(self, method: str, params=None):
        self._req_id += 1
        req: dict = {"jsonrpc": "2.0", "id": self._req_id, "method": method}
        if params is not None:
            req["params"] = params
        self._sock.sendall(json.dumps(req).encode())
        buf = b""
        while True:
            chunk = self._sock.recv(65536)
            buf += chunk
            try:
                resp = json.loads(buf.decode())
                if "error" in resp:
                    return None
                return resp.get("result")
            except json.JSONDecodeError:
                if not chunk:
                    return None

    def _get(self, key: str):
        return self._rpc("cbrx_connection_get", [self._handle, key])

    def _rpc_batch(self, requests: list[tuple[str, list]]) -> list:
        """Send multiple RPC requests in one round trip; return results in order."""
        batch = []
        for i, (method, params) in enumerate(requests):
            self._req_id += 1
            batch.append({"jsonrpc": "2.0", "id": self._req_id, "method": method, "params": params})
        self._sock.sendall(json.dumps(batch).encode())
        buf = b""
        while True:
            chunk = self._sock.recv(65536)
            buf += chunk
            try:
                responses = json.loads(buf.decode())
                by_id = {r["id"]: r.get("result") for r in responses}
                return [by_id[r["id"]] for r in batch]
            except (json.JSONDecodeError, KeyError):
                if not chunk:
                    return [None] * len(requests)

    @property
    def hub_id(self) -> str:
        self._connect()
        return self._unit

    def supported_modes(self) -> list[str]:
        if self._modes is None:
            self._connect()
            hw = self._get("Hardware") or ""
            self._modes = _FC_MODES.get(_hw_to_fc(hw), ["on", "off"])
        return self._modes

    def get_ports(self) -> list[PortState]:
        self._connect()
        ports_info = self._get("PortsInfo") or {}
        port_ids = sorted(
            info["Port"] for info in ports_info.values() if info.get("Port", 0) != 0
        )
        # Batch-fetch voltage, time, energy for all ports in one round trip
        props = ["Voltage_10mV", "TimeCharging_sec", "Energy_Wh"]
        requests = [
            ("cbrx_connection_get", [self._handle, f"Port.{pid}.{prop}"])
            for pid in port_ids
            for prop in props
        ]
        results = self._rpc_batch(requests)
        extras: dict[int, dict] = {}
        for i, pid in enumerate(port_ids):
            v10mv, t, e = results[i * 3], results[i * 3 + 1], results[i * 3 + 2]
            extras[pid] = {
                "voltage_v": round(v10mv / 100.0, 2) if v10mv is not None else None,
                "charging_seconds": t,
                "energy_wh": round(e, 2) if e is not None else None,
            }
        ports = [
            self._parse_ports_info(info, extras.get(info["Port"], {}))
            for info in ports_info.values()
            if info.get("Port", 0) != 0
        ]
        return sorted(ports, key=lambda p: p.id)

    def get_port(self, port_id: int) -> PortState:
        self._connect()
        n = port_id
        mode_char = self._get(f"Port.{n}.Mode") or ""
        attached = self._get(f"Port.{n}.Attached") or False
        current_ma = self._get(f"Port.{n}.Current_mA")
        energy_wh = self._get(f"Port.{n}.Energy_Wh")
        time_sec = self._get(f"Port.{n}.TimeCharging_sec")
        raw_10mv = self._get(f"Port.{n}.Voltage_10mV")
        voltage_v = round(raw_10mv / 100.0, 2) if raw_10mv is not None else None
        energy_wh = round(energy_wh, 2) if energy_wh is not None else None
        return PortState(
            id=port_id,
            attached=attached,
            mode=_MODE_FROM_CLI.get(mode_char, "unknown"),
            voltage_v=voltage_v,
            current_ma=current_ma,
            charging_seconds=time_sec,
            energy_wh=energy_wh,
        )

    def set_mode(self, port_id: int, mode: str) -> None:
        self._connect()
        self._rpc("cbrx_connection_set", [self._handle, f"Port.{port_id}.Mode", _MODE_TO_CLI.get(mode, mode)])

    def _parse_ports_info(self, info: dict, extras: dict = {}) -> PortState:
        flags = info.get("Flags", "")
        mode = "off" if "O" in flags else ("sync" if "S" in flags else ("biased" if "B" in flags else "on"))
        return PortState(
            id=info["Port"],
            attached=info.get("Attached", False),
            mode=mode,
            voltage_v=extras.get("voltage_v"),
            current_ma=info.get("Current_mA"),
            charging_seconds=extras.get("charging_seconds"),
            energy_wh=extras.get("energy_wh"),
        )


# ---------------------------------------------------------------------------
# CLI transports
# ---------------------------------------------------------------------------

class CliTransport(ABC):
    @abstractmethod
    def send_command(self, cmd: str) -> str: ...

    def hub_serial(self) -> str | None:
        """Return the hub's USB/OS-level serial number if known by this transport, else None."""
        return None


class SerialTransport(CliTransport):
    def __init__(self, port: str, baud_rate: int = 115200, timeout: float = 1.0):
        self._port = port
        self._baud = baud_rate
        self._timeout = timeout
        self._ser: serial.Serial | None = None

    def _ensure_open(self) -> None:
        if self._ser is None or not self._ser.is_open:
            self._ser = serial.Serial(self._port, self._baud, timeout=self._timeout)
            self._ser.reset_input_buffer()

    def send_command(self, cmd: str) -> str:
        self._ensure_open()
        self._ser.reset_input_buffer()
        self._ser.write(f"{cmd}\r\n".encode())
        response = ""
        start = time.time()
        while True:
            line = self._ser.readline().decode("utf-8", errors="ignore")
            if not line:
                if response or time.time() - start > self._timeout:
                    break
                continue
            response += line
            if ">>" in line:
                break
        return response

    def hub_serial(self) -> str | None:
        import subprocess
        try:
            out = subprocess.run(
                ["udevadm", "info", "--query=property", self._port],
                capture_output=True, text=True, timeout=3,
            ).stdout
            for line in out.splitlines():
                if line.startswith("ID_SERIAL_SHORT="):
                    return line.split("=", 1)[1]
        except Exception:
            pass
        return None

    def close(self) -> None:
        if self._ser and self._ser.is_open:
            self._ser.close()


class ApiProxyTransport(CliTransport):
    """Sends CLI commands via POST /api/v1/hubs/{hubId}/command (REST v4.0 proxy)."""

    def __init__(self, hub_id: str, base: str = _REST_BASE):
        self._hub_id = hub_id
        self._url = f"{base}/hubs/{hub_id}/command"
        self._client = httpx.Client(timeout=5)

    def hub_serial(self) -> str:
        return self._hub_id

    def send_command(self, cmd: str) -> str:
        resp = self._client.post(
            self._url,
            content=f"{cmd}\n",
            headers={"Content-Type": "text/plain"},
        )
        resp.raise_for_status()
        return resp.text


# ---------------------------------------------------------------------------
# CLI API
# ---------------------------------------------------------------------------

class CliClient(HubClient):
    @classmethod
    def discover_serial(cls) -> list["CliClient"]:
        from serial.tools import list_ports
        found = []
        for p in list_ports.comports():
            client = cls.via_serial(p.device)
            try:
                client.hub_id
            except Exception:
                continue
            found.append(client)
        return found

    @classmethod
    def via_serial(cls, tty: str = "/dev/ttyUSB0") -> "CliClient":
        return cls(SerialTransport(tty))

    @classmethod
    def via_http(cls, hub_id: str, base: str = _REST_BASE) -> "CliClient":
        return cls(ApiProxyTransport(hub_id, base))

    def __init__(self, transport: CliTransport, hub_serial: str | None = None):
        self._transport = transport
        self._hub_serial = hub_serial
        self._fc: str | None = None
        self._modes: list[str] | None = None

    @property
    def hub_id(self) -> str:
        if self._hub_serial is None:
            self._parse_id()
        return self._hub_serial

    def _parse_id(self) -> None:
        raw = self._transport.send_command("id")
        info: dict[str, str] = {}
        for line in raw.splitlines():
            if "mfr:" in line:
                for part in line.replace(">>", "").strip().split(","):
                    if ":" in part:
                        k, v = part.split(":", 1)
                        info[k.strip()] = v.strip()
                break
        if info.get("mfr", "").lower() != "cambrionix":
            raise ValueError(f"Not a Cambrionix device (mfr={info.get('mfr')!r})")
        # Prefer USB-level serial from transport (FTDI chip); firmware sn may be zeroed
        self._hub_serial = self._transport.hub_serial() or info.get("sn", "unknown")
        self._fc = info.get("fc", "")

    def supported_modes(self) -> list[str]:
        if self._modes is None:
            if self._fc is None:
                self._parse_id()
            self._modes = _FC_MODES.get(self._fc, ["on", "off"])
        return self._modes

    def get_ports(self) -> list[PortState]:
        raw = self._transport.send_command("state")
        ports = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith(("state", ">>", "Port")):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 3:
                continue
            try:
                port_id = int(parts[0])
            except ValueError:
                continue
            if port_id == 0:
                continue
            ports.append(self._parse_state_line(parts))
        return sorted(ports, key=lambda p: p.id)

    def get_port(self, port_id: int) -> PortState:
        raw = self._transport.send_command(f"state {port_id}")
        for line in raw.splitlines():
            parts = [p.strip() for p in line.strip().split(",")]
            if len(parts) >= 3:
                try:
                    if int(parts[0]) == port_id:
                        return self._parse_state_line(parts)
                except ValueError:
                    continue
        raise RuntimeError(f"Port {port_id} not found in state output")

    def set_mode(self, port_id: int, mode: str) -> None:
        cli_mode = _MODE_TO_CLI.get(mode, mode)
        self._transport.send_command(f"mode {cli_mode} {port_id}")

    def _parse_state_line(self, parts: list[str]) -> PortState:
        # PDSync column order: port, voltage_10mV, current_mA, flags, time_s, energy_mwh_or_x, power_W
        def _int(v: str) -> int | None:
            try:
                return int(v)
            except (ValueError, TypeError):
                return None

        port_id = _int(parts[0]) or 0
        voltage_10mv = _int(parts[1]) if len(parts) > 1 else None
        current_ma = _int(parts[2]) if len(parts) > 2 else None
        flags = set(parts[3].split()) if len(parts) > 3 else set()
        time_sec = _int(parts[4]) if len(parts) > 4 else None
        # parts[5] = time_charged ('x' while still charging — skip)
        energy_str = parts[6].strip() if len(parts) > 6 else None
        try:
            energy_wh = float(energy_str) if energy_str and energy_str != "x" else None
        except ValueError:
            energy_wh = None

        mode = "off" if "O" in flags else ("sync" if "S" in flags else ("biased" if "B" in flags else "on"))
        attached = "D" not in flags  # D = Detached flag

        return PortState(
            id=port_id,
            attached=attached,
            mode=mode,
            voltage_v=voltage_10mv / 100.0 if voltage_10mv is not None else None,
            current_ma=current_ma,
            charging_seconds=time_sec,
            energy_wh=energy_wh,
        )
