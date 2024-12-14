"""
Test GDL-90 recorder functions.
"""

import unittest
from iputils.iputils import IPUtils

class NetworkUtils(unittest.TestCase):
    """Test functionality of network utilities"""

    def test_ipv4_address(self):
        self.assertTrue(IPUtils.is_ipv4_addr('255.255.255.255'))
        self.assertTrue(IPUtils.is_ipv4_addr('0.0.0.0'))
        self.assertTrue(IPUtils.is_ipv4_addr('1.10.100.0'))
        # negative tests
        self.assertFalse(IPUtils.is_ipv4_addr('256.255.255.255'))
        self.assertFalse(IPUtils.is_ipv4_addr('1.099.100.10'))
        self.assertFalse(IPUtils.is_ipv4_addr('1.999.100.10'))
        self.assertFalse(IPUtils.is_ipv4_addr('no.way.no.how'))

    def test_ipv4_loopback(self):
        self.assertTrue(IPUtils.is_ipv4_loopback('127.0.0.1'))
        self.assertTrue(IPUtils.is_ipv4_loopback('127.0.1.1'))
        self.assertTrue(IPUtils.is_ipv4_loopback('127.255.1.1'))
        self.assertTrue(IPUtils.is_ipv4_loopback('127.1.1.0'))
        # negative tests
        self.assertFalse(IPUtils.is_ipv4_loopback('126.0.0.1'))
        self.assertFalse(IPUtils.is_ipv4_loopback('127.256.0.1'))
        self.assertFalse(IPUtils.is_ipv4_loopback('1.0.0.127'))

    def test_ipv4_str_to_int(self):
        self.assertEqual(IPUtils._ipv4_str_to_int('0.0.0.0'), 0)
        self.assertEqual(IPUtils._ipv4_str_to_int('255.255.255.255'), 4294967295)
        self.assertEqual(IPUtils._ipv4_str_to_int('10.5.12.3'), 168102915)
        # negative tests
        self.assertRaises(ValueError, IPUtils._ipv4_str_to_int, '10.20.30')
        self.assertRaises(ValueError, IPUtils._ipv4_str_to_int, '10.20')
        self.assertRaises(ValueError, IPUtils._ipv4_str_to_int, '')

    def test_ipv4_int_to_str(self):
        self.assertEqual(IPUtils._ipv4_int_to_str(0), '0.0.0.0')
        self.assertEqual(IPUtils._ipv4_int_to_str(4294967295), '255.255.255.255')
        self.assertEqual(IPUtils._ipv4_int_to_str(168102915), '10.5.12.3')
        # negative tests
        self.assertRaises(ValueError, IPUtils._ipv4_int_to_str, -1)
        self.assertRaises(ValueError, IPUtils._ipv4_int_to_str, 2**32)

    def test_ipv4_broadcast_addr(self):
        self.assertEqual(IPUtils.ipv4_broadcast_addr('1.2.3.4', 24), '1.2.3.255')
        self.assertEqual(IPUtils.ipv4_broadcast_addr('1.2.3.4', 16), '1.2.255.255')
        self.assertEqual(IPUtils.ipv4_broadcast_addr('1.2.3.4', 8), '1.255.255.255')
        self.assertEqual(IPUtils.ipv4_broadcast_addr('11.22.33.44', 22), '11.22.35.255')
        # negative tests
        self.assertRaises(ValueError, IPUtils.ipv4_broadcast_addr, '300.2.3.4', 24)
        self.assertRaises(ValueError, IPUtils.ipv4_broadcast_addr, '1.2.3.4', -1)
        self.assertRaises(ValueError, IPUtils.ipv4_broadcast_addr, '1.2.3.4', 33)

    def test_ipv4_network_addr(self):
        self.assertEqual(IPUtils.ipv4_network_addr('1.2.3.4', 24), '1.2.3.0')
        self.assertEqual(IPUtils.ipv4_network_addr('1.2.3.4', 16), '1.2.0.0')
        self.assertEqual(IPUtils.ipv4_network_addr('1.2.3.4', 8), '1.0.0.0')
        self.assertEqual(IPUtils.ipv4_network_addr('11.22.33.44', 22), '11.22.32.0')
        # negative tests
        self.assertRaises(ValueError, IPUtils.ipv4_network_addr, '300.2.3.4', 24)

    def test_ipv4_network_mask(self):
        self.assertEqual(IPUtils.ipv4_network_mask(24), '255.255.255.0')
        self.assertEqual(IPUtils.ipv4_network_mask(16), '255.255.0.0')
        self.assertEqual(IPUtils.ipv4_network_mask(13), '255.248.0.0')
        self.assertEqual(IPUtils.ipv4_network_mask(7), '254.0.0.0')
        # negative tests
        self.assertRaises(ValueError, IPUtils.ipv4_network_mask, 33)
        self.assertRaises(ValueError, IPUtils.ipv4_network_mask, -1)

    def test_ipv4_multicast_addr(self):
        self.assertTrue(IPUtils.is_ipv4_multicast('224.0.100.200'))
        self.assertTrue(IPUtils.is_ipv4_multicast('233.252.100.200'))
        self.assertTrue(IPUtils.is_ipv4_multicast('239.255.100.200'))
        # negative tests
        self.assertFalse(IPUtils.is_ipv4_multicast('223.255.255.255'))
        self.assertFalse(IPUtils.is_ipv4_multicast('240.0.0.0'))
        self.assertFalse(IPUtils.is_ipv4_multicast('224.0.0'))



