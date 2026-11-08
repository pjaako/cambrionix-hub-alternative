"""SerialTransport follows its hub by FTDI serial number when tty names change after a replug."""
from types import SimpleNamespace
from unittest import mock

import pytest
import serial

import hub_backends
from hub_backends import SerialTransport


class FakeSerial:
    opened = []

    def __init__(self, port, baud, timeout, exclusive):
        FakeSerial.opened.append(port)
        self.port = port
        self.is_open = True
        self.in_waiting = 0
        self.fail_next = None

    def reset_input_buffer(self):
        pass

    def write(self, b):
        if self.fail_next:
            e, self.fail_next = self.fail_next, None
            raise e

    def read(self, n):
        return b""

    def close(self):
        self.is_open = False


def ports(mapping):
    return lambda: [SimpleNamespace(device=dev, vid=0x0403, pid=0x6015, serial_number=sn)
                    for dev, sn in mapping.items()]


@pytest.fixture(autouse=True)
def fake_serial(monkeypatch):
    FakeSerial.opened = []
    monkeypatch.setattr(hub_backends.serial, "Serial", FakeSerial)
    monkeypatch.setattr(hub_backends.time, "sleep", lambda s: None)


def test_transport_follows_hub_to_new_tty_after_error(monkeypatch):
    comports = mock.MagicMock(side_effect=ports({"/dev/ttyUSB1": "DN00I9CQ", "/dev/ttyUSB0": "DT04KRQJ"}))
    monkeypatch.setattr("serial.tools.list_ports.comports", comports)
    t = SerialTransport("/dev/ttyUSB1", timeout=0.01)
    t.send_command("id")
    assert t.hub_serial() == "DN00I9CQ"

    # Both hubs replugged, names swapped. The old handle fails with an I/O error.
    comports.side_effect = ports({"/dev/ttyUSB0": "DN00I9CQ", "/dev/ttyUSB1": "DT04KRQJ"})
    t._ser.fail_next = OSError(5, "Input/output error")
    with pytest.raises(serial.SerialException):
        t.send_command("state")

    t.send_command("state")
    assert FakeSerial.opened == ["/dev/ttyUSB1", "/dev/ttyUSB0"]   # reopened where its hub is now
    assert t.hub_serial() == "DN00I9CQ"


def test_transport_reports_unplugged_hub(monkeypatch):
    comports = mock.MagicMock(side_effect=ports({"/dev/ttyUSB1": "DN00I9CQ"}))
    monkeypatch.setattr("serial.tools.list_ports.comports", comports)
    t = SerialTransport("/dev/ttyUSB1", timeout=0.01)
    t.send_command("id")
    comports.side_effect = ports({})
    t._ser.fail_next = OSError(5, "Input/output error")
    with pytest.raises(serial.SerialException):
        t.send_command("state")
    with pytest.raises(serial.SerialException, match="not connected"):
        t.send_command("state")
    assert FakeSerial.opened == ["/dev/ttyUSB1"]


def test_serial_exception_drops_handle(monkeypatch):
    monkeypatch.setattr("serial.tools.list_ports.comports", ports({"/dev/ttyUSB1": "DN00I9CQ"}))
    t = SerialTransport("/dev/ttyUSB1", timeout=0.01)
    t.send_command("id")
    t._ser.fail_next = serial.SerialException("device reports readiness to read but returned no data")
    with pytest.raises(serial.SerialException):
        t.send_command("state")
    assert t._ser is None
