#!/usr/bin/env python
#
"""GDL-90 Recorder

This program records RAW output from the GDL-90 data link interface.

This depends upon the 'netifaces' package in order to get information about
the hosts network interfaces. It is installed with:
  # apt-get install python-pip
  # pip install netifaces

"""

__progTitle__ = "GDL-90 Recorder"

__author__ = "Eric Dey <eric@deys.org>"
__created__ = "September 2012"
__copyright__ = "Copyright (C) 2018 by Eric Dey"

__version__ = "1.3"
__date__ = "16-NOV-2018"


import os, sys, time, datetime, re, optparse, socket, struct, threading

try:
    import netifaces
except ImportError:
    sys.stderr.write("ERROR: could not import 'netifaces' package; use 'pip install netifaces' to add it/n")
    sys.exit(1)

# Default values for options
DEF_RECV_PORT=43211
DEF_RECV_MAXSIZE=1500
DEF_DATA_FLUSH_SECS=10
DEF_LOG_PREFIX="/root/skyradar"

SLOWEXIT_DELAY=15

# Exit codes
EXIT_CODE = {
    "OK" : 0,
    "OPTIONS" : 1,
    "OTHER" : 99,
}


def print_error(msg):
    """print an error message"""
    print(msg, file=sys.stderr)


def _isNumeric(n):
    """test if 'n' can be converted for use in numeric calculations"""
    try:
        b = float(n)
        return True
    except:
        pass
    return False


def _options_okay(options):
    """test to see if options are valid"""
    errors = False
    
    if int(options.port) <=0 or int(options.port) >=65536:
        errors = True
        print_error("Argument '--port' must between 1 and 65535")
    
    if options.interface == '':
        # this means use all interfaces
        pass
    elif _getAddressByIfaceName(options.interface) is None:
        errors = True
        print_error("Argument '--interface' is not a valid interface name")
    else:
        try:
            netifaces.ifaddresses(options.interface)[netifaces.AF_INET][0]
        except KeyError:
            errors = True
            print_error("Receive interface does not have an IP address")
    
    if options.rebroadcast != "":
        if options.interface == '':
            errors = True
            print_error("Argument '--interface' cannot by all when using --rebroadcast option") 
        
        if _getAddressByIfaceName(options.rebroadcast) is None:
            print_error("Argument '--rebroadcast' is not a valid interface name; disabling rebroadcast")
            options.rebroadcast = ""
        elif options.interface == options.rebroadcast:
            print_error("Receive interface must be different from rebroadcast interface; disabling rebroadcast")
            options.rebroadcast = ""
        else:
            try:
                netifaces.ifaddresses(options.rebroadcast)[netifaces.AF_INET][0]
            except KeyError:
                print_error("Rebroadcast interface does not have an IP address; disabling rebroadcast")
                options.rebroadcast = ""
    
    return not errors


def _get_progVersion():
    """return program version string"""
    return "%s" % (__version__)


def _getTimeStamp():
    """create a time stamp string"""
    return datetime.datetime.utcnow().isoformat(' ')


def _extractSvnKeywordValue(s):
    """Extracts the value string from an SVN keyword property string."""
    if re.match(r'^\$[^:]*\$$', s):
        return ""
    return re.sub(r'^\$[^:]*: (.*)\$$', r'\1', s).strip(' ')


def _nextFileName(dirName, baseName='gdl90_cap', fmt=r'%s/%s.%03d'):
    if not os.path.isdir(dirName):
        Exception("Directory %s does not exist" % (dirName))

    i = 0
    while i < 1000:
        fname = fmt % (dirName, baseName, i)
        if not os.path.exists(fname):
            return fname
        i += 1
    raise Exception("Search exhausted; too many files exist already.")


def _getAddressByIfaceName(ifname, broadcast=False):
    """return an IP address for a named interface
    Only the first IP address is returned if multiple exist.
    @ifname: interface name string
    @broadcast: return network broadcast address instead of interface addr
    @return: IP address string or None if error
    """
    
    if ifname == '':
        return ''
    
    if not ifname in netifaces.interfaces():
        return None
    
    try:
        ifdetails = netifaces.ifaddresses(ifname)[netifaces.AF_INET][0]
    except KeyError:
        return None
    
    if broadcast:
        return ifdetails['broadcast']
    
    return ifdetails['addr']


def _record(options):
    """record packets"""

    logFile = None
    logFileName = _nextFileName(options.logprefix)
    if options.verbose == True:
        print_error("will use log file name '%s'" % (logFileName))

    try:
        if options.subnetbcast:
            listenIP = netifaces.ifaddresses(options.interface)[netifaces.AF_INET][0]['broadcast']
        elif options.bcast:
            listenIP = '<broadcast>'
        else:
            listenIP = ''
    except KeyError as e:
        sys.stderr.write("ERROR: error getting network details for '%s' %s\n" % (options.interface,e))
        sys.exit(1)
    sockIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockIn.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sockIn.bind((listenIP, options.port))
        
    packetTotal = 0
    bytesTotal = 0
    lastFlushTime = time.time()
    
    if options.verbose == True:
        print_error("Listening on interface '%s' at address '%s' port '%s'" % (options.interface, listenIP, options.port))
    
    sockOut = None
    if options.rebroadcast != "":
        sockOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sockOut.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sockOutSendToAddr = _getAddressByIfaceName(options.rebroadcast, broadcast=True)
        if options.verbose == True:
            print_error("Rebroadcasting on interface ''%s' at address '%s' port '%s'" % (options.rebroadcast, _getAddressByIfaceName(options.rebroadcast), options.port))
    
    
    try:
        while True:
            (data, dataSrc) = sockIn.recvfrom(DEF_RECV_MAXSIZE)
            (saddr, sport) = dataSrc
            packetTotal += 1
            bytesTotal += len(data)
            
            #optionally rebroadcast onto another network
            if sockOut is not None:
                sockOut.sendto(data, (sockOutSendToAddr, options.port))
            
            # Create log file only when the first bytes arrive
            if logFile is None:
                logFile = open(logFileName, "wb")
                if options.verbose == True:
                    print_error("created log file '%s'" %(logFileName))
            
            logFile.write(data)
            
            # Ensure periodic flush to disk
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
        def_interface = netifaces.interfaces()[1]
    except IndexError:
        def_interface = netifaces.interfaces()[0]   # loopback device

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
    group.add_option("--logprefix", action="store", default=DEF_LOG_PREFIX, metavar="PATH", help="path prefix for log file names (default=%default)")
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
