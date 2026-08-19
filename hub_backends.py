from __future__ import annotations

import json
import logging
import socket
import sys
import time
from abc import ABC, abstractmethod

import httpx
import serial

from models import Attachment, PortState, Status

_REST_BASE = "http://localhost:43424/api/v1"
_RPC_HOST = "127.0.0.1"
_RPC_PORT = 43424

# CLI uses single-char mode codes; interface uses human-readable strings
_MODE_TO_CLI = {"on": "c", "off": "o", "sync": "s", "biased": "b"}
_MODE_FROM_CLI = {"c": "on", "o": "off", "s": "sync", "b": "biased"}

# Column 1 (Attachment) flag letters -> canonical value, PDSync / TS3-C10 firmware
_ATTACHMENT_MAP = {"A": Attachment.ATTACHED, "D": Attachment.DETACHED,
                    "P": Attachment.PD_CONTRACT, "C": Attachment.TYPE_C_ONLY}

# Column 2 (Status) flag letters -> canonical value, PDSync / TS3-C10 firmware
_STATUS_MAP = {"I": Status.IDLE, "S": Status.HOST_CONNECTED, "C": Status.CHARGING,
               "F": Status.FINISHED, "O": Status.OFF, "c": Status.POWER_NO_DEVICE}

# Universal firmware: single combined flag column, mutually exclusive per the
# firmware docs (docs/cambrionix-cli-reference/02-commands-n-z-and-deprecated.md:66-77)
_UNIVERSAL_STATUS_MAP = {"O": Status.OFF, "S": Status.SYNC, "B": Status.BIASED, "I": Status.IDLE,
                          "P": Status.PROFILING, "C": Status.CHARGING, "F": Status.FINISHED}


def _universal_status(flags: set[str]) -> Status:
    return next((v for k, v in _UNIVERSAL_STATUS_MAP.items() if k in flags), Status.UNKNOWN)


# REST API power.state values -> canonical status (best-effort, see RestApiClient._parse)
_REST_STATUS_MAP = {"charging": Status.CHARGING, "idle": Status.IDLE,
                     "finished": Status.FINISHED, "off": Status.OFF}

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


logger = logging.getLogger(__name__)


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
    def set_mode(self, port_id: int | None, mode: str) -> None:
        """port_id=None applies the mode to every port on the hub."""
        ...


# ---------------------------------------------------------------------------
# REST API v4.0
# ---------------------------------------------------------------------------

class RestApiClient(HubClient):
    @classmethod
    def discover(cls, base: str = _REST_BASE) -> list["RestApiClient"]:
        try:
            resp = httpx.get(f"{base}/hubs", timeout=5)
            logger.debug("REST GET %s -> %s", f"{base}/hubs", resp.text)
            data = resp.raise_for_status().json()
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
            resp = self._client.get(f"{self._base}/hubs")
            logger.debug("REST GET %s -> %s", f"{self._base}/hubs", resp.text)
            data = resp.raise_for_status().json()
            self._hub = data["result"][0]["serialNumber"]
        return self._hub

    def supported_modes(self) -> list[str]:
        if self._modes is None:
            hub = self.hub_id
            url = f"{self._base}/hubs/{hub}/ports/modes/supported"
            resp = self._client.get(url)
            logger.debug("REST GET %s -> %s", url, resp.text)
            data = resp.raise_for_status().json()
            self._modes = [m["mode"] for m in data["result"]]
        return self._modes

    def _fetch_energies(self) -> dict[int, int]:
        # REST API bug (confirmed ≥4.0.0, still present in 4.0.1): energy field missing
        # from port response. Fetch via firmware CLI state command as workaround.
        hub = self.hub_id
        url = f"{self._base}/hubs/{hub}/command"
        resp = self._client.post(
            url,
            content="state\n",
            headers={"Content-Type": "text/plain"},
        )
        logger.debug("REST POST %s (state) -> %s", url, resp.text)
        resp.raise_for_status()
        energies: dict[int, int] = {}
        for line in resp.text.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 7:
                continue
            try:
                port_id = int(parts[0])
            except ValueError:
                continue
            try:
                energies[port_id] = round(float(parts[6]) * 1000) if parts[6] not in ("", "x") else 0
            except ValueError:
                energies[port_id] = 0
        return energies

    def get_ports(self) -> list[PortState]:
        hub = self.hub_id
        url = f"{self._base}/hubs/{hub}/ports"
        resp = self._client.get(url)
        logger.debug("REST GET %s -> %s", url, resp.text)
        data = resp.raise_for_status().json()
        energies = self._fetch_energies()
        ports = [self._parse(p, energies.get(p["id"], 0)) for p in data["result"] if p["id"] != 0]
        return sorted(ports, key=lambda p: p.id)

    def get_port(self, port_id: int) -> PortState:
        hub = self.hub_id
        url = f"{self._base}/hubs/{hub}/ports/{port_id}"
        resp = self._client.get(url)
        logger.debug("REST GET %s -> %s", url, resp.text)
        data = resp.raise_for_status().json()
        energies = self._fetch_energies()
        return self._parse(data["result"], energies.get(port_id, 0))

    def set_mode(self, port_id: int | None, mode: str) -> None:
        hub = self.hub_id
        if port_id is None:
            url = f"{self._base}/hubs/{hub}/ports/mode"
            resp = self._client.post(url, json={"mode": mode})
            logger.debug("REST POST %s (mode=%s, all ports) -> %s", url, mode, resp.text)
            resp.raise_for_status()
            return
        # REST API bug (confirmed ≥4.0.0, still present in 4.0.1): POST mode "on"
        # returns success but port stays off. Always use firmware CLI for "on".
        if mode == "on":
            url = f"{self._base}/hubs/{hub}/command"
            resp = self._client.post(
                url,
                content=f"mode c {port_id}\n",
                headers={"Content-Type": "text/plain"},
            )
            logger.debug("REST POST %s (mode c %d) -> %s", url, port_id, resp.text)
            resp.raise_for_status()
            return
        url = f"{self._base}/hubs/{hub}/ports/{port_id}/mode"
        resp = self._client.post(
            url,
            json={"mode": mode},
        )
        logger.debug("REST POST %s (mode=%s) -> %s", url, mode, resp.text)
        resp.raise_for_status()

    def _parse(self, raw: dict, energy_mwh: int = 0) -> PortState:
        state = raw.get("state", {})
        sensors = {s["type"]: s["value"] for s in raw.get("sensors", [])}
        power = raw.get("power", {})
        charging = power.get("charge", {}).get("charging", {})
        attachment = Attachment.ATTACHED if state.get("attached", False) else Attachment.DETACHED
        # Best-effort: power.state mirrors the CLI Status column but only "charging"
        # has been observed against a live hub in this repo; other values are inferred
        # from the CLI naming. Verify against a live hub before relying on values
        # other than "charging".
        raw_status = power.get("state", "")
        status = _REST_STATUS_MAP.get(raw_status, Status.UNKNOWN)
        return PortState(
            id=raw["id"],
            attachment=attachment,
            status=status,
            voltage_mv=round(sensors.get("volts", 0.0) * 1000),
            current_ma=sensors.get("milliamps") or 0,
            charging_seconds=charging.get("seconds", 0),
            energy_mwh=energy_mwh,
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
        req_str = json.dumps(req)
        logger.debug("RPC SEND (discover) -> %s", req_str)
        sock.sendall(req_str.encode())
        buf = b""
        while True:
            chunk = sock.recv(65536)
            buf += chunk
            logger.debug("RPC RECV (discover) <- %s", chunk)
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
        req_str = json.dumps(req)
        logger.debug("RPC SEND (%s) -> %s", method, req_str)
        self._sock.sendall(req_str.encode())
        buf = b""
        while True:
            chunk = self._sock.recv(65536)
            buf += chunk
            logger.debug("RPC RECV (%s) <- %s", method, chunk)
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
        req_str = json.dumps(batch)
        logger.debug("RPC SEND (batch) -> %s", req_str)
        self._sock.sendall(req_str.encode())
        buf = b""
        while True:
            chunk = self._sock.recv(65536)
            buf += chunk
            logger.debug("RPC RECV (batch) <- %s", chunk)
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
                "voltage_mv": v10mv * 10 if v10mv is not None else 0,
                "charging_seconds": t or 0,
                "energy_mwh": round(e * 1000) if e is not None else 0,
            }
        ports = [
            self._parse_ports_info(info, extras.get(info["Port"], {}))
            for info in ports_info.values()
            if info.get("Port", 0) != 0
        ]
        return sorted(ports, key=lambda p: p.id)

    def get_port(self, port_id: int) -> PortState:
        self._connect()
        ports_info = self._get("PortsInfo") or {}
        info = next((i for i in ports_info.values() if i.get("Port") == port_id), None)
        if info is None:
            raise RuntimeError(f"Port {port_id} not found")
        props = ["Voltage_10mV", "TimeCharging_sec", "Energy_Wh"]
        v10mv, time_sec, energy_wh = self._rpc_batch([
            ("cbrx_connection_get", [self._handle, f"Port.{port_id}.{prop}"])
            for prop in props
        ])
        return self._parse_ports_info(info, {
            "voltage_mv": v10mv * 10 if v10mv is not None else 0,
            "charging_seconds": time_sec or 0,
            "energy_mwh": round(energy_wh * 1000) if energy_wh is not None else 0,
        })

    def set_mode(self, port_id: int | None, mode: str) -> None:
        self._connect()
        key = "mode" if port_id is None else f"Port.{port_id}.Mode"
        self._rpc("cbrx_connection_set", [self._handle, key, _MODE_TO_CLI.get(mode, mode)])

    def _parse_ports_info(self, info: dict, extras: dict = {}) -> PortState:
        flag_tokens = info.get("Flags", "").split()
        flags = set(flag_tokens)
        if "Attached" in info:
            # Best-effort, unverified against a live hub: per test_api.py, PDSync/PD
            # hubs report attachment via a separate boolean rather than the 'A' flag,
            # so Flags is assumed to hold Status(+QC) only here.
            attachment = Attachment.ATTACHED if info.get("Attached") else Attachment.DETACHED
            status = _STATUS_MAP.get(flag_tokens[0], Status.UNKNOWN) if flag_tokens else Status.UNKNOWN
        else:
            attachment = Attachment.DETACHED if "D" in flags else Attachment.ATTACHED
            status = _universal_status(flags)
        return PortState(
            id=info["Port"],
            attachment=attachment,
            status=status,
            voltage_mv=extras.get("voltage_mv", 0),
            current_ma=info.get("Current_mA") or 0,
            charging_seconds=extras.get("charging_seconds", 0),
            energy_mwh=extras.get("energy_mwh", 0),
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


# Cambrionix hubs expose their firmware CLI over an FTDI USB-serial chip. Windows'
# FTDI driver appends the chip's channel letter to the serial number it reports for
# each port instance (FTDIBUS\VID_0403+PID_6015+ABCDEFGHA\0000 -> "ABCDEFGHA"),
# while Linux reports the bare USB device serial ("ABCDEFGH"). Strip the suffix so
# the same hub yields the same hub_id on either platform.
_FTDI_VID = 0x0403
_FTDI_CHANNELS = frozenset("ABCD")  # FT4232H is the widest FTDI part, 4 channels


def _normalize_usb_serial(info) -> str | None:
    sn = info.serial_number
    if not sn:
        return None
    if sys.platform == "win32" and info.vid == _FTDI_VID and len(sn) > 1 and sn[-1] in _FTDI_CHANNELS:
        return sn[:-1]
    return sn


def _usb_serial_for_port(port: str) -> str | None:
    """USB serial number the OS assigned to `port`, or None if it can't be determined.

    Works on Linux and Windows via pyserial's port enumeration, which reads sysfs
    and the PnP registry respectively — no external tools involved.
    """
    from serial.tools import list_ports
    for info in list_ports.comports():
        if info.device == port:
            return _normalize_usb_serial(info)
    return None


class SerialTransport(CliTransport):
    def __init__(self, port: str, baud_rate: int = 115200, timeout: float = 1.0):
        self._port = port
        self._baud = baud_rate
        self._timeout = timeout
        self._ser: serial.Serial | None = None

    def _ensure_open(self) -> None:
        if self._ser is None or not self._ser.is_open:
            # exclusive=True prevents a second connection (e.g. a concurrent
            # rediscovery probe) from silently interleaving reads/writes on
            # the same tty and corrupting responses; it fails loudly instead.
            self._ser = serial.Serial(self._port, self._baud, timeout=self._timeout, exclusive=True)
            self._ser.reset_input_buffer()

    def send_command(self, cmd: str) -> str:
        try:
            self._ensure_open()
            self._ser.reset_input_buffer()
            logger.debug("SERIAL SEND [%s] -> %r", self._port, cmd)
            self._ser.write(f"{cmd}\r\n".encode())
            response = ""
            start = time.time()
            deadline = start + self._timeout  # idle deadline: pushed out each time data arrives
            hard_deadline = start + max(self._timeout * 5, 5.0)  # absolute cap in case the hub never goes idle
            while True:
                now = time.time()
                if now >= deadline or now >= hard_deadline:
                    break
                if self._ser.in_waiting > 0:
                    chunk = self._ser.read(self._ser.in_waiting).decode("utf-8", errors="ignore")
                    if chunk:
                        response += chunk
                        deadline = time.time() + self._timeout
                        if ">>" in response:
                            break
                else:
                    time.sleep(0.01)
            logger.debug("SERIAL RECV [%s] <-\n%s", self._port, response)
            return response
        except serial.SerialException:
            raise
        except OSError as e:
            self._ser = None  # force reopen on next call
            raise serial.SerialException(f"{self._port}: {e}") from e

    def hub_serial(self) -> str | None:
        return _usb_serial_for_port(self._port)

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
        logger.debug("API PROXY SEND (%s) -> %r", self._hub_id, cmd)
        resp = self._client.post(
            self._url,
            content=f"{cmd}\n",
            headers={"Content-Type": "text/plain"},
        )
        resp.raise_for_status()
        logger.debug("API PROXY RECV (%s) <- %s", self._hub_id, resp.text)
        return resp.text

    def close(self) -> None:
        self._client.close()


# ---------------------------------------------------------------------------
# CLI API
# ---------------------------------------------------------------------------

class CliClient(HubClient):
    @classmethod
    def _classify_usb_serial(cls) -> tuple[list["CliClient"], int, int]:
        """Probe all USB serial ports in one pass.

        Returns (hubs, inaccessible_count, other_count).
        inaccessible: port opened but OS rejected it (busy, permission denied).
        other: port opened but did not respond as a Cambrionix hub.
        """
        from serial.tools import list_ports
        hubs, inaccessible, other = [], 0, 0
        for p in list_ports.comports():
            if p.vid is None:
                continue
            client = cls.via_serial(p.device)
            try:
                client.hub_id
                hubs.append(client)
            except serial.SerialException:
                inaccessible += 1
                client.close()
            except Exception:
                other += 1
                client.close()
        return hubs, inaccessible, other

    @classmethod
    def discover_serial(cls) -> list["CliClient"]:
        hubs, _, _ = cls._classify_usb_serial()
        return hubs

    @classmethod
    def discover_http(cls, base: str = _REST_BASE) -> list["CliClient"]:
        try:
            data = httpx.get(f"{base}/hubs", timeout=5).raise_for_status().json()
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise RuntimeError(f"CambrionixApiService not reachable at {base} — is it running?") from e
        return [cls.via_http(h["serialNumber"], base) for h in data["result"]]

    @classmethod
    def via_serial(cls, tty: str) -> "CliClient":
        """`tty` is an OS port name: "/dev/ttyUSB0" on Linux, "COM3" on Windows."""
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

    def close(self) -> None:
        self._transport.close()

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
        self.hub_id  # ensure self._fc is populated
        supply_mv = self._supply_voltage_mv() if self._fc == "un" else None
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
            ports.append(self._parse_state_line(parts, supply_mv))
        return sorted(ports, key=lambda p: p.id)

    def get_port(self, port_id: int) -> PortState:
        self.hub_id  # ensure self._fc is populated
        supply_mv = self._supply_voltage_mv() if self._fc == "un" else None
        raw = self._transport.send_command(f"state {port_id}")
        for line in raw.splitlines():
            parts = [p.strip() for p in line.strip().split(",")]
            if len(parts) >= 3:
                try:
                    if int(parts[0]) == port_id:
                        return self._parse_state_line(parts, supply_mv)
                except ValueError:
                    continue
        raise RuntimeError(f"Port {port_id} not found in state output")

    def set_mode(self, port_id: int | None, mode: str) -> None:
        cli_mode = _MODE_TO_CLI.get(mode, mode)
        cmd = f"mode {cli_mode}" if port_id is None else f"mode {cli_mode} {port_id}"
        self._transport.send_command(cmd)

    def _supply_voltage_mv(self) -> int | None:
        # Universal firmware doesn't report per-port voltage in `state` (all ports
        # on these USB2 hubs are paralleled onto one supply rail anyway), but `health`
        # reports the shared rail. Observed live-hub format is "5V Now:   5.13" (volts);
        # the CLI reference docs (docs/cambrionix-cli-reference) instead show "5V_V1: 5042"
        # (mV) — handle both since we've only verified one hub against real hardware.
        raw = self._transport.send_command("health")
        for line in raw.splitlines():
            line = line.strip()
            if line.lower().startswith("5v now"):
                try:
                    return round(float(line.split(":", 1)[1].strip()) * 1000)
                except (ValueError, IndexError):
                    return None
            if line.startswith("5V_V1"):
                try:
                    return int(line.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    return None
        return None

    def _parse_state_line(self, parts: list[str], supply_mv: int | None = None) -> PortState:
        # PDSync: port, voltage_10mV, current_mA, flags, time_s, time_charged_or_x, energy_Wh_or_x
        # Universal: port, current_mA, flags, profile_id, time_s, time_charged_or_x, energy_Wh_or_x
        def _int(v: str) -> int | None:
            try:
                return int(v)
            except (ValueError, TypeError):
                return None

        port_id = _int(parts[0]) or 0
        
        if self._fc == "un":
            current_ma = _int(parts[1]) if len(parts) > 1 else None
            flags_idx = 2
        else:
            voltage_10mv = _int(parts[1]) if len(parts) > 1 else None
            current_ma = _int(parts[2]) if len(parts) > 2 else None
            flags_idx = 3

        flags_str = parts[flags_idx] if len(parts) > flags_idx else ""
        flag_tokens = flags_str.split()
        flags = set(flag_tokens)

        time_sec = _int(parts[4]) if len(parts) > 4 else None
        energy_str = parts[6].strip() if len(parts) > 6 else None
        try:
            energy_mwh = round(float(energy_str) * 1000) if energy_str and energy_str != "x" else 0
        except ValueError:
            energy_mwh = 0

        if self._fc == "un":
            attachment = Attachment.DETACHED if "D" in flags else Attachment.ATTACHED
            status = _universal_status(flags)
        else:
            # PDSync / TS3-C10: flag_tokens are positional (Attachment, Status, QC)
            attachment = _ATTACHMENT_MAP.get(flag_tokens[0], Attachment.UNKNOWN) if flag_tokens else Attachment.UNKNOWN
            status = _STATUS_MAP.get(flag_tokens[1], Status.UNKNOWN) if len(flag_tokens) > 1 else Status.UNKNOWN

        return PortState(
            id=port_id,
            attachment=attachment,
            status=status,
            voltage_mv=supply_mv if self._fc == "un" else (voltage_10mv * 10 if voltage_10mv is not None else None),
            current_ma=current_ma or 0,
            charging_seconds=time_sec,
            energy_mwh=energy_mwh,
        )
