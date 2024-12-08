#!/usr/bin/env python3
#
"""GDL-90 Recorder

This program records RAW output from the GDL-90 data link interface.

"""

__progTitle__ = "GDL-90 Recorder"

__author__ = "Eric Dey <eric@deys.org>"
__created__ = "September 2012"
__copyright__ = "Copyright (C) 2024 by Eric Dey"

__version__ = "1.4"
__date__ = "DEC-2024"


import optparse, os, re, socket, sys, time
from iputils.iputils import Interfaces


# Default values for options
DEF_RECV_PORT=43211
DEF_RECV_MAXSIZE=1500
DEF_DATA_FLUSH_SECS=10
DEF_LOG_DIR="/root/gdl90-data"

SLOWEXIT_DELAY=15

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

    options.listen_ip = None
    options.rebroadcast_ip = None
    
    if int(options.port) <=0 or int(options.port) >=65536:
        errors = True
        print_error("Argument '--port' must between 1 and 65535")
    
    if options.interface == '':
        # this means use all interfaces
        options.listen_ip = ''  # special meaning for socket.socket.bind()
    
    else:
        # use a specific interface, subnet broadcast, or global broadcast
        iface = NetIfaces.ipv4_details_by_name(options.interface)
        if iface is None:
            errors = True
            print_error("Receive interface %s does not have an IP address" % (options.interface))
        else: 
            if options.subnetbcast:
                # subnet broadcast (e.g., x.y.z.255)
                options.listen_ip = iface.broadcast
            
            elif options.bcast:
                # global broadcast 255.255.255.255
                options.listen_ip = '<broadcast>'  # special meaning for socket.socket.bind()

            else:
                # adapter's IP address (i.e., unicast)
                options.listen_ip = iface.ip

    if options.rebroadcast != '':
        if options.interface == '':
            errors = True
            print_error("Argument '--interface' must be specified when using --rebroadcast option") 
        else:
            iface = NetIfaces.ipv4_details_by_name(options.rebroadcast)
            if iface is None:
                options.rebroadcast_ip = None
            else:
                options.rebroadcast_ip = iface.broadcast
        
        if options.rebroadcast_ip is None:
            print_error("Rebroadcast interface %s does not have an IP address" % (options.rebroadcast))
            options.rebroadcast = ''
        elif options.interface == options.rebroadcast:
            print_error("Receive interface must be different from rebroadcast interface; disabling rebroadcast")
            options.rebroadcast = ''
            options.rebroadcast_ip = None
    
    return not errors


def _get_progVersion():
    """return program version string"""
    return "%s" % (__version__)


def _extractSvnKeywordValue(s):
    """Extracts the value string from an SVN keyword property string."""
    if re.match(r'^\$[^:]*\$$', s):
        return ""
    return re.sub(r'^\$[^:]*: (.*)\$$', r'\1', s).strip(' ')


def _nextFileName(dirName, baseName='gdl90_cap', fmt=r'%s/%s.%03d'):
    if not os.path.isdir(dirName):
        Exception("Directory %s does not exist" % (dirName))

    for i in range(0, 1000):
        fname = fmt % (dirName, baseName, i)
        if not os.path.exists(fname):
            return fname
    raise Exception("Search exhausted; too many files exist already.")


def _record(options):
    """record packets and optionally rebroadcast to another interface"""

    logFile = None
    logFileName = _nextFileName(options.logdir)
    if options.verbose == True:
        print_error("will use log file name '%s'" % (logFileName))

    sockIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockIn.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sockIn.bind((options.listen_ip, options.port))
    
    packetTotal = 0
    bytesTotal = 0
    lastFlushTime = time.time()
    
    if options.verbose == True:
        print_error("Listening on interface '%s' at address '%s' port '%s'" % (options.interface, options.listen_ip, options.port))
    
    sockOut = None
    if options.rebroadcast != '':
        sockOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sockOut.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if options.verbose == True:
            print_error("Rebroadcasting on interface ''%s' at address '%s' port '%s'" % (options.rebroadcast, options.rebroadcast_ip, options.port))
    
    try:
        while True:
            (data, dataSrc) = sockIn.recvfrom(DEF_RECV_MAXSIZE)
            (saddr, sport) = dataSrc
            packetTotal += 1
            bytesTotal += len(data)

            if options.verbose and (packetTotal % 100) == 0:
                print_error("[%s packets received at %s]" % (packetTotal, options.listen_ip))
            
            #optionally rebroadcast onto another network
            if sockOut is not None:
                sockOut.sendto(data, (options.rebroadcast_ip, options.port))
            
            # Create log file only when the first bytes arrive
            if logFile is None:
                logFile = open(logFileName, "wb")
                if options.verbose == True:
                    print_error("created log file '%s'" %(logFileName))
            
            logFile.write(data)
            
            # Ensure periodic flush to disk
            # TODO: This doesn't work because sockIn.recvfrom() blocks
            if int(time.time() - lastFlushTime) > options.dataflush:
                logFile.flush()
                os.fsync(logFile.fileno())
                lastFlushTime = time.time()
                if options.verbose == True:
                    print_error("[%s] disk flush" %(lastFlushTime))
            
    except Exception as e:
        print(e)

    if logFile: logFile.close()
    sockIn.close()
    if sockOut is not None:
        sockOut.close()
    print("Recorded %d packets and %d bytes." % (packetTotal, bytesTotal))


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
    descriptionMsg = __progTitle__ + """ is a data receiver."""
    epilogMsg = """"""
    optParser = optparse.OptionParser(usage=usageMsg, 
                                      version=versionMsg,
                                      description=descriptionMsg,
                                      epilog=epilogMsg)

    # add options outside of any option group
    optParser.add_option("--verbose", "-v", action="store_true", help="Verbose reporting on STDERR")
    optParser.add_option("--slowexit", action="store_true", help="Delay error exit for %s seconds" % (SLOWEXIT_DELAY))

    # optional options
    group = optparse.OptionGroup(optParser,"Optional")
    group.add_option("--interface", action="store", default=def_interface, metavar="name", help="receive interface name (default=%default)")
    group.add_option("--port","-p", action="store", default=DEF_RECV_PORT, type="int", metavar="NUM", help="receive port (default=%default)")
    group.add_option("--maxsize","-s", action="store", default=DEF_RECV_MAXSIZE, type="int", metavar="BYTES", help="maximum packet size (default=%default)")
    group.add_option("--dataflush", action="store", default=DEF_DATA_FLUSH_SECS, type="int", metavar="SECS", help="seconds between data file flush (default=%default)")
    group.add_option("--logdir", action="store", default=DEF_LOG_DIR, metavar="PATH", help="log file directory (default=%default)")
    group.add_option("--rebroadcast", action="store", default="", metavar="name", help="rebroadcast interface (default=off)")
    group.add_option("--bcast", action="store_true", help="listen on 255.255.255.255")
    group.add_option("--subnetbcast", action="store_true", help="listen on subnet broadcast")

    optParser.add_option_group(group)

    # do the option parsing
    (options, args) = optParser.parse_args(args=sys.argv[1:])

    # check options
    if not _options_okay(options):
        print_error("Stopping due to option errors.")
        if options.slowexit == True:
            print_error("  ... pausing for %s seconds before exit." % (SLOWEXIT_DELAY))
            time.sleep(SLOWEXIT_DELAY)
        sys.exit(EXIT_CODE['OPTIONS'])

    _record(options)
