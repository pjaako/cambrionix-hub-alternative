"""CliClient serial discovery must open FTDI (Cambrionix) ports only, never other USB serial devices."""
from types import SimpleNamespace
from unittest import mock

import hub_backends
from hub_backends import CliClient, _FTDI_VID


def _ports():
    return [
        SimpleNamespace(device="/dev/ttyACM0", vid=0x0483, pid=0x5740),   # STM32 virtual COM port (A1207 gauge)
        SimpleNamespace(device="/dev/ttyUSB0", vid=_FTDI_VID, pid=0x6015),  # Cambrionix hub (FTDI)
        SimpleNamespace(device="/dev/ttyS0", vid=None, pid=None),         # built-in UART, no USB ids
    ]


def test_only_ftdi_ports_are_opened():
    opened = []

    class FakeClient:
        def __init__(self, tty):
            opened.append(tty)
            self.hub_id = "DT04KRQJ"
        def close(self):
            pass

    with mock.patch("serial.tools.list_ports.comports", _ports), \
         mock.patch.object(CliClient, "via_serial", side_effect=FakeClient):
        hubs, inaccessible, other = CliClient._classify_usb_serial()

    assert opened == ["/dev/ttyUSB0"]
    assert len(hubs) == 1 and inaccessible == 0
    assert other == 1            # the STM32 port is reported, not probed
