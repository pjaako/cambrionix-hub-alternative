import unittest
from unittest.mock import MagicMock

from hub_backends import CliClient, CommandRefused, _parse_health

# `health` now runs on every firmware class, so it sits between `id` and `state`
# in every send_command sequence below.
_HEALTH_DOC = "5V_V1: 5042\n5V_V2: 5038\n12V: 12050\nTemp: 35400\nFlags: R\n>>"
_HEALTH_LIVE = (
    "System up for:    10870 seconds\n"
    "5V Now:   5.30\n"
    "5V Min:   4.57\n"
    "5V Max:   5.30\n"
    "5V Flags: UV\n"
    "Temperature Now (C): <0.1\n"
    "Temperature Flags:\n"
    "Rebooted flag: R\n>>"
)


def _client(fc, health, *replies):
    transport = MagicMock()
    transport.send_command.side_effect = [f"mfr: Cambrionix, sn: 123, fc: {fc}", health, *replies]
    transport.hub_serial.return_value = "SN123"
    return CliClient(transport), transport


class TestCliParsing(unittest.TestCase):
    def test_pdsync_parsing(self):
        # Ex 1: 1, 0515, 2051, A C -, 3383, x, 9.92
        client, _ = _client("ps", _HEALTH_DOC, "1, 0515, 2051, A C -, 3383, x, 9.92\n>>")
        ports = client.get_ports()

        self.assertEqual(len(ports), 1)
        p = ports[0]
        self.assertEqual(p.id, 1)
        self.assertEqual(p.voltage_mv, 5150)
        self.assertEqual(p.current_ma, 2051)
        self.assertEqual(p.attachment, "attached")
        self.assertEqual(p.status, "charging")
        self.assertEqual(p.energy_mwh, 9920)

    def test_pdsync_finished_charging(self):
        # Port 16 reaching "finished charging" (flag F in the Status column)
        client, _ = _client("ps", _HEALTH_DOC, "16, 0515, 0000, A F -, 3383, 3383, 9.92\n>>")
        p = client.get_ports()[0]

        self.assertEqual(p.attachment, "attached")
        self.assertEqual(p.status, "finished")

    def test_pdsync_attachment_status_collision(self):
        # "C" means Type-C-cable-only in Attachment (col 1) but Charging in Status
        # (col 2) — positional parsing must resolve them independently.
        client, _ = _client("ps", _HEALTH_DOC, "1, 0515, 0000, C c -, 0, x, 0.00\n>>")
        p = client.get_ports()[0]

        self.assertEqual(p.attachment, "type_c_only")
        self.assertEqual(p.status, "power_no_device")

    def test_universal_parsing(self):
        # Ex 2: 1, 0429, R A S, 0, 0, x, 0.00
        client, _ = _client("un", _HEALTH_DOC, "1, 0429, R A S, 0, 0, x, 0.00\n>>")
        ports = client.get_ports()

        self.assertEqual(len(ports), 1)
        p = ports[0]
        self.assertEqual(p.id, 1)
        # Universal doesn't have voltage in state command; it's current at index 1
        self.assertEqual(p.current_ma, 429)
        self.assertEqual(p.attachment, "attached")
        self.assertEqual(p.status, "sync")
        self.assertEqual(p.energy_mwh, 0)
        # Universal hubs are USB2 with all ports paralleled onto one supply rail,
        # so voltage comes from the hub-wide `health` command instead.
        self.assertEqual(p.voltage_mv, 5042)

    def test_pdsync_voltage_comes_from_state_not_health(self):
        # Regression guard: `health` runs on every firmware class now, but only
        # Universal takes its voltage from it. A PDSync port must keep the
        # reading from its own state column even when health reports something
        # wildly different.
        client, _ = _client("ps", "5V Now:   9.99\n>>", "1, 0515, 2051, A C -, 3383, x, 9.92\n>>")
        p = client.get_ports()[0]

        self.assertEqual(p.voltage_mv, 5150)  # 0515 * 10, not 9990


class TestErrorFlags(unittest.TestCase):
    """Lowercase `e` is a port fault; uppercase `E` is a hub condition.

    The firmware prints `E` on every port line, but it means "system errors
    present, check health" — so it belongs to the hub, not to sixteen ports.
    """

    def test_lowercase_e_is_a_port_fault(self):
        # Confirmed on hardware: an `e` port will not detect or charge a device.
        client, _ = _client("un", _HEALTH_DOC, "2, 0000, e D S, 0, 0, x, 0.00\n>>")
        p = client.get_ports()[0]

        self.assertTrue(p.port_error)
        self.assertEqual(p.attachment, "detached")
        self.assertEqual(p.status, "sync")     # the fault does not mask status
        self.assertEqual(client.health().error_flags, [])   # nothing hub-wide

    def test_uppercase_E_goes_to_the_hub_not_the_ports(self):
        client, _ = _client(
            "un", _HEALTH_DOC,
            "1, 0000, E D O, 0, 0, x, 0.00\n2, 0000, E D O, 0, 0, x, 0.00\n>>")
        ports = client.get_ports()

        self.assertFalse(any(p.port_error for p in ports))
        self.assertEqual(client.health().error_flags, ["E"])   # recorded once

    def test_case_is_significant(self):
        client, _ = _client("un", _HEALTH_DOC, "1, 0000, e D S, 0, 0, x, 0.00\n>>")
        client.get_ports()
        self.assertEqual(client.health().error_flags, [])      # e is not E

    def test_port_fault_on_an_attached_port(self):
        # Observed live as "e A S": attachment still reports normally even
        # though the port cannot charge what is attached.
        client, _ = _client("un", _HEALTH_DOC, "14, 0000, e A S, 0, 0, x, 0.00\n>>")
        p = client.get_ports()[0]

        self.assertTrue(p.port_error)
        self.assertEqual(p.attachment, "attached")

    def test_both_flags_at_once(self):
        client, _ = _client("un", _HEALTH_DOC, "3, 0000, e E D O, 0, 0, x, 0.00\n>>")
        p = client.get_ports()[0]

        self.assertTrue(p.port_error)
        self.assertEqual(client.health().error_flags, ["E"])

    def test_no_flags(self):
        client, _ = _client("un", _HEALTH_DOC, "1, 0000, D I, 0, 0, x, 0.00\n>>")
        self.assertFalse(client.get_ports()[0].port_error)

    def test_pdsync_never_reports_a_port_fault(self):
        # The positional format has no error column, so a "C" in the status
        # position must not be mistaken for one.
        client, _ = _client("ps", _HEALTH_DOC, "1, 0515, 2051, A C -, 3383, x, 9.92\n>>")
        self.assertFalse(client.get_ports()[0].port_error)


class TestCommandRefusal(unittest.TestCase):
    def test_set_mode_raises_on_refusal(self):
        client, transport = _client("un", _HEALTH_DOC)
        transport.send_command.side_effect = [
            "mode c 1\n*E422: Refused: an error flag is set\n>>"
        ]
        with self.assertRaises(CommandRefused) as ctx:
            client.set_mode(1, "on")
        self.assertEqual(ctx.exception.code, "422")
        self.assertIn("error flag is set", ctx.exception.message)

    def test_set_mode_raises_on_undocumented_code(self):
        # 420 and 422 are both absent from the manual table, so detection must
        # be generic rather than a lookup of known codes.
        client, transport = _client("un", _HEALTH_DOC)
        transport.send_command.side_effect = ["*E999: brand new failure\n>>"]
        with self.assertRaises(CommandRefused) as ctx:
            client.set_mode(1, "on")
        self.assertEqual(ctx.exception.code, "999")

    def test_set_mode_succeeds_quietly(self):
        client, transport = _client("un", _HEALTH_DOC)
        transport.send_command.side_effect = ["mode c 1\n>>"]
        client.set_mode(1, "on")  # must not raise

    def test_state_line_is_not_mistaken_for_an_error(self):
        client, _ = _client("un", _HEALTH_DOC, "1, 0000, D I, 0, 0, x, 0.00\n>>")
        self.assertEqual(len(client.get_ports()), 1)


class TestParseHealth(unittest.TestCase):
    def test_live_format(self):
        h = _parse_health(_HEALTH_LIVE)
        self.assertEqual(h.supply_mv, 5300)  # "5V Now" in volts
        self.assertEqual(h.error_flags, ["UV"])
        self.assertTrue(h.rebooted)

    def test_running_minimum_is_not_read_as_supply(self):
        # "5V Min" is a since-boot record, not the current rail.
        self.assertEqual(_parse_health(_HEALTH_LIVE).supply_mv, 5300)

    def test_documented_format(self):
        h = _parse_health(_HEALTH_DOC)
        self.assertEqual(h.supply_mv, 5042)  # already mV
        self.assertEqual(h.temperature_mc, 35400)
        self.assertEqual(h.error_flags, [])
        self.assertTrue(h.rebooted)  # "Flags: R"

    def test_rebooted_is_not_an_error(self):
        # R does not block mode changes and is cleared by `crf`.
        self.assertEqual(_parse_health("Rebooted flag: R\n>>").error_flags, [])

    def test_unknown_flag_ignored(self):
        # A false red is worse than a missed one on a partly-verified format.
        self.assertEqual(_parse_health("5V Flags: ZZ\n>>").error_flags, [])

    def test_multiple_flags(self):
        h = _parse_health("5V Flags: UV OV\nTemperature Flags: OT\n>>")
        self.assertEqual(sorted(h.error_flags), ["OT", "OV", "UV"])

    def test_empty(self):
        h = _parse_health("")
        self.assertIsNone(h.supply_mv)
        self.assertEqual(h.error_flags, [])


class TestHealthProbe(unittest.TestCase):
    def test_unsupported_health_is_not_a_failure(self):
        # A product without `health` answers *E400. That is "no reading", not a
        # broken hub, so get_ports() must still work.
        client, _ = _client("ps", "*E400: Command is not valid\n>>",
                            "1, 0515, 2051, A C -, 3383, x, 9.92\n>>")
        ports = client.get_ports()

        self.assertEqual(len(ports), 1)
        self.assertEqual(client.health().error_flags, [])

    def test_health_exposed_after_poll(self):
        client, _ = _client("un", _HEALTH_LIVE, "1, 0000, E D O, 0, 0, x, 0.00\n>>")
        client.get_ports()
        # UV from health, E from the state output — both hub-level.
        self.assertEqual(sorted(client.health().error_flags), ["E", "UV"])


if __name__ == "__main__":
    unittest.main()
