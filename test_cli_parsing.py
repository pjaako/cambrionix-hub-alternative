import unittest
from unittest.mock import MagicMock
from hub_backends import CliClient, PortState

class TestCliParsing(unittest.TestCase):
    def test_pdsync_parsing(self):
        # Ex 1: 1, 0515, 2051, A C -, 3383, x, 9.92
        transport = MagicMock()
        # Mock 'id' command to return PDSync
        transport.send_command.side_effect = [
            "mfr: Cambrionix, sn: 123, fc: ps", # id
            "1, 0515, 2051, A C -, 3383, x, 9.92\n>>" # state
        ]
        transport.hub_serial.return_value = "SN123"
        
        client = CliClient(transport)
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
        transport = MagicMock()
        transport.send_command.side_effect = [
            "mfr: Cambrionix, sn: 123, fc: ps",
            "16, 0515, 0000, A F -, 3383, 3383, 9.92\n>>",
        ]
        transport.hub_serial.return_value = "SN123"

        client = CliClient(transport)
        p = client.get_ports()[0]

        self.assertEqual(p.attachment, "attached")
        self.assertEqual(p.status, "finished")

    def test_pdsync_attachment_status_collision(self):
        # "C" means Type-C-cable-only in Attachment (col 1) but Charging in Status
        # (col 2) — positional parsing must resolve them independently.
        transport = MagicMock()
        transport.send_command.side_effect = [
            "mfr: Cambrionix, sn: 123, fc: ps",
            "1, 0515, 0000, C c -, 0, x, 0.00\n>>",
        ]
        transport.hub_serial.return_value = "SN123"

        client = CliClient(transport)
        p = client.get_ports()[0]

        self.assertEqual(p.attachment, "type_c_only")
        self.assertEqual(p.status, "power_no_device")

    def test_universal_parsing(self):
        # Ex 2: 1, 0429, R A S, 0, 0, x, 0.00
        transport = MagicMock()
        # Mock 'id' command to return Universal
        transport.send_command.side_effect = [
            "mfr: Cambrionix, sn: 456, fc: un", # id
            "5V_V1: 5042\n5V_V2: 5038\n12V: 12050\nTemp: 35400\nFlags: R\n>>", # health
            "1, 0429, R A S, 0, 0, x, 0.00\n>>" # state
        ]
        transport.hub_serial.return_value = "SN456"

        client = CliClient(transport)
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

if __name__ == "__main__":
    unittest.main()
