from dataclasses import dataclass
from enum import StrEnum


class Attachment(StrEnum):
    ATTACHED = "attached"
    DETACHED = "detached"
    PD_CONTRACT = "pd_contract"
    TYPE_C_ONLY = "type_c_only"
    UNKNOWN = "unknown"


class Status(StrEnum):
    IDLE = "idle"
    HOST_CONNECTED = "host_connected"
    CHARGING = "charging"
    FINISHED = "finished"
    OFF = "off"
    POWER_NO_DEVICE = "power_no_device"
    SYNC = "sync"
    BIASED = "biased"
    PROFILING = "profiling"
    UNKNOWN = "unknown"


@dataclass
class PortState:
    id: int
    attachment: Attachment
    status: Status
    voltage_mv: int | None
    current_ma: int
    charging_seconds: int | None
    energy_mwh: int = 0
