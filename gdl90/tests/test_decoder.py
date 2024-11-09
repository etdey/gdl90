"""
Test GDL-90 message decoder functions.
"""

import unittest
from collections import namedtuple

from gdl90.decoder import Decoder

class DecodingResyncChecks(unittest.TestCase):
    """Test resynchronization of the parser buffer"""

    def _buffer_mismatch_message(self, expected, actual):
        return "mismatch of resulting buffer: expected=[%s], actual=[%s]" % (expected, actual)

    def test_buffer_empty(self):
        msg_decoder = Decoder()
        msg = "empty parser buffer should not resync"
        self.assertFalse(msg_decoder._resynchronizeParser(), msg=msg)
        pass

    def test_buffer_too_small(self):
        msg_decoder = Decoder()
        data = bytearray([0x7E])
        msg_decoder.addBytes(data)
        msg = "parser buffer is too small to resync"
        self.assertFalse(msg_decoder._resynchronizeParser(), msg=msg)
        msg = "parser buffer size should not have changed"
        self.assertEqual(len(msg_decoder.inputBuffer), 1, msg=msg)
        msg = "parser buffer contents should not have changed"
        self.assertEqual(msg_decoder.inputBuffer[0], 0x7E, msg=msg)

    def test_buffer_trash(self):
        msg_decoder = Decoder()
        data = bytearray([0x11, 0x22, 0x33, 0x44])
        msg_decoder.addBytes(data)
        msg = "parser should not have resynchronized"
        self.assertFalse(msg_decoder._resynchronizeParser(), msg=msg)
        msg = "parser buffer should have been emptied"
        self.assertEqual(len(msg_decoder.inputBuffer), 0, msg=msg)

    def test_buffer_final_0x7e(self):
        msg_decoder = Decoder()
        data = bytearray([0x66, 0x77, 0x88, 0x99, 0x7E])
        msg_decoder.addBytes(data)
        msg = "parser should not have resynchronized"
        self.assertFalse(msg_decoder._resynchronizeParser(), msg=msg)
        expected_buffer = bytearray([0x7E])
        msg = self._buffer_mismatch_message(expected_buffer, data)
        self.assertEqual(expected_buffer, msg_decoder.inputBuffer, msg=msg)

    def test_buffer_trash_before_msg(self):
        msg_decoder = Decoder()
        data = bytearray([0x88, 0x99, 0x7E, 0x11, 0x22])
        msg_decoder.addBytes(data)
        msg = "parser should have synchronized"
        self.assertTrue(msg_decoder._resynchronizeParser(), msg=msg)
        expected_buffer = bytearray([0x7E, 0x11, 0x22])
        msg = self._buffer_mismatch_message(expected_buffer, data)
        self.assertEqual(expected_buffer, msg_decoder.inputBuffer, msg=msg)

    def test_buffer_start_mid_msg(self):
        msg_decoder = Decoder()
        data = bytearray([0x88, 0x99, 0x7E, 0x7E, 0x11, 0x22])
        msg_decoder.addBytes(data)
        msg = "parser should have synchronized"
        self.assertTrue(msg_decoder._resynchronizeParser(), msg=msg)
        expected_buffer = bytearray([0x7E, 0x11, 0x22])
        msg = self._buffer_mismatch_message(expected_buffer, data)
        self.assertEqual(expected_buffer, msg_decoder.inputBuffer, msg=msg)


class DecodingMsgChecks(unittest.TestCase):
    """Test decoding of specific messages; input data excludes the start/stop 0x7E bytes"""

    def test_heartbeat(self):
        msg_decoder = Decoder()
        rawdata = bytearray([0x00,0x81,0x01,0x90,0x7D,0x5E,0x00,0x02,0x0C,0x1B])
        expected_msg = namedtuple('Heartbeat', 'MsgType StatusByte1 StatusByte2 TimeStamp MessageCounts')
        expected_msg._make(['Heartbeat', 0x81, 0x01, 32400, 2])
        msg = "heartbeat message failed to decode"
        result = msg_decoder._decodeMessage(rawdata)
        self.assertTrue(result, msg=msg)
        # TODO: test decoded message fields after refactor of Decoder parser

    def test_ownship(self):
        msg_decoder = Decoder()
        rawdata = bytearray([0x0a,0x01,0xBE,0xEF,0x01,0x17,0xBE,0x76,0xB5,0xAA,0xE5,0x03,0x5B,0x88,0x0E,0x10,0x00,0x5B,0x01,0x4E,0x31,0x32,0x33,0x4D,0x45,0x20,0x20,0x00,0xB3,0xE0])
        expected_msg = namedtuple('OwnshipReport', 'MsgType Status Type Address Latitude Longitude Altitude Misc NavIntegrityCat NavAccuracyCat HVelocity VVelocity TrackHeading EmitterCat CallSign Code')
        expected_msg._make(['OwnshipReport', 0, 1, 0xBEEF01, 33.39, -104.53, 348, 0b1011, 8, 8, 225, 0, 128, 1, 'N123ME', 0])
        msg = "ownship message failed to decode"
        result = msg_decoder._decodeMessage(rawdata)
        self.assertTrue(result, msg=msg)
        # TODO: test decoded message fields after refactor of Decoder parser

    # TODO: add testing for additional message types
