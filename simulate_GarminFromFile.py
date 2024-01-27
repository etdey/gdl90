#!/usr/bin/env python
#
# simulate_GarminFromFile.py
#


import time
from datetime import datetime
import socket
import gdl90.encoder
import math
import os
import sys
import optparse
import csv

__progTitle__ = "GDL-90 Sender"

__author__ = "Jochen Koehler"
__created__ = "Januar 2024"
__copyright__ = "Copyright (c) 2025 by Jochen Koehler"

__date__ = "$Date$"
__version__ = "0.1"
__revision__ = "$Revision$"
__lastChangedBy__ = "$LastChangedBy$"

# Default values for options
DEF_SEND_ADDR="255.255.255.255"
#DEF_SEND_ADDR="10.1.1.255"
DEF_SEND_PORT=43211

# These are the identifiers in a Garmin CSV file
id_date = 'Lcl Date'
id_time = 'Lcl Time'
id_latitude = 'Latitude'
id_longitude = 'Longitude'
id_altitude = 'AltMSL'
id_heading = 'HDG'
id_groundspeed = 'GndSpd'
id_verticalspeed = 'VSpd'

# Date-Format
datetime_format = '%Y-%m-%d %H:%M:%S'

# Exit codes
EXIT_CODE = {
    "OK" : 0,
    "OPTIONS" : 1,
    "OTHER" : 99,
}

def print_error(msg):
    """print an error message"""
    print(sys.stderr, msg)

def _options_okay(options):
    """test to see if options are valid"""
    errors = False
    
    if not (options.file == "" or os.path.exists(options.file)):
        errors = True
        print_error("Agument '--file' points to non-existent file")
    
    return not errors

if __name__ == '__main__':

    # Get name of program from command line or else use embedded default
    progName = os.path.basename(sys.argv[0])  

    # Setup option parsing
    #
    usageMsg = "usage: %s [options]" % (progName)
    optParser = optparse.OptionParser(usage=usageMsg)

    # add options outside of any option group
    optParser.add_option("--verbose", "-v", action="store_true", help="Verbose reporting on STDERR")
    optParser.add_option("--file","-f", action="store", default="example.csv", type="str", metavar="FILE", help="input file (default=STDIN)")
    optParser.add_option("--callsign","-c", action="store", default="DEUKN", type="str", metavar="CALLSIGN", help="Aeroplane Callsign (default=DEUKN)")

    # optional options
    group = optparse.OptionGroup(optParser,"Optional")
    group.add_option("--speedfactor","-s", action="store", default="5.0", type="float", metavar="SPEEDFACTOR", help="time lapse factor (default=5.0)")
    group.add_option("--dest","-d", action="store", default=DEF_SEND_ADDR, type="str", metavar="IP", help="destination IP (default=%default)")
    group.add_option("--port","-p", action="store", default=DEF_SEND_PORT, type="int", metavar="NUM", help="destination port (default=%default)")
    optParser.add_option_group(group)

    # do the option parsing
    (options, args) = optParser.parse_args(args=sys.argv[1:])

    # check options
    if not _options_okay(options):
        print_error("Stopping due to option errors.")
        sys.exit(EXIT_CODE['OPTIONS'])

    print("Simulating Skyradar from Garmin CSV File")
    print("Transmitting to %s:%s" % (options.dest, options.port))

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    packetTotal = 0
    encoder = gdl90.encoder.Encoder()
        
    csv_file = open(options.file)
    reader = csv.DictReader(csv_file, skipinitialspace=True)
    
    callSign = options.callsign     
    for row in reader:
        timeStart = time.time()  # mark start time of message burst
        currdatetime_str = row[id_date] + ' ' + row[id_time]
        currdatetime = datetime.strptime(currdatetime_str, datetime_format)
        latitude = float(row[id_latitude])
        longitude = float(row[id_longitude])
        altitude = float(row[id_altitude])
        heading = float(row[id_heading])
        groundspeed = float(row[id_groundspeed])
        verticalspeed = float(row[id_verticalspeed])

        # Heartbeat Message
        buf = encoder.msgHeartbeat(ts = currdatetime)
        s.sendto(buf, (options.dest, options.port))
        packetTotal += 1
        
        # Ownership Report
        buf = encoder.msgOwnershipReport(latitude=latitude, longitude=longitude, altitude=altitude, hVelocity=groundspeed, vVelocity=verticalspeed, trackHeading=heading, callSign=callSign)
        s.sendto(buf, (options.dest, options.port))
        packetTotal += 1
        
        # Ownership Geometric Altitude
        buf = encoder.msgOwnershipGeometricAltitude(altitude=altitude)
        s.sendto(buf, (options.dest, options.port))
        packetTotal += 1
        
        # GPS Time, Custom 101 Message
        buf = encoder.msgGpsTime(count=packetTotal)
        s.sendto(buf, (options.dest, options.port))
        packetTotal += 1
        
        # On-screen status output 
        if (currdatetime.second % 10 == 0):
            print("Uptime %s, lat=%3.6f, long=%3.6f, altitude=%d, heading=%d" % (currdatetime.strftime('%H:%M:%S'), latitude, longitude, altitude, heading))
            
        # Delay for the rest of this second
        # Delay to 100ms for each step - so video can be slowed down by given factor
        time.sleep(max(0.0, 1.0/options.speedfactor - (time.time() - timeStart)))
