#!/usr/bin/env python
#
"""GDL-90 Recorder

This program records RAW output from the GDL-90 data link interface.

Copyright (c) 2012 by Eric Dey; All rights reserved
"""

__progTitle__ = "GDL-90 Recorder"

__author__ = "Eric Dey <eric@deys.org>"
__created__ = "September 2012"
__copyright__ = "Copyright (c) 2012 by Eric Dey"

__date__ = "$Date$"
__version__ = "0.1"
__revision__ = "$Revision$"
__lastChangedBy__ = "$LastChangedBy$"


import os, sys, time, datetime, re, optparse, socket, struct

# Default values for options
DEF_RECV_PORT=43211
DEF_RECV_MAXSIZE=1500
DEF_SYNC_AFTER_PKTS=60
DEF_LOG_PREFIX="/root/skyradar"

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


def _nextFileName(s, fmt=r'%s.%03d'):
    i = 0
    while i < 1000:
        fname = fmt % (s, i)
        if not os.path.exists(fname):
            return fname
        i += 1
    raise Exception("Search exhausted; too many files exist already.")


def _record(options):
    """record packets"""

    logFile = None
    logFileName = _nextFileName(options.logprefix)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', options.port))
    packetTotal = 0
    bytesTotal = 0
    
    try:
        while True:
            (data, dataSrc) = s.recvfrom(DEF_RECV_MAXSIZE)
            (saddr, sport) = dataSrc
            sender = "%s:%s" % (saddr, sport)
            packetTotal += 1
            bytesTotal += len(data)
            
            # Create log file only when the first bytes arrive
            if not logFile:
                logFile = open(logFileName, "wb")
            
            logFile.write(data)
            
            # Ensure periodic flush to disk
            if (packetTotal % options.syncafter) == 0:
                logFile.flush()
                os.fsync(logFile.fileno())
            
    except Exception, e:
        print e

    if logFile: logFile.close()
    s.close()
    print "Recorded %d packets and %d bytes." % (packetTotal, bytesTotal)


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

    # optional options
    group = optparse.OptionGroup(optParser,"Optional")
    group.add_option("--port","-p", action="store", default=DEF_RECV_PORT, type="int", metavar="NUM", help="receive port (default=%default)")
    group.add_option("--maxsize","-s", action="store", default=DEF_RECV_MAXSIZE, type="int", metavar="BYTES", help="maximum packet size (default=%default)")
    group.add_option("--syncafter", action="store", default=DEF_SYNC_AFTER_PKTS, type="int", metavar="NUM", help="sync every NUM packets (default=%default)")
    group.add_option("--logprefix", action="store", default=DEF_LOG_PREFIX, metavar="PATH", help="path prefix for log file names (default=%default)")
    optParser.add_option_group(group)

    # do the option parsing
    (options, args) = optParser.parse_args(args=sys.argv[1:])

    # check options
    if not _options_okay(options):
        print_error("Stopping due to option errors.")
        sys.exit(EXIT_CODE['OPTIONS'])

    _record(options)
