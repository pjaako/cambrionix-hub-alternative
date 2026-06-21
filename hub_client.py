import httpx
from models import PortState

_BASE = "http://localhost:43424/api/v1"


class CambrionixClient:
    def __init__(self):
        self._client = httpx.Client(timeout=5)
        self._hub_id: str | None = None
        self._supported_modes: list[str] | None = None

    def hub_id(self) -> str:
        if not self._hub_id:
            data = self._client.get(f"{_BASE}/hubs").raise_for_status().json()
            self._hub_id = data["result"][0]["serialNumber"]
        return self._hub_id

    def supported_modes(self) -> list[str]:
        if self._supported_modes is None:
            hub = self.hub_id()
            data = self._client.get(f"{_BASE}/hubs/{hub}/ports/modes/supported").raise_for_status().json()
            self._supported_modes = [m["mode"] for m in data["result"]]
        return self._supported_modes

    def get_ports(self) -> list[PortState]:
        hub = self.hub_id()
        data = self._client.get(f"{_BASE}/hubs/{hub}/ports").raise_for_status().json()
        ports = [self._parse_port(p) for p in data["result"] if p["id"] != 0]
        return sorted(ports, key=lambda p: p.id)

    def get_port(self, port_id: int) -> PortState:
        hub = self.hub_id()
        data = self._client.get(f"{_BASE}/hubs/{hub}/ports/{port_id}").raise_for_status().json()
        return self._parse_port(data["result"])

    def set_mode(self, port_id: int, mode: str) -> None:
        hub = self.hub_id()
        self._client.post(
            f"{_BASE}/hubs/{hub}/ports/{port_id}/mode",
            json={"mode": mode},
        ).raise_for_status()

    def _parse_port(self, raw: dict) -> PortState:
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
        )
