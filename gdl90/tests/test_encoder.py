"""
Test GDL-90 message encoder functions.
"""

import unittest

from gdl90.encoder import Encoder

class EncodingUtilChecks(unittest.TestCase):

    def _as_hex_str(self, data):
        values = []
        for byte in data:
            values.append("0x%02X" % byte)
        return "[%s]" % (",".join(values))


    def test_heartbeat_msg(self):
        msg_encoder = Encoder()
        # entries are ((st1, st2, ts, mc), (bytes ...))
        sample_data = [
            ((0x81, 0x01, 3600, 1), (0x7E,0x00,0x81,0x01,0x10,0x0E,0x00,0x01,0x00,0x7D,0x5E,0x7E)),
            ((0x81, 0x01, 32400, 2), (0x7E,0x00,0x81,0x01,0x90,0x7D,0x5E,0x00,0x02,0x0C,0x1B,0x7E)),
            ((0x81, 0x01, 0x12233, 3), (0x7E,0x00,0x81,0x81,0x33,0x22,0x00,0x03,0x03,0xF3,0x7E)),
            ((0x81, 0x01, 86399, 4), (0x7E,0x00,0x81,0x81,0x7F,0x51,0x00,0x04,0x51,0xF5,0x7E)),
        ]

        for (fields, expected) in sample_data:
            (st1, st2, ts, mc) = fields
            expected = bytearray(expected)
            computed = msg_encoder.msgHeartbeat(st1, st2, ts, mc)
            msg = "sequence %s does not match expected %s" % (self._as_hex_str(computed), self._as_hex_str(expected))
            print("computed msg = %s" % self._as_hex_str(computed))
            self.assertEqual(computed, expected, msg=msg)