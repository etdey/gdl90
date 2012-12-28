#!/usr/bin/env python
#
"""GDL-90 Sender

This program implements a sender of the GDL-90 data format.

Copyright (c) 2012 by Eric Dey; All rights reserved
"""

__progTitle__ = "GDL-90 Sender"

__author__ = "Eric Dey <eric@deys.org>"
__created__ = "August 2012"
__copyright__ = "Copyright (c) 2012 by Eric Dey"

__date__ = "$Date$"
__version__ = "0.1"
__revision__ = "$Revision$"
__lastChangedBy__ = "$LastChangedBy$"


import os, sys, time, datetime, re, optparse, socket, struct

# Default values for options
DEF_SEND_ADDR="255.255.255.255"
DEF_SEND_PORT=43211
DEF_SEND_SIZE=50
DEF_SEND_INTERVAL_MS=10

# Exit codes
EXIT_CODE = {
    "OK" : 0,
    "OPTIONS" : 1,
    "OTHER" : 99,
}


def print_error(msg):
    """print an error message"""
    print >> sys.stderr, msg


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
    
    if int(options.size) <= 0:
        errors = True
        print_error("Agument '--size' must be greater than 0")
    
    if not (options.file == "" or os.path.exists(options.file)):
        errors = True
        print_error("Agument '--file' points to non-existent file")
    
    return not errors


def _get_progVersion():
    """return program version string"""
    rev = _extractSvnKeywordValue(__revision__)
    return "%s.%s" % (__version__, rev)


def _getTimeStamp():
    """create a time stamp string"""
    return datetime.datetime.utcnow().isoformat(' ')


def _extractSvnKeywordValue(s):
    """Extracts the value string from an SVN keyword property string."""
    if re.match(r'^\$[^:]*\$$', s):
        return ""
    return re.sub(r'^\$[^:]*: (.*)\$$', r'\1', s).strip(' ')


def _send(options):
    """send packets"""

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Open data source file
    if options.file == "":
        inputFile = sys.stdin
    else:
        inputFile = open(options.file, "rb")
    
    packetTotal = 0
    packetDelay = float(options.delay) / 1000.0
    while True:
        buf = inputFile.read(options.size)
        if len(buf) == 0:
            break
        
        s.sendto(buf, (options.dest, options.port))
        packetTotal += 1
        time.sleep(packetDelay)
    
    s.close()
    inputFile.close()
    print "%s packets sent to %s:%s" % (packetTotal, options.dest, options.port)



# Interactive Runs
if __name__ == '__main__':

    # Get name of program from command line or else use embedded default
    progName = os.path.basename(sys.argv[0])

    # Create other program tags from SVN strings
    progDate = _extractSvnKeywordValue(__date__)
    progVersion = _get_progVersion()
    
    #
    # Setup option parsing
    #
    usageMsg = "usage: %s {requiredOptions} [otherOptions]" % (progName)
    versionMsg = "%s version %s (%s)" % (progName, progVersion, progDate)
    descriptionMsg = __progTitle__ + """ is a data receiver."""
    epilogMsg = """"""
    optParser = optparse.OptionParser(usage=usageMsg, 
                                      version=versionMsg,
                                      description=descriptionMsg,
                                      epilog=epilogMsg)

    # add options outside of any option group
    optParser.add_option("--verbose", "-v", action="store_true", help="Verbose reporting on STDERR")
    optParser.add_option("--file","-f", action="store", default="", type="str", metavar="FILE", help="input file (default=STDIN)")

    # optional options
    group = optparse.OptionGroup(optParser,"Optional")
    group.add_option("--dest","-d", action="store", default=DEF_SEND_ADDR, type="str", metavar="IP", help="destination IP (default=%default)")
    group.add_option("--port","-p", action="store", default=DEF_SEND_PORT, type="int", metavar="NUM", help="destination port (default=%default)")
    group.add_option("--size","-s", action="store", default=DEF_SEND_SIZE, type="int", metavar="BYTES", help="packet size (default=%default)")
    group.add_option("--delay", action="store", default=DEF_SEND_INTERVAL_MS, type="int", metavar="MSEC", help="time between packets (default=%default)")
    optParser.add_option_group(group)

    # do the option parsing
    (options, args) = optParser.parse_args(args=sys.argv[1:])

    # check options
    if not _options_okay(options):
        print_error("Stopping due to option errors.")
        sys.exit(EXIT_CODE['OPTIONS'])

    _send(options)
