#!/usr/bin/env python
#
# simulate_stratux.py
#
"""Stratux Simulator

This program implements a sender of the GDL-90 data format used by Stratux.

Copyright (c) 2013 by Eric Dey; All rights reserved
"""

import time
import socket
import gdl90.encoder
import math
import os

# Default values for options
#DEF_SEND_ADDR="255.255.255.255"
DEF_SEND_ADDR="10.1.1.255"
DEF_SEND_PORT=4000

LATLONG_TO_RADIANS = math.pi / 180.0
RADIANS_TO_NM = 180.0 * 60.0 / math.pi

def distance(lat0, lon0, lat1, lon1):
    """compute distance between two points"""
    lat0 *= LATLONG_TO_RADIANS
    lat1 *= LATLONG_TO_RADIANS
    lon0 *= -LATLONG_TO_RADIANS
    lon1 *= -LATLONG_TO_RADIANS
    radians = math.acos(math.sin(lat0)*math.sin(lat1)+math.cos(lat0)*math.cos(lat1)*math.cos(lon0-lon1))
    return(radians*RADIANS_TO_NM)


def distance_short(lat0, lon0, lat1, lon1):
    """compute distance between two points that are close to each other"""
    lat0 *= LATLONG_TO_RADIANS
    lat1 *= LATLONG_TO_RADIANS
    lon0 *= -LATLONG_TO_RADIANS
    lon1 *= -LATLONG_TO_RADIANS
    radians = 2.0*math.asin(math.sqrt((math.sin((lat0-lat1)/2.0))**2 + math.cos(lat0)*math.cos(lat1)*(math.sin((lon0-lon1)/2.0))**2))
    return(radians*RADIANS_TO_NM)


def horizontal_speed(distance, seconds):
    """compute integer speed for a distance traveled in some number of seconds"""
    return(int(3600.0 * distance / seconds))


if __name__ == '__main__':

    if 'SEND_ADDR' in list(os.environ.keys()):
        destAddr = os.environ['SEND_ADDR']
    else:
        destAddr = DEF_SEND_ADDR

    destPort = int(DEF_SEND_PORT)

    print("Simulating Stratux unit.")
    print("Transmitting to %s:%s" % (destAddr, destPort))
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    packetTotal = 0
    encoder = gdl90.encoder.Encoder()
    
    callSign = 'N12345'
    latCenter = 30.456447222222224
    longCenter = -98.2941888888889
    pathRadius = 0.25  # degrees
    angle = 0.0
    altitude = 0
    heading = 0
    groundspeed = 0
    verticalspeed = 0
    
    # ADS-B towers:
    towers = [
        (29.888890, -97.865556, 'HYI01'),
        (30.463333, -99.736390, 'TX009'),
        (31.203056, -97.051111, 'TX021'),
        (30.586667, -97.682222, 'TX024'),
        (31.598056, -100.160000, 'TX028'),
    ]

    # traffic tuples: lat, long, alt, hspeed, vspeed, hdg, callSign, address
    traffic = [
        (30.60, -98.00, 3000, 100, 500, 45, 'NBNDT1', 0x000001),
        (30.60, -98.40, 2500, 120, 0, 295, 'NBNDT2', 0x000002),
        (30.18, -98.13, 3200, 150, -100, 285, 'NBNDT3', 0x000003),
        (30.13, -98.30, 2000, 110, 250, 10, 'NBNDT4', 0x000004),
    ]
    
    uptime = 0
    latitudePrev = 0.0
    longitudePrev = 0.0
    
    while True:
        
        timeStart = time.time()  # mark start time of message burst
        
        # Move ourself
        angle += 0.66666  # degrees
        while angle >= 360.0:
            angle -= 360.0
        angleRadians = (angle / 180.0) * math.pi
        latitude = latCenter - (pathRadius * math.sin(angleRadians))
        longitude = longCenter + (pathRadius * math.cos(angleRadians))
        altitude = 2500 + 1000 * math.sin(uptime / 20.0)
        heading = (180 + int(angle)) % 360
        
        distanceMoved = distance_short(latitudePrev, longitudePrev, latitude, longitude)
        groundspeed = horizontal_speed(distanceMoved, 1.0)
        latitudePrev = latitude
        longitudePrev = longitude
        
        # Heartbeat Message
        buf = encoder.msgHeartbeat()
        s.sendto(buf, (destAddr, destPort))
        packetTotal += 1

        # Stratux Heartbeat Message
        buf = encoder.msgStratuxHeartbeat()
        s.sendto(buf, (destAddr, destPort))
        packetTotal += 1
        
        # Hiltonsoftware SX Heartbeat Message
        buf = encoder.msgSXHeartbeat(towers=towers)
        s.sendto(buf, (destAddr, destPort))
        packetTotal += 1
        
        # Ownership Report
        buf = encoder.msgOwnershipReport(latitude=latitude, longitude=longitude, altitude=altitude, hVelocity=groundspeed, vVelocity=verticalspeed, trackHeading=heading, callSign=callSign)
        s.sendto(buf, (destAddr, destPort))
        packetTotal += 1
        
        # Ownership Geometric Altitude
        buf = encoder.msgOwnershipGeometricAltitude(altitude=altitude)
        s.sendto(buf, (destAddr, destPort))
        packetTotal += 1
        
        # Traffic Reports
        for t in traffic:
            (tlat, tlong, talt, tspeed, tvspeed, thdg, tcall, taddr) = t
            buf = encoder.msgTrafficReport(latitude=tlat, longitude=tlong, altitude=talt, hVelocity=tspeed, vVelocity=tvspeed, trackHeading=thdg, callSign=tcall, address=taddr)
            s.sendto(buf, (destAddr, destPort))
            packetTotal += 1
        
        # GPS Time, Custom 101 Message
        buf = encoder.msgGpsTime(count=packetTotal)
        s.sendto(buf, (destAddr, destPort))
        packetTotal += 1
        
        # On-screen status output
        uptime += 1
        if uptime % 10 == 0:
            print("Uptime %d, lat=%3.6f, long=%3.6f, altitude=%d, heading=%d, angle=%3.3f" % (uptime, latitude, longitude, altitude, heading, angle))
        
        # Delay for the rest of this second
        time.sleep(1.0 - (time.time() - timeStart))
