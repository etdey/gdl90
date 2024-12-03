"""
Test GDL-90 message encoder functions.
"""

import unittest

from gdl90.encoder import Encoder

class EncodingUtilChecks(unittest.TestCase):

    def _as_hex_str(self, data):
        return data.hex(',').upper()


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
            msg = "sequence does not match:\n expected=%s\n computed=%s" % (self._as_hex_str(expected), self._as_hex_str(computed))
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
            msg = "sequence does not match:\n expected=%s\n computed=%s" % (self._as_hex_str(expected), self._as_hex_str(computed))
            self.assertEqual(computed, expected, msg=msg)


    def test_ownship_msg(self):
        sample_data = [
            ((10, 0, 1, 0xBEEF01, 33.39, -104.53, 348, 0b1011, 8, 8, 225, 0, 128, 1, 'N123ME', 0), 
             (0x7E,0x0a,0x01,0xBE,0xEF,0x01,0x17,0xBE,0x76,0xB5,0xAA,0xE5,0x03,0x5B,0x88,0x0E,0x10,0x00,0x5B,0x01,0x4E,0x31,0x32,0x33,0x4D,0x45,0x20,0x20,0x00,0xB3,0xE0,0x7E)
            ),
            ((10, 0, 0, 0, 30.209548473358154, -98.25480937957764, 3300, 9, 8, 8, 545, 1408, 258.75, 1, 'N12345', 0),
             (0x7e,0x0a,0x00,0x00,0x00,0x00,0x15,0x7b,0x7b,0xba,0x21,0x42,0x0a,0xc9,0x88,0x22,0x10,0x16,0xb8,0x01,0x4e,0x31,0x32,0x33,0x34,0x35,0x20,0x20,0x00,0x3d,0x8c,0x7e)
             ),
        ]
        self._test_message_type_10and20(sample_data)


    def test_traffic_msg(self):
        sample_data = [
            ((20, 0, 0, 0xE1F24F, 30.52377462387085, -98.53493928909302, 4900, 9, 8, 8, 310, 0, 195.46875, 1, 'BNDT0', 0),
             (0x7e,0x14,0x0,0xe1,0xf2,0x4f,0x15,0xb4,0xaf,0xb9,0xee,0x43,0xe,0xc9,0x88,0x13,0x60,0x0,0x8b,0x1,0x42,0x4e,0x44,0x54,0x30,0x20,0x20,0x20,0x0,0x41,0xa5,0x7e)
            ),
            ((20, 0, 0, 0xB33B89, 30.597481727600098, -98.50058555603027, 4050, 9, 8, 8, 300, 0, 213.75, 1, 'BNDT1', 0),
             (0x7e,0x14,0x0,0xb3,0x3b,0x89,0x15,0xc2,0x1a,0xb9,0xf4,0x84,0xc,0xa9,0x88,0x12,0xc0,0x0,0x98,0x1,0x42,0x4e,0x44,0x54,0x31,0x20,0x20,0x20,0x0,0xb7,0x89,0x7e)
            ),
        ]
        self._test_message_type_10and20(sample_data)


    #def _test_message_type_10and20(self, sample_data:list[tuple[tuple[int, ...], tuple[int, ...]]]):  # requires python3.10
    def _test_message_type_10and20(self, sample_data:list, ):
        """unified test for ownship (10) and traffic (20)
        Sample data list of tuples (fields, expected)
            Fields: 
                msgid, status, addrType, address, latitude, longitude, 
                altitude, misc, navIntegrityCat, navAccuracyCat, 
                hVelocity, vVelocity, trackHeading, emitterCat, callSign, code
            where
                msgid = 10 | 20
                see GDL90 specification for meaning/format of the other fields
            
            Expected:
                list of encoded bytes: 0x7E, ..., 0x7E
        """
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
            msg = "%s sequence does not match:\n expected=%s\n computed=%s" % (msgTypeStr, self._as_hex_str(expected), self._as_hex_str(computed))
            self.assertEqual(computed, expected, msg=msg)
