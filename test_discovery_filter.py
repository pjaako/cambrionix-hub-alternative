"""CliClient serial discovery must open FTDI (Cambrionix) ports only, never other USB serial devices."""
from types import SimpleNamespace
from unittest import mock

import hub_backends
from hub_backends import CliClient, _FTDI_VID


def _ports():
    return [
        SimpleNamespace(device="/dev/ttyACM0", vid=0x0483, pid=0x5740, serial_number="207635AD3931"),  # A1207 gauge
        SimpleNamespace(device="/dev/ttyUSB0", vid=_FTDI_VID, pid=0x6015, serial_number="DT04KRQJ"),   # hub (FTDI)
        SimpleNamespace(device="/dev/ttyS0", vid=None, pid=None, serial_number=None),                # built-in UART
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


def test_known_hub_is_reported_present_without_reopening_its_port():
    opened = []
    known_client = object()

    class FakeClient:
        def __init__(self, tty):
            opened.append(tty)
            self.hub_id = "X"
        def close(self):
            pass

    with mock.patch("serial.tools.list_ports.comports", _ports), \
         mock.patch.object(CliClient, "via_serial", side_effect=FakeClient):
        hubs, inaccessible, other = CliClient._classify_usb_serial({"DT04KRQJ": known_client})

    assert opened == []                 # the registered hub's port was not touched
    assert hubs == [known_client] and inaccessible == 0 and other == 1
