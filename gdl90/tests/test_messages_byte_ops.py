"""
Test GDL-90 message byte operation functions
"""

import unittest

from gdl90.messages import _unsigned32, _signed32, _unsigned24, _signed24, _unsigned16, _signed16, _thunkByte

class ByteChecks(unittest.TestCase):

    def test_unsigned32(self):
        samples_bigEndian = [
            ((0xFF, 0xFF, 0xFF, 0xFF), 0xFFFFFFFF),
            ((0x00, 0x80, 0xF0, 0x80), 0x0080F080),
            ((0x80, 0xF0, 0x00, 0x7F), 0x80F0007F) ,
            ((0xF0, 0x00, 0x80, 0x00), 0xF0008000),
        ]
        samples_littleEndian = [
            ((0xFF, 0xFF, 0xFF, 0xFF), 0xFFFFFFFF),
            ((0x80, 0x00, 0x80, 0xF0), 0xF0800080),
            ((0x80, 0xF0, 0x00, 0x7F), 0x7F00F080),
            ((0xF0, 0x00, 0x80, 0x00), 0x008000F0),
        ]

        # Big endian tests
        for (data, expected) in samples_bigEndian:
            computed = _unsigned32(data, False)
            msg="32-bit unsigned big endian decode error %06X != %06X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)
        
        # Little endian tests
        for (data, expected) in samples_littleEndian:
            computed = _unsigned32(data, True)
            msg="32-bit unsigned little endian decode error %06X != %06X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)

        # Input data without enough bytes raises AssertionError
        self.assertRaises(AssertionError, _unsigned32, bytearray([0x01]))
        self.assertRaises(AssertionError, _unsigned32, bytearray([0x01, 0x02]))
        self.assertRaises(AssertionError, _unsigned32, bytearray([0x01, 0x02, 0x03]))


    def test_signed32(self):
        samples_bigEndian = [
            ((0xFF, 0xFF, 0xFF, 0xFF), -1),
            ((0x00, 0x80, 0xF0, 0x80),  0x0080F080),
            ((0x80, 0xF0, 0x00, 0x7F), -0x7F0FFF81) ,
            ((0xF0, 0x00, 0x80, 0x00), -0x0FFF8000),
        ]
        samples_littleEndian = [
            ((0xFF, 0xFF, 0xFF, 0xFF), -1),
            ((0x80, 0x00, 0x80, 0xF0), -0x0F7FFF80),
            ((0x80, 0xF0, 0x00, 0x7F), 0x7F00F080),
            ((0xF0, 0x00, 0x80, 0x00), 0x008000F0),
        ]

        # Big endian tests
        for (data, expected) in samples_bigEndian:
            computed = _signed32(data, False)
            msg="32-bit signed big endian decode error %08X != %08X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)
        
        # Little endian tests
        for (data, expected) in samples_littleEndian:
            computed = _signed32(data, True)
            msg="32-bit signed little endian decode error %08X != %08X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)

        # Input data without enough bytes raises AssertionError
        self.assertRaises(AssertionError, _signed32, bytearray([0x01]))
        self.assertRaises(AssertionError, _signed32, bytearray([0x01, 0x02]))
        self.assertRaises(AssertionError, _signed32, bytearray([0x01, 0x02, 0x03]))


    def test_unsigned24(self):
        samples_bigEndian = [
            ((0xFF, 0xFF, 0xFF), 0xFFFFFF),
            ((0x00, 0x80, 0xF0), 0x0080F0),
            ((0x80, 0xF0, 0x00), 0x80F000),
            ((0xF0, 0x00, 0x80), 0xF00080),
        ]
        samples_littleEndian = [
            ((0xFF, 0xFF, 0xFF), 0xFFFFFF),
            ((0x00, 0x80, 0xF0), 0xF08000),
            ((0x80, 0xF0, 0x00), 0x00F080),
            ((0xF0, 0x00, 0x80), 0x8000F0),
        ]

        # Big endian tests
        for (data, expected) in samples_bigEndian:
            computed = _unsigned24(data, False)
            msg = "24-bit unsigned big endian decode error %08X != %08X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)
        
        # Little endian tests
        for (data, expected) in samples_littleEndian:
            computed = _unsigned24(data, True)
            msg = "24-bit unsigned little endian decode error %08X != %08X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)

        # Input data without enough bytes raises AssertionError
        self.assertRaises(AssertionError, _unsigned24, bytearray([0x01]))
        self.assertRaises(AssertionError, _unsigned24, bytearray([0x01, 0x02]))


    def test_signed24(self):
        samples_bigEndian = [
            ((0xFF, 0xFF, 0xFF), -1),
            ((0x00, 0x80, 0xF0),  0x0080F0),
            ((0x80, 0xF0, 0x00), -0x7F1000),
            ((0xF0, 0x00, 0x80), -0x0FFF80),
        ]
        samples_littleEndian = [
            ((0xFF, 0xFF, 0xFF), -1),
            ((0x00, 0x80, 0xF0), -0x0F8000),
            ((0x80, 0xF0, 0x00),  0x00F080),
            ((0xF0, 0x00, 0x80), -0x7FFF10),
        ]

        # Big endian tests
        for (data, expected) in samples_bigEndian:
            computed = _signed24(data, False)
            msg="24-bit signed big endian decode error %06X != %06X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)
        
        # Little endian tests
        for (data, expected) in samples_littleEndian:
            computed = _signed24(data, True)
            msg="24-bit signed little endian decode error %06X != %06X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)

        # Input data without enough bytes raises AssertionError
        self.assertRaises(AssertionError, _signed24, bytearray([0x01]))
        self.assertRaises(AssertionError, _signed24, bytearray([0x01, 0x02]))


    def test_unsigned16(self):
        samples_bigEndian = [
            ((0xFF, 0xFF), 0xFFFF),
            ((0x80, 0x01), 0x8001),
            ((0x01, 0x80), 0x0180),
        ]
        samples_littleEndian = [
            ((0xFF, 0xFF), 0xFFFF),
            ((0x80, 0x01), 0x0180),
            ((0x01, 0x80), 0x8001),
        ]

        # Big endian tests
        for (data, expected) in samples_bigEndian:
            computed = _unsigned16(data, False)
            msg = "16-bit unsigned big endian decode error %04X != %04X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)
        
        # Little endian tests
        for (data, expected) in samples_littleEndian:
            computed = _unsigned16(data, True)
            msg = "16-bit unsigned little endian decode error %04X != %04X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)

        # Input data without enough bytes raises AssertionError
        self.assertRaises(AssertionError, _unsigned16, bytearray([0x01]))


    def test_signed16(self):
        samples_bigEndian = [
            ((0xFF, 0xFF), -1),
            ((0x80, 0x01), -0x7FFF),
            ((0x01, 0x80), 0x0180),
        ]
        samples_littleEndian = [
            ((0xFF, 0xFF), -1),
            ((0x80, 0x01), 0x0180),
            ((0x01, 0x80), -0x7FFF),
        ]

        # Big endian tests
        for (data, expected) in samples_bigEndian:
            computed = _signed16(data, False)
            msg = "16-bit signed big endian decode error %04X != %04X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)
        
        # Little endian tests
        for (data, expected) in samples_littleEndian:
            computed = _signed16(data, True)
            msg = "16-bit signed little endian decode error %04X != %04X" % (computed, expected)
            self.assertEqual(computed, expected, msg=msg)

        # Input data without enough bytes raises AssertionError
        self.assertRaises(AssertionError, _signed16, bytearray([0x01]))


    def test_thunk_byte(self):
        # samples are: inputByte, mask, shift, expectedResult
        samples = [
            (0b10100101, 0b11110000, -4, 0b1010),
            (0b10100101, 0b00111000, -3, 0b100),
            (0b10100101, 0b11100000, -5, 0b101),
            (0b10100101, 0b11100000, -6, 0b10),
            (0b10100101, 0b00001111,  4, 0b01010000),
            (0b10100101, 0b00000111,  6, 0b101000000),
        ]
        for (data, mask, shift, expected) in samples:
            computed = _thunkByte(data, mask, shift)
            msg = "thunkByte(0x%02X, 0x%02X, %d) computed=0x%02X is not expected=0x%02X" % (data, mask, shift, computed, expected)
            self.assertEqual(computed, expected, msg=msg)

        # Illegal input larger than 8-bit raises ValueError exception
        self.assertRaises(ValueError, _thunkByte, 0x101, 0x0f, 0)