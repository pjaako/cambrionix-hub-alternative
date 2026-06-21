from dataclasses import dataclass


@dataclass
class PortState:
    id: int
    attached: bool
    mode: str
    voltage_v: float | None
    current_ma: int | None
    charging_seconds: int | None
