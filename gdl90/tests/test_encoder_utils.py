"""
Test GDL-90 message encoder utility functions.
"""

import unittest

from gdl90.encoder import Encoder


def bytearray_as_hex_str(data):
    """return a hex string representation of a bytearray"""
    values = []
    for byte in data:
        values.append(hex(byte))
    return "[%s]" % (",".join(values))


class EncodingUtilChecks(unittest.TestCase):

    def test_escape_bytes(self):
        msg_encoder = Encoder()
        sample_data = [
            ((), ()),
            ((0, 1, 2, 3, 4, 5, 6, 7), (0, 1, 2, 3, 4, 5, 6, 7)),
            (([0x7D]), (0x7D, 0x5D)),
            (([0x7E]), (0x7D, 0x5E)),
            ((0x80, 0x7D, 0x7E, 0x80), (0x80, 0x7D, 0x5D, 0x7D, 0x5E, 0x80)),
            ((0x7D, 0x7E, 0x80), (0x7D, 0x5D, 0x7D, 0x5E, 0x80)),
            ((0x80, 0x7D, 0x7E), (0x80, 0x7D, 0x5D, 0x7D, 0x5E)),
        ]

        for (data, expected) in sample_data:
            expected = bytearray(expected)
            computed = msg_encoder._escape(data)
            msg = "sequence %s does not match expected %s" % (bytearray_as_hex_str(computed), bytearray_as_hex_str(expected))
            self.assertEqual(computed, expected, msg=msg)


    def test_add_crc(self):
        msg_encoder = Encoder()
        sample_data = [
            ([0x00, 0x81, 0x41, 0xDB, 0xD0, 0x08, 0x02], [0xb3, 0x8b]),
            ([0x00, 0x81, 0x00, 0x28, 0xc9, 0x01, 0x00], [0xa6, 0x6d]),
            ([0x0b, 0x00, 0x69, 0x00, 0x32], [0x4c, 0x0d]),
            ([0x6e,0x94,0x8f,0xc4,0x48,0x49,0x29,0x21], [0x7f,0xf7]), 
            ([0xe0,0xbd,0x3,0xe7,0xa7,0xac,0xb4,0x68], [0xe6,0x7e]), 
            ([0x93,0x8d,0x68,0x72,0x7d,0xbe,0x3c,0xb6], [0x31,0x6d]), 
        ]

        for (data, crc) in sample_data:
            expected = bytearray(data) + bytearray(crc)
            computed = bytearray(data)
            msg_encoder._addCrc(computed)
            msg = "sequence %s does not match expected %s" % (bytearray_as_hex_str(computed), bytearray_as_hex_str(expected))
            self.assertEqual(computed, expected, msg=msg)


    def test_prepare_message(self):
        msg_encoder = Encoder()
        sample_data = [
            ([0x00, 0x81, 0x41, 0xDB, 0xD0, 0x08, 0x02], [0x7E, 0x00, 0x81, 0x41, 0xDB, 0xD0, 0x08, 0x02, 0xb3, 0x8b, 0x7E]),
            ([0x00, 0x81, 0x00, 0x28, 0xc9, 0x01, 0x00], [0x7E, 0x00, 0x81, 0x00, 0x28, 0xc9, 0x01, 0x00, 0xa6, 0x6d, 0x7E]),
            ([0x0b, 0x00, 0x69, 0x00, 0x32], [0x7E, 0x0b, 0x00, 0x69, 0x00, 0x32, 0x4c, 0x0d, 0x7E]),
            ([0xe0,0xbd,0x3,0xe7,0xa7,0xac,0xb4,0x68], [0x7E, 0xe0,0xbd,0x3,0xe7,0xa7,0xac,0xb4,0x68, 0xe6,0x7D,0x5e, 0x7E]), 
            ([0x93,0x8d,0x68,0x72,0x7d,0xbe,0x3c,0xb6], [0x7E, 0x93,0x8d,0x68,0x72,0x7D,0x5d,0xbe,0x3c,0xb6, 0x31,0x6d, 0x7E]), 
        ]

        for (data, expected) in sample_data:
            expected = bytearray(expected)
            computed = msg_encoder._preparedMessage(bytearray(data))
            msg = "sequence %s does not match expected %s" % (bytearray_as_hex_str(computed), bytearray_as_hex_str(expected))
            self.assertEqual(computed, expected, msg=msg)


    def test_pack_24_bit(self):
        msg_encoder = Encoder()
        sample_data = [
               (0x102030, (0x10, 0x20, 0x30)),
               (0x4080C0, (0x40, 0x80, 0xC0)),
               (0x0080FF, (0x00, 0x80, 0xFF)),
        ]

        for(input, expected) in sample_data:
            expected = bytearray(expected)
            computed = msg_encoder._pack24bit(input)
            msg = "sequence %s for value 0x%06X does not match expected %s" % (bytearray_as_hex_str(computed), input, bytearray_as_hex_str(expected))
            self.assertEqual(computed, expected, msg=msg)

        # Check some illegal values
        self.assertRaises(ValueError, msg_encoder._pack24bit, 0x1F0F0F0)  # too many bits
        self.assertRaises(ValueError, msg_encoder._pack24bit, -100)  # negative


    def test_make_latitude(self):
        msg_encoder = Encoder()
        sample_data = [
               (83.417007, 0x3B519A),
               (32.829766, 0x175879),
               (-34.405037, 0xE788C2),
               (-77.843680, 0xC8A4FE),
               (-100.123, 0xC00000),  # capped at -90.0
               (95.678, 0x400000),    # capped at 90.0
        ]

        for (input, expected) in sample_data:
            computed = msg_encoder._makeLatitude(input)
            msg = "latitude %f encoding 0x%06X does not match expected 0x%06X" % (input, computed, expected)
            self.assertEqual(computed, expected, msg=msg)


    def test_make_longitude(self):
        msg_encoder = Encoder()
        sample_data = [
               (-35.896606, 0xE67939),
               (-96.724556, 0xBB37D5),
               (-58.257767, 0xD69280),
               (166.616173, 0x767B8C),
               (-190.123, 0x800000),  # capped at -180.0
               (200.321, 0x800000),    # capped at 180.0
        ]

        for (input, expected) in sample_data:
            computed = msg_encoder._makeLongitude(input)
            msg = "longitude %f encoding 0x%06X does not match expected 0x%06X" % (input, computed, expected)
            self.assertEqual(computed, expected, msg=msg)
