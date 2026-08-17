from dataclasses import dataclass


@dataclass
class PortState:
    id: int
    attachment: str
    status: str
    voltage_v: float | None
    current_ma: int | None
    charging_seconds: int | None
    energy_wh: float = 0.0
