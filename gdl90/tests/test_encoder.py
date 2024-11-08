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
            self.assertEqual(computed, expected, msg=msg)

    
    def test_heartbeat_stratux_msg(self):
        msg_encoder = Encoder()
        # entries are ((st1, ver), (bytes ...))
        sample_data = [
            ((0x02, 0x01), (0x7E,0xCC,0x06,0x06,0xCC,0x7E)),
        ]

        for (fields, expected) in sample_data:
            (st1, ver) = fields
            expected = bytearray(expected)
            computed = msg_encoder.msgStratuxHeartbeat(st1, ver)
            msg = "sequence %s does not match expected %s" % (self._as_hex_str(computed), self._as_hex_str(expected))
            self.assertEqual(computed, expected, msg=msg)


    def test_ownship_msg(self):
        # TODO: Validate the expected output bytes; add more samples
        sample_data = [
            ((10, 0, 1, 0xBEEF01, 33.39, -104.53, 348, 0b1011, 8, 8, 225, 0, 128, 1, 'N123ME', 0), 
             (0x7E,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0xBE,0xEF,0x01,0x17,0xBE,0x76,0xB5,0xAA,0xE5,0x03,0x5B,0x88,0x0E,0x10,0x00,0x5B,0x01,0x4E,0x31,0x32,0x33,0x4D,0x45,0x20,0x20,0x00,0xFD,0x9B,0x7E)
            ),
        ]
        self._test_message_type_10and20(sample_data)


    def test_traffic_msg(self):
        # TODO: Complete this set of tests
        sample_data = [
        ]
        self._test_message_type_10and20(sample_data)


    #def _test_message_type_10and20(self, sample_data:list[tuple[tuple[int, ...], tuple[int, ...]]]):  # requires python3.10
    def _test_message_type_10and20(self, sample_data:list):
        msg_encoder = Encoder()
        for (fields, expected) in sample_data:
            args = tuple(fields[1:])
            msgType = fields[0]
            if msgType == 10:
                msgTypeStr = "OwnshipReport"
                msg_func = msg_encoder.msgOwnshipReport
            elif msgType == 20:
                msgTypeStr = "TrafficReport"
                msg_func = msg_encoder.msgTrafficReport
            else:
                raise ValueError("report type must be 10 or 20: received %d" % (msgType))

            expected = bytearray(expected)
            computed = msg_func(*args)
            msg = "sequence %s does not match expected %s" % (self._as_hex_str(computed), self._as_hex_str(expected))
            self.assertEqual(computed, expected, msg=msg)


