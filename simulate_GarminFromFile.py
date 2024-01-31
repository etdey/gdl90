#!/usr/bin/env python
#
# simulate_GarminFromFile.py
#


import time
from datetime import datetime, timezone
import socket
import gdl90.encoder
import os
import sys
import optparse
import csv
import msvcrt
#import winsound

__progTitle__ = "GDL-90 Sender"

__author__ = "Jochen Koehler"
__created__ = "Januar 2024"
__copyright__ = "Copyright (c) 2025 by Jochen Koehler"

__date__ = "$Date$"
__version__ = "0.1"
__revision__ = "$Revision$"
__lastChangedBy__ = "$LastChangedBy$"

#################
# We have some ambiguities due to non-smooth input data. Possible improvement by calculating a gliding average value - 
# but this ends up in more complex code ...

# Default values for options
DEF_SEND_ADDR="255.255.255.255"
DEF_SEND_PORT=43211
# DEF_SEND_PORT=4000

# These are the identifiers in a Garmin CSV file
id_date = 'Lcl Date'
id_UTCOffset = 'UTCOfst'
id_time = 'Lcl Time'
id_latitude = 'Latitude'
id_longitude = 'Longitude'
id_altitudeMSL = 'AltMSL'
id_altitudeGPS = 'AltGPS'
id_heading = 'HDG'
id_track = 'TRK'
id_groundspeed = 'GndSpd'
id_airspeed = 'IAS'
id_trueairspeed = 'TAS'
id_verticalspeed = 'VSpdG'
id_windspeed = 'WndSpd'

# Date-Format
datetime_format = '%Y-%m-%d %H:%M:%S %z'

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

def decomment(csvfile):
    for row in csvfile:
        raw = row.split('#')[0].strip()
        if raw: yield raw
        
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
    group.add_option("--lapsefactor","-l", action="store", default="2.0", type="float", metavar="LAPSEFACTOR", help="time lapse factor (default=5.0)")
    group.add_option("--timeofstart","-s", action="store", default="0.0", type="float", metavar="TIMEOFSTART", help="relative time to start [s] (default=0.0)")
    group.add_option("--takeoff_altitude","-a", action="store", default="-1000", type="float", metavar="TAKEOFFALT", help="Correct take off altitude [ft]) (default=-1000)")
    group.add_option("--landing_altitude","-t", action="store", default="-1000", type="float", metavar="LANDINGALT", help="Correct landing altitude [ft]) (default=-1000)")
    group.add_option("--duration","-u", action="store", default="1e9", type="float", metavar="TIMEOFDURATION", help="duration of video [s] ]in realtime) (default=1e9)")
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
    FirstIt = True
    encoder = gdl90.encoder.Encoder()
        
    csv_file = open(options.file)
    reader = csv.DictReader(decomment(csv_file), skipinitialspace=True)
    callSign = options.callsign   
    # First run to detect take-off and landing
    OffsetLandingAltitude = 0
    OffsetTakeOffAltitude = 0
    gradOffsetAltitude = 0
    TakeOffDetectedForOffset = False

    for row in reader:
        windspeed = row[id_windspeed]
        currdatetime_str = row[id_date] + ' ' + row[id_time] + ' ' + row[id_UTCOffset].replace(":", "")
        currdatetime = datetime.strptime(currdatetime_str, datetime_format)
        if windspeed == '':
            if not TakeOffDetectedForOffset: 
                continue
            if TakeOffDetectedForOffset:
                LandingTime = currdatetime
                if options.takeoff_altitude > -1000.0 and options.landing_altitude > - 1000.0:
                    OffsetLandingAltitude = options.landing_altitude - float(row[id_altitudeGPS])
                    gradOffsetAltitude = (OffsetLandingAltitude - OffsetTakeOffAltitude) / (LandingTime - TakeOffTime).total_seconds()
                print("Landing at %s with altitude offset: %d" % (LandingTime.strftime('%H:%M:%S'), OffsetLandingAltitude))
                break
        else:
            if not TakeOffDetectedForOffset:
                if options.takeoff_altitude > -1000.0 and options.landing_altitude > - 1000.0:
                    OffsetTakeOffAltitude = options.takeoff_altitude - float(row[id_altitudeGPS])
                TakeOffTime = currdatetime
                print("Takeoff at %s with altitude offset: %d" % (TakeOffTime.strftime('%H:%M:%S'), OffsetTakeOffAltitude))
                TakeOffDetectedForOffset = True

    csv_file.seek(0)
    reader = csv.DictReader(decomment(csv_file), skipinitialspace=True)       
    for row in reader:
        try:
            timeStart = time.time()  # mark start time of message burst
            currdatetime_str = row[id_date] + ' ' + row[id_time] + ' ' + row[id_UTCOffset].replace(":", "")
            currdatetime = datetime.strptime(currdatetime_str, datetime_format)
            timeSim = currdatetime.second + currdatetime.minute *60 + currdatetime.hour *3600
            # Altitude correction
            if TakeOffDetectedForOffset:
                OffsetAltitude = OffsetTakeOffAltitude + gradOffsetAltitude * max(0.0, (min(currdatetime, LandingTime) - TakeOffTime).total_seconds())
            else:
                OffsetAltitude = 0
            if FirstIt:
                time0 = timeSim
                FirstIt = False
            if timeSim - time0 < options.timeofstart: # did we pass start time already?
                continue
            elif timeSim - options.timeofstart > options.duration: # is duration over already? 
                break
            altitudeMSL = float(row[id_altitudeMSL]) + OffsetAltitude
            altitudeGPS = float(row[id_altitudeGPS])
            groundspeed = float(row[id_groundspeed])
            verticalspeed = float(row[id_verticalspeed])
            latitude = float(row[id_latitude])
            longitude = float(row[id_longitude])
            heading = float(row[id_heading])
            track = float(row[id_track])
            airspeed = float(row[id_airspeed])
            trueairspeed = float(row[id_trueairspeed])
        except Exception as e:
            print(e)
            break
        # Heartbeat Message
        buf = encoder.msgHeartbeat(ts = currdatetime.astimezone(timezone.utc))
        s.sendto(buf, (options.dest, options.port))
        packetTotal += 1
        
        # Ownership Report
        buf = encoder.msgOwnershipReport(latitude=latitude, longitude=longitude, altitude=altitudeGPS, hVelocity=groundspeed, vVelocity=verticalspeed, trackHeading=track, misc=9, callSign=callSign)
        s.sendto(buf, (options.dest, options.port))
        packetTotal += 1
        
        # Ownership Geometric Altitude
        buf = encoder.msgOwnershipGeometricAltitude(altitude=altitudeGPS)
        s.sendto(buf, (options.dest, options.port))
        packetTotal += 1
        
        # GPS Time, Custom 101 Message
        buf = encoder.msgGpsTime(count=packetTotal, quality=1, hour=currdatetime.hour, minute=currdatetime.minute)
        s.sendto(buf, (options.dest, options.port))
        packetTotal += 1
        
        # On-screen status output 
        if (currdatetime.second % 10 == 0):
            print("Real Time %s, lat=%3.6f, long=%3.6f, altitudeMSL=%d, heading=%d, groundspeed=%d, airspeed=%d" % (currdatetime.strftime('%H:%M:%S'), latitude, longitude, altitudeMSL, heading, groundspeed, airspeed))
            
        # Delay for the rest of this second
        # Delay to 100ms for each step - so video can be slowed down by given factor
        time.sleep(max(0.0, 1.0/options.lapsefactor - (time.time() - timeStart)))
        if msvcrt.kbhit():
            mych = msvcrt.getch()
            if msvcrt.getch() == b' ':
                # Pause
                while True:
                    if msvcrt.kbhit():  
                        break
    print('Sent lines of csv-file: %d' % (reader.line_num))    
    csv_file.close()
    freq=3000
    dur=1000
#    winsound.Beep(freq,dur)
    time.sleep(0.3)
#    winsound.Beep(freq,dur)
    time.sleep(0.3)
#    winsound.Beep(freq,dur)
