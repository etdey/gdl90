"""
Test GDL-90 message decoder utility functions.
"""

import unittest

from gdl90.decoder import Decoder

class DecodingUtilChecks(unittest.TestCase):

    def _as_hex_str(self, data):
        values = []
        for byte in data:
            values.append(hex(byte))
        return "[%s]" % (",".join(values))


    def test_unescape_bytes(self):
        msg_decoder = Decoder()
        sample_data = [
            ((), ()),
            ((0, 1, 2, 3, 4, 5, 6, 7), (0, 1, 2, 3, 4, 5, 6, 7)),
            ((0x7D, 0x5D), ([0x7D])),
            ((0x7D, 0x5E), ([0x7E])),
            ((0x80, 0x7D, 0x5D, 0x7D, 0x5E, 0x80), (0x80, 0x7D, 0x7E, 0x80)),
            ((0x7D, 0x5D, 0x7D, 0x5E, 0x80), (0x7D, 0x7E, 0x80)),
            ((0x80, 0x7D, 0x5D, 0x7D, 0x5E), (0x80, 0x7D, 0x7E)),
            #((0x80, 0x7D), (0x80, 0x7D)),  # nothing follows escape char
            ((0x80, 0x7D, 0x5E, 0x7D), (0x80, 0x7E, 0x7D)),  # nothing follows last escape char
        ]

        for (data, expected) in sample_data:
            data = bytearray(data)
            expected = bytearray(expected)
            computed = msg_decoder._unescape(data)
            msg = "sequence %s does not match expected %s" % (self._as_hex_str(computed), self._as_hex_str(expected))
            self.assertEqual(computed, expected, msg=msg)
