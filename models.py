from dataclasses import dataclass, field
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
    # Firmware `e` flag: a fault on this port alone. Undocumented in either
    # manual, but confirmed on real hardware: an `e` port silently fails to
    # detect or charge an attached device, while still accepting mode commands
    # normally. Sticky — survives `cef`, mode changes and a port power cycle.
    port_error: bool = False


@dataclass
class HubHealth:
    """Result of the hub-wide `health` probe. Every field is best-effort.

    Populated for all firmware classes, but `supply_mv` is only *used* for
    per-port voltage on Universal hubs — PDSync/TS3-C10 report voltage per port
    in the `state` command itself.
    """
    # Note the uppercase `E` flag lives here rather than on PortState. The
    # firmware prints it on every port line, but it means "system errors are
    # present, check health" - a hub-wide condition, not sixteen port faults.
    supply_mv: int | None = None
    temperature_mc: int | None = None
    # Raised error flags, a subset of UV / OV / OT / E. Empty means healthy.
    error_flags: list[str] = field(default_factory=list)
    # `R`. Informational only — a rebooted hub does not refuse mode changes,
    # and `crf` clears it. Deliberately not part of error_flags.
    rebooted: bool = False


@dataclass
class CommandError:
    """A command the hub refused, or that failed in transport.

    An *event*, not polled state: it records that one command failed at one
    moment. Polled conditions (PortState.system_error/port_error,
    HubHealth.error_flags) are
    re-derived from hardware every cycle and live there instead.
    """
    kind: str            # "refused" (firmware *E<nnn>) | "transport" | "injected"
    code: str | None     # "422" parsed out of *E422; None when there was no code
    message: str
    command: str         # the CLI command that drew the error, "" if unknown
    mode: str            # the mode the user asked for
    port_id: int | None  # None means the command was hub-wide
    at: float            # time.time() when it happened, for TTL expiry
