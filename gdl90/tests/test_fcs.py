"""
Test CRC computations
"""

import unittest

from gdl90.fcs import crcCompute, crcCheck, CRC16Table, createCRC16Table

class CRCChecks(unittest.TestCase):

    # The first 4 entries are sample GDL-90 messages,
    # next 9 are patterns that use every 8-bit value,
    # remainder are random input.
    good_values = [
        ([0x00, 0x81, 0x41, 0xDB, 0xD0, 0x08, 0x02], [0xb3, 0x8b]),
        ([0x00, 0x81, 0x00, 0x28, 0xc9, 0x01, 0x00], [0xa6, 0x6d]),
        ([0x0b, 0x00, 0x69, 0x00, 0x32], [0x4c, 0x0d]),
        ([0x0a, 0x00, 0x00, 0x00, 0x00, 0x15, 0x76, 0x78, 0xba, 0x8d, 0x1f, 0x03, 0xb9, 0x88, 0x00, 0x00, 0x00, 0xa8, 0x01, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x00], [0x97, 0x33]),
        ([0, 0, 0, 0, 0, 0, 0, 0], [0, 0]), 
        ([0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, 152, 160, 168, 176, 184, 192, 200, 208, 216, 224, 232, 240, 248], [112, 8]),
        ([1, 9, 17, 25, 33, 41, 49, 57, 65, 73, 81, 89, 97, 105, 113, 121, 129, 137, 145, 153, 161, 169, 177, 185, 193, 201, 209, 217, 225, 233, 241, 249], [161, 220]),
        ([2, 10, 18, 26, 34, 42, 50, 58, 66, 74, 82, 90, 98, 106, 114, 122, 130, 138, 146, 154, 162, 170, 178, 186, 194, 202, 210, 218, 226, 234, 242, 250], [243, 177]),
        ([3, 11, 19, 27, 35, 43, 51, 59, 67, 75, 83, 91, 99, 107, 115, 123, 131, 139, 147, 155, 163, 171, 179, 187, 195, 203, 211, 219, 227, 235, 243, 251], [34, 101]),
        ([4, 12, 20, 28, 36, 44, 52, 60, 68, 76, 84, 92, 100, 108, 116, 124, 132, 140, 148, 156, 164, 172, 180, 188, 196, 204, 212, 220, 228, 236, 244, 252], [87, 107]),
        ([5, 13, 21, 29, 37, 45, 53, 61, 69, 77, 85, 93, 101, 109, 117, 125, 133, 141, 149, 157, 165, 173, 181, 189, 197, 205, 213, 221, 229, 237, 245, 253], [134, 191]),
        ([6, 14, 22, 30, 38, 46, 54, 62, 70, 78, 86, 94, 102, 110, 118, 126, 134, 142, 150, 158, 166, 174, 182, 190, 198, 206, 214, 222, 230, 238, 246, 254], [212, 210]),
        ([7, 15, 23, 31, 39, 47, 55, 63, 71, 79, 87, 95, 103, 111, 119, 127, 135, 143, 151, 159, 167, 175, 183, 191, 199, 207, 215, 223, 231, 239, 247, 255], [5, 6]),
        ([29, 156, 204, 54, 20, 187, 191, 88], [170, 20]),
        ([120, 99, 68, 56, 173, 205, 216, 69], [63, 204]),
        ([251, 183, 168, 215, 79, 46, 29, 83], [72, 81]),
        ([54, 58, 185, 201, 168, 84, 45, 19], [88, 241]),
        ([180, 84, 1, 75, 137, 85, 63, 176], [49, 110]),
        ([165, 146, 215, 238, 80, 128, 23, 3], [10, 10]), 
        ([18, 203, 217, 177, 133, 161, 203, 147], [13, 86]),
    ]

    # These random inputs should fail to match their CRCs
    bad_values = [
        ([11, 240, 255, 35, 111, 237, 12, 102], [135, 210]), 
        ([42, 21, 132, 175, 151, 109, 76, 25], [149, 225]), 
        ([185, 65, 191, 231, 89, 168, 141, 1], [168, 164]),
        ([254, 255, 255, 255, 255, 255, 255, 255], [32, 104]),
    ]


    def _as_hex_str(self, data:bytearray) -> str:
        values = []
        for byte in data:
            values.append(hex(byte))
        return "[%s]" % (",".join(values))
        

    def test_crc_good(self):
        for (test, crc) in self.good_values:
            test_str = self._as_hex_str(test)
            crc_str = self._as_hex_str(crc)
            res_str = self._as_hex_str(crcCompute(test))
            msg = "input=%s, expected_crc=%s, computed_crc=%s" % (test_str, crc_str, res_str)
            self.assertTrue(crcCheck(test, crc), msg=msg)
    

    def test_crc_bad(self):
        for (test, crc) in self.bad_values:
            test_str = self._as_hex_str(test)
            msg = "input=%s should fail validation" % (test_str)
            self.assertFalse(crcCheck(test, crc), msg=msg)
        (test, crc) = self.bad_values[0]
        self.assertRaises(Exception, crcCheck, test, [0x01])  # crc too short
        self.assertRaises(Exception, crcCheck, test, [0x01,0x02,0x03])  # crc too long


    def test_crc_table(self):
        computed = createCRC16Table()

        self.assertEqual(256, len(computed), msg="incorrect computed table size; not equal 256")
        self.assertEqual(256, len(CRC16Table), msg="incorrect static table size; not equal 256")

        for table_index in range(256):
            element_static = CRC16Table[table_index]
            element_computed = computed[table_index]
            msg = "crc16_table[%03d] static=0x%04X not equal to computed=0x%04X" % (table_index, element_static, element_computed)
            self.assertEqual(element_static, element_computed, msg=msg)
