"""
Networking functions used by GDL 90 utilities

This depends upon the 'ifaddr' package in order to get information about
the hosts network interfaces. It is installed with:
  # pip3 install ifaddr

"""

import re, sys
from collections import namedtuple

try:
    import ifaddr
except ImportError:
    sys.stderr.write("ERROR: could not import 'ifaddr' package; see README.md for install instructions/n")
    sys.exit(1)


IPV4_ADDR_RE = r'''^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$'''
IPV4_LOOPBACK_ADDR_RE = r'''^127\.((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){3}$'''


class IPUtils(object):

    @staticmethod
    def is_ipv4_addr(addr: str) -> bool:
        if re.match(IPV4_ADDR_RE, addr) is None:
            return False
        return True


    @staticmethod
    def is_ipv4_loopback(addr: str) -> bool:
        if re.match(IPV4_LOOPBACK_ADDR_RE, addr) is None:
            return False
        return True
    

    @staticmethod
    def is_ipv4_multicast(addr:str) -> bool:
        if not IPUtils.is_ipv4_addr(addr):
            return False
        
        # the 4 most significant bits of a mcast addr are 1110
        ipnum = IPUtils._ipv4_str_to_int(addr)
        if (ipnum >> 28) != 0b1110:
            return False
        return True


    @staticmethod
    def ipv4_broadcast_addr(addr:str, netmask_bits:int) -> str:
        if not IPUtils.is_ipv4_addr(addr):
            raise ValueError("invalid IPv4 address format")

        ipnum = IPUtils._ipv4_str_to_int(addr)
        (netmask, hostmask) = IPUtils._ipv4_mask_nums(netmask_bits)
        bcastnum = ipnum | hostmask
        return IPUtils._ipv4_int_to_str(bcastnum)


    @staticmethod
    def ipv4_network_addr(addr:str, netmask_bits:int) -> str:
        if not IPUtils.is_ipv4_addr(addr):
            raise ValueError("invalid IPv4 address format")

        ipnum = IPUtils._ipv4_str_to_int(addr)
        (netmask, hostmask) = IPUtils._ipv4_mask_nums(netmask_bits)
        networknum = ipnum & netmask
        return IPUtils._ipv4_int_to_str(networknum)
    

    @staticmethod
    def ipv4_network_mask(netmask_bits:int) -> str:
        """returns a dotted notation string of a network mask"""
        if (netmask_bits > 32) or (netmask_bits < 0):
            raise ValueError("invalid netmask size")
        shift = 32 - netmask_bits
        netmask = (0xFFFFFFFF >> shift) << shift  # produces zeros on left-shift
        return IPUtils._ipv4_int_to_str(netmask)


    @staticmethod
    def _ipv4_str_to_int(addr:str) -> int:
        """computes 32-bit int from dotted notation; does not pre-validate IP syntax"""
        octets = addr.split('.')  # MSB-first ordering
        if len(octets) != 4:
            raise ValueError("invalid IPv4 address format")
        
        ipnum = 0
        for shift in range(0, 32, 8):
            octet = octets.pop()  # remove last LSB item
            ipnum += int(octet) << shift
        return ipnum


    @staticmethod
    def _ipv4_int_to_str(ipnum:int) -> str:
        """creates dotted notation from 32-bit int"""
        if ((ipnum & 0xFFFFFFFF) != ipnum) or (ipnum < 0):
            raise ValueError("invalid IPv4 value")
        
        octets = []
        for shift in range(0, 32, 8):
            mask = 0xFF << shift
            octet = str((ipnum & mask) >> shift)
            octets.insert(0, octet)  # insert MSB at start of list
        return ".".join(octets)
    

    @staticmethod
    def _ipv4_mask_nums(netmask_bits: int) -> tuple[int, int]:
        """returns 32-bit numbers for (network, host) masks"""
        if (netmask_bits > 32) or (netmask_bits < 0):
            raise ValueError("invalid netmask size")

        shift = 32 - netmask_bits
        netmask = (0xFFFFFFFF >> shift) << shift  # produces zeros on left-shift
        hostmask = netmask ^ 0xFFFFFFFF
        return tuple([netmask, hostmask])


# Namedtuple that holds network details for an interface
IPInterface = namedtuple('IPInterface', 'name ip netmask broadcast netmask_bits')

class Interfaces(object):

    def __init__(self) -> None:
        self._ip_interfaces = {}
        self.scan_interfaces()


    def scan_interfaces(self) -> None:
        """scan all interfaces and refresh the list of adapters/IPs"""
        self._adapters = ifaddr.get_adapters()
        self._ip_interfaces = {
            'ipv4': [],
            'ipv4_loopback': [],
        }
        for adapter in self._adapters:
            for ip in adapter.ips:
                if ip.is_IPv4:
                    if not ip.is_IPv4:
                        continue
                    name = adapter.name
                    ipaddr = ip.ip
                    netmask_bits = ip.network_prefix
                    netmask = IPUtils.ipv4_network_mask(netmask_bits)
                    broadcast = IPUtils.ipv4_broadcast_addr(ip.ip, netmask_bits)
                    iface = IPInterface._make([name, ipaddr, netmask, broadcast, netmask_bits])

                    if IPUtils.is_ipv4_loopback(iface.ip):
                        self._ip_interfaces['ipv4_loopback'].append(iface)
                    else:
                        self._ip_interfaces['ipv4'].append(iface)

    def ipv4_details_by_name(self, name:str) -> IPInterface:
        """returns all network details for named interface"""
        for iface_type in ['ipv4', 'ipv4_loopback']:
            for iface in self._ip_interfaces[iface_type]:
                if iface.name == name:
                    return iface


    def ipv4_address_by_name(self, name:str) -> str:
        """returns the first IP associated with interface name"""
        for iface_type in ['ipv4', 'ipv4_loopback']:
            for iface in self._ip_interfaces[iface_type]:
                if iface.name == name:
                    return iface.ip
        return None
    

    def ipv4_name_by_address(self, ip:str) -> str:
        """returns the interface name associated with IP address"""
        for iface_type in ['ipv4', 'ipv4_loopback']:
            for iface in self._ip_interfaces[iface_type]:
                if iface.ip == ip:
                    return iface.name
        return None
    

    def ipv4_all_addresses(self, include_loopback=False) -> list[str]:
        """returns list of all IPv4 addresses; if loopbacks are
        included, they will come first in the list"""
        ip_list = []
        for iface_type in ['ipv4_loopback', 'ipv4']:
            if iface_type == 'ipv4_loopback' and not include_loopback:
                continue  # skip loopback IPs 
            for iface in self._ip_interfaces[iface_type]:
                ip_list.append(iface.ip)
        return ip_list


    def ipv4_all_interfaces(self, include_loopback=False) -> list[str]:
        """returns list of all IPv4 interfaces; if loopbacks are
        included, they will come first in the list"""
        iface_list = []
        for iface_type in ['ipv4_loopback', 'ipv4']:
            if iface_type == 'ipv4_loopback' and not include_loopback:
                continue  # skip loopback interfaces 
            for iface in self._ip_interfaces[iface_type]:
                iface_list.append(iface.name)
        return iface_list

