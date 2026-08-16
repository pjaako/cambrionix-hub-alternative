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
        self.assertEqual(p.voltage_v, 5.15)
        self.assertEqual(p.current_ma, 2051)
        self.assertEqual(p.mode, "on")
        self.assertTrue(p.attached)
        self.assertEqual(p.energy_wh, 9.92)

    def test_universal_parsing(self):
        # Ex 2: 1, 0429, R A S, 0, 0, x, 0.00
        transport = MagicMock()
        # Mock 'id' command to return Universal
        transport.send_command.side_effect = [
            "mfr: Cambrionix, sn: 456, fc: un", # id
            "1, 0429, R A S, 0, 0, x, 0.00\n>>" # state
        ]
        transport.hub_serial.return_value = "SN456"
        
        client = CliClient(transport)
        ports = client.get_ports()
        
        self.assertEqual(len(ports), 1)
        p = ports[0]
        self.assertEqual(p.id, 1)
        # Universal doesn't have voltage in state command, or it's current at index 1
        self.assertEqual(p.current_ma, 429)
        self.assertEqual(p.mode, "sync")
        self.assertTrue(p.attached)
        self.assertEqual(p.energy_wh, 0.0)
        self.assertIsNone(p.voltage_v)

if __name__ == "__main__":
    unittest.main()
