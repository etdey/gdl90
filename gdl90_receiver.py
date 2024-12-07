#!/usr/bin/env python3
#
"""GDL-90 Receiver

This program implements a receiver of the GDL-90 data link interface.

"""

__progTitle__ = "GDL-90 Receiver"

__author__ = "Eric Dey <eric@deys.org>"
__created__ = "August 2012"
__copyright__ = "Copyright (C) 2024 by Eric Dey"

__version__ = "0.3"
__date__ = "DEC-2024"


import os, sys, datetime, re, optparse, socket
import gdl90.decoder
from iputils.iputils import Interfaces


# Default values for options
DEF_RECV_PORT=43211
DEF_RECV_MAXSIZE=9000
DEF_REPORT_COUNT=100

# Exit codes
EXIT_CODE = {
    "OK" : 0,
    "OPTIONS" : 1,
    "OTHER" : 99,
}

# Network interface singleton
NetIfaces = Interfaces()


def print_error(msg):
    """print to stderr"""
    print(msg, file=sys.stderr)


def _options_okay(options):
    """test to see if options are valid"""
    errors = False
    
    if int(options.port) <=0 or int(options.port) >=65536:
        errors = True
        print_error("Argument '--port' must between 1 and 65535")
        
    return not errors


def _get_progVersion():
    """return program version string"""
    return "%s" % (__version__)


def _getTimeStamp():
    """create a time stamp string"""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(' ')


def _extractSvnKeywordValue(s):
    """Extracts the value string from an SVN keyword property string."""
    if re.match(r'^\$[^:]*\$$', s):
        return ""
    return re.sub(r'^\$[^:]*: (.*)\$$', r'\1', s).strip(' ')


def _receive(options):
    """receive packets"""

    decoder = gdl90.decoder.Decoder()

    options.listen_ip = None  # used when receiving from network not a file
    
    if options.date:
        (year, month, day) = options.date.split("-")
        dayStart = datetime.date(int(year), int(month), int(day))
    else:
        dayStart = datetime.date.today()
    decoder.dayStart = dayStart
    
    if options.plotflight:
        decoder.format = 'plotflight'
    
    if options.uat:
        decoder.uatOutput = True
    
    if options.inputfile:
        useNetwork = False
        s = open(options.inputfile, "rb")
    else:
        useNetwork = True

        # use a specific interface, subnet broadcast, or global broadcast
        iface = NetIfaces.ipv4_details_by_name(options.interface)
        if iface is None:
            print_error("Receive interface %s does not have an IP address" % (options.interface))
            sys.exit(EXIT_CODE['OTHER'])

        if options.subnetbcast:
            # subnet broadcast (e.g., x.y.z.255)
            options.listen_ip = iface.broadcast
        
        elif options.bcast:
            # global broadcast 255.255.255.255
            options.listen_ip = '<broadcast>'  # special meaning for socket.socket.bind()

        else:
            # adapter's IP address (i.e., unicast)
            options.listen_ip = iface.ip

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if options.verbose:
            print_error("Listening on interface %s at address %s on port %s" % (options.interface, options.listen_ip, options.port))
        s.bind((options.listen_ip, options.port))
    
    packetTotal = 0
    
    while True:
        if useNetwork:
            (data, dataSrc) = s.recvfrom(options.maxsize)
            (saddr, sport) = dataSrc
            sender = "%s:%s" % (saddr, sport)
        else:
            data = s.read(options.maxsize)
            if len(data) == 0:
                break
            sender = "file:%s" % (options.inputfile)
        
        packetTotal += 1
        if packetTotal % options.reportcount == 0:
            ts = _getTimeStamp()
            print_error("[%s] %s packets received from %s" % (ts, packetTotal, sender))
        
        decoder.addBytes(data)

    s.close()




# Interactive Runs
if __name__ == '__main__':

    # get default network interface device
    try:
        def_interface = NetIfaces.ipv4_all_interfaces()[0]
    except IndexError:
        def_interface = NetIfaces.ipv4_all_interfaces(include_loopback=True)[0]  # loopback device
    
    # Get name of program from command line or else use embedded default
    progName = os.path.basename(sys.argv[0])

    # Create other program tags from SVN strings
    progDate = _extractSvnKeywordValue(__date__)
    progVersion = _get_progVersion()
    
    #
    # Setup option parsing
    #
    usageMsg = "usage: %s [options]" % (progName)
    versionMsg = "%s version %s (%s)" % (progName, progVersion, progDate)
    descriptionMsg = __progTitle__ + """ is a data receiver and decoder."""
    epilogMsg = """"""
    optParser = optparse.OptionParser(usage=usageMsg, 
                                      version=versionMsg,
                                      description=descriptionMsg,
                                      epilog=epilogMsg)

    # add options outside of any option group
    optParser.add_option("--verbose", "-v", action="store_true", help="Verbose reporting on STDERR")

    # optional options
    group = optparse.OptionGroup(optParser,"Optional")
    group.add_option("--interface", action="store", default=def_interface, metavar="name", help="receive interface name (default=%default)")
    group.add_option("--port","-p", action="store", default=DEF_RECV_PORT, type="int", metavar="NUM", help="receive port (default=%default)")
    group.add_option("--maxsize","-s", action="store", default=DEF_RECV_MAXSIZE, type="int", metavar="BYTES", help="maximum packet size (default=%default)")
    group.add_option("--reportcount","-r", action="store", default=DEF_REPORT_COUNT, type="int", metavar="PACKETS", help="report after receiving this many packets (default=%default)")
    group.add_option("--inputfile","-i", action="store", metavar="FILE", help="read from input file instead of network")
    group.add_option("--date", action="store", metavar="YYYY-MM-DD", help="UTC starting date for data (default=now)")
    group.add_option("--plotflight", action="store_true", help="output plotflight format")
    group.add_option("--uat", action="store_true", help="output UAT messages")
    group.add_option("--bcast", action="store_true", help="listen on 255.255.255.255")
    group.add_option("--subnetbcast", action="store_true", help="listen on subnet broadcast")
    optParser.add_option_group(group)

    # do the option parsing
    (options, args) = optParser.parse_args(args=sys.argv[1:])

    # check options
    if not _options_okay(options):
        print_error("Stopping due to option errors.")
        sys.exit(EXIT_CODE['OPTIONS'])

    _receive(options)
