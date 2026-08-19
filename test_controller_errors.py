import unittest
from unittest.mock import patch

import controller
from controller import HubController
from hub_backends import CommandRefused
from models import HubHealth, PortState


class FakeHub:
    """Minimal HubClient stand-in driven entirely by the test."""

    def __init__(self, hub_id="HUB1", n_ports=4):
        self.hub_id = hub_id
        self._n = n_ports
        self.health_result = HubHealth(supply_mv=5000)
        self.poll_error = None      # set to an Exception to make get_ports raise
        self.set_mode_error = None  # set to an Exception to make set_mode raise
        self.error_ports = set()    # port ids that report the firmware E flag
        self.calls = []

    def supported_modes(self):
        return ["on", "off"]

    def get_ports(self):
        if self.poll_error:
            raise self.poll_error
        return [
            PortState(id=i, attachment="detached", status="off", voltage_mv=5000,
                      current_ma=0, charging_seconds=0, energy_mwh=0,
                      error_flag=i in self.error_ports)
            for i in range(1, self._n + 1)
        ]

    def health(self):
        return self.health_result

    def set_mode(self, port_id, mode):
        self.calls.append((port_id, mode))
        if self.set_mode_error:
            raise self.set_mode_error


def make_controller(hub=None):
    """Build a controller with no worker thread, so tests drive it directly."""
    with patch("controller.threading.Thread"):
        c = HubController(poll_interval=0.01)
    hub = hub or FakeHub()
    c._hubs = {hub.hub_id: hub}
    return c, hub


def port(c, port_id, hub_index=0):
    return next(p for p in c.get_hubs()[hub_index]["ports"] if p["id"] == port_id)


class TestCommandErrors(unittest.TestCase):
    def test_refusal_reaches_the_cache(self):
        c, hub = make_controller()
        c._poll()
        self.assertIsNone(port(c, 1)["command_error"])

        hub.set_mode_error = CommandRefused("422", "*E422: Refused: an error flag is set", "mode c 1")
        c._apply_set_mode("HUB1", 1, "on")

        p = port(c, 1)
        self.assertEqual(p["command_error"]["code"], "422")
        self.assertEqual(p["command_error"]["kind"], "refused")
        self.assertTrue(p["blocked"])
        self.assertIn("error flag is set", p["error_detail"])

    def test_refusal_does_not_force_rediscovery(self):
        # A refusal is a policy answer over a healthy link. Rescanning the
        # serial port on every refused click would be pure cost.
        c, hub = make_controller()
        c._poll()
        c._last_discovery = 1234.0
        hub.set_mode_error = CommandRefused("422", "*E422: Refused", "mode c 1")
        c._apply_set_mode("HUB1", 1, "on")

        self.assertEqual(c._last_discovery, 1234.0)

    def test_transport_failure_does_force_rediscovery(self):
        c, hub = make_controller()
        c._poll()
        c._last_discovery = 1234.0
        hub.set_mode_error = OSError("serial port vanished")
        c._apply_set_mode("HUB1", 1, "on")

        self.assertEqual(c._last_discovery, 0)
        self.assertEqual(port(c, 1)["command_error"]["kind"], "transport")

    def test_success_clears_a_previous_error(self):
        c, hub = make_controller()
        c._poll()
        hub.set_mode_error = CommandRefused("422", "*E422: Refused", "mode c 1")
        c._apply_set_mode("HUB1", 1, "on")
        self.assertIsNotNone(port(c, 1)["command_error"])

        hub.set_mode_error = None
        c._apply_set_mode("HUB1", 1, "on")
        self.assertIsNone(port(c, 1)["command_error"])
        self.assertFalse(port(c, 1)["blocked"])

    def test_error_expires_after_ttl(self):
        c, hub = make_controller()
        c._poll()
        hub.set_mode_error = CommandRefused("422", "*E422: Refused", "mode c 1")
        with patch("controller.time.time", return_value=1000.0):
            c._apply_set_mode("HUB1", 1, "on")
            self.assertIsNotNone(port(c, 1)["command_error"])

        with patch("controller.time.time", return_value=1000.0 + controller._COMMAND_ERROR_TTL + 1):
            c._refresh_cache_view()
            self.assertIsNone(port(c, 1)["command_error"])

    def test_hub_wide_failure_marks_the_hub_not_every_tile(self):
        # 16 red tiles from one click is noise; the header carries the message.
        c, hub = make_controller()
        c._poll()
        hub.set_mode_error = CommandRefused("422", "*E422: Refused", "mode c")
        c._apply_set_mode("HUB1", None, "on")

        h = c.get_hubs()[0]
        self.assertTrue(h["blocked"])
        self.assertEqual(h["command_error"]["code"], "422")
        self.assertTrue(all(p["command_error"] is None for p in h["ports"]))

    def test_hub_wide_success_clears_port_errors(self):
        c, hub = make_controller()
        c._poll()
        hub.set_mode_error = CommandRefused("422", "*E422: Refused", "mode c 1")
        c._apply_set_mode("HUB1", 1, "on")
        c._apply_set_mode("HUB1", 2, "on")

        hub.set_mode_error = None
        c._apply_set_mode("HUB1", None, "off")

        self.assertEqual(c._command_errors, {})

    def test_unknown_hub_records_an_error(self):
        c, _ = make_controller()
        c._poll()
        c._apply_set_mode("NOPE", 1, "on")
        self.assertEqual(c._command_errors[("NOPE", 1)].kind, "transport")


class TestPolledConditions(unittest.TestCase):
    def test_port_error_flag_blocks_that_port_only(self):
        c, hub = make_controller()
        hub.error_ports = {2}
        c._poll()

        self.assertTrue(port(c, 2)["blocked"])
        self.assertIn("error flag (E)", port(c, 2)["error_detail"])
        self.assertFalse(port(c, 1)["blocked"])
        self.assertFalse(c.get_hubs()[0]["blocked"])

    def test_health_flag_blocks_the_whole_hub(self):
        c, hub = make_controller()
        hub.health_result = HubHealth(supply_mv=5000, error_flags=["UV"])
        c._poll()

        h = c.get_hubs()[0]
        self.assertTrue(h["blocked"])
        self.assertIn("under-voltage", h["error_detail"])
        self.assertTrue(all(p["blocked"] for p in h["ports"]))

    def test_rebooted_flag_is_not_an_error(self):
        c, hub = make_controller()
        hub.health_result = HubHealth(supply_mv=5000, rebooted=True)
        c._poll()
        self.assertFalse(c.get_hubs()[0]["blocked"])

    def test_poll_failure_retains_ports_and_marks_stale(self):
        c, hub = make_controller()
        c._poll()
        self.assertEqual(len(c.get_hubs()[0]["ports"]), 4)

        hub.poll_error = OSError("hub disappeared")
        c._poll()

        h = c.get_hubs()[0]
        self.assertEqual(len(h["ports"]), 4)  # tiles stay visible
        self.assertTrue(h["stale"])
        self.assertTrue(h["blocked"])
        self.assertIn("hub disappeared", h["error_detail"])
        self.assertTrue(all(p["blocked"] for p in h["ports"]))

    def test_recovery_clears_everything(self):
        c, hub = make_controller()
        hub.poll_error = OSError("gone")
        c._poll()
        self.assertTrue(c.get_hubs()[0]["blocked"])

        hub.poll_error = None
        c._poll()

        h = c.get_hubs()[0]
        self.assertFalse(h["blocked"])
        self.assertFalse(h["stale"])
        self.assertIsNone(h["error_detail"])


class TestInjection(unittest.TestCase):
    def test_injection_is_ignored_without_the_env_var(self):
        c, _ = make_controller()
        c._poll()
        with patch.dict("os.environ", {}, clear=True):
            c.inject_error({"kind": "command", "hub_id": "HUB1", "port_id": 1})
        self.assertTrue(c._command_queue.empty())

    def test_injected_command_error_renders_like_a_real_one(self):
        c, _ = make_controller()
        c._poll()
        c._apply_injection({"hub_id": "HUB1", "port_id": 1, "kind": "command",
                            "code": "422", "message": "*E422: Refused"})

        p = port(c, 1)
        self.assertEqual(p["command_error"]["code"], "422")
        self.assertTrue(p["blocked"])

    def test_injected_port_flag_survives_a_poll(self):
        # Unlike a command error, a simulated polled condition must persist.
        c, _ = make_controller()
        c._poll()
        c._apply_injection({"hub_id": "HUB1", "port_id": 3, "kind": "port_flag"})
        c._poll()

        self.assertTrue(port(c, 3)["blocked"])
        self.assertFalse(port(c, 1)["blocked"])

    def test_injected_health_flag_blocks_the_hub(self):
        c, _ = make_controller()
        c._poll()
        c._apply_injection({"hub_id": "HUB1", "kind": "health", "flags": ["OT"]})

        h = c.get_hubs()[0]
        self.assertTrue(h["blocked"])
        self.assertIn("over-temperature", h["error_detail"])

    def test_injected_poll_error_keeps_tiles(self):
        c, _ = make_controller()
        c._poll()
        c._apply_injection({"hub_id": "HUB1", "kind": "poll", "message": "simulated"})

        h = c.get_hubs()[0]
        self.assertTrue(h["stale"])
        self.assertEqual(len(h["ports"]), 4)

    def test_clear_removes_injections(self):
        c, _ = make_controller()
        c._poll()
        c._apply_injection({"hub_id": "HUB1", "kind": "health", "flags": ["UV"]})
        c._apply_injection({"hub_id": "HUB1", "clear": True})
        c._poll()

        self.assertFalse(c.get_hubs()[0]["blocked"])


if __name__ == "__main__":
    unittest.main()
