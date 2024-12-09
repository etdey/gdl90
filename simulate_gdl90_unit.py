#!/usr/bin/env python3
#
#
"""GDL 90 UAT Simulator

This program implements a GDL 90 UAT output stream with a selectable
device personality.

Copyright (c) 2018-2024 by Eric Dey. All rights reserved.
"""

import argparse, logging, math, socket, sys, time, random
from collections import namedtuple
import gdl90.encoder
from iputils.iputils import Interfaces


# Default values for options
DEF_LOG_LEVEL = logging.INFO
DEF_UNIT_NAME = "stratux"

DEF_CENTER_LAT =  30.4564472222222
DEF_CENTER_LON = -98.2941888888889
DEF_PATH_RADIUS = 0.25   # degrees

DEF_CALLSIGN = "N12345"
DEF_START_ANGLE = 0.0
DEF_ANGULAR_VELOCITY = 0.667

DEF_ALTITUDE_MEAN = 3500
DEF_ALTITUDE_DELTA = 1500
DEF_ALTTIUDE_DIV = 30.0

DEF_NUM_BANDITS = 12
DEF_BANDIT_PREFIX = "BNDT"
DEF_BANDIT_ANGULAR_VELOCITY = -0.333
DEF_BANDIT_ALTITUDE = 4000
DEF_BANDIT_ALTITUDE_DELTA = 2000


# Unit defaults by manufacturer
UAT_UNIT = {
    "skyradar" : {
        "name" : "Skyradar",
        "client_port" : 43211,
    },

    "stratux" : {
        "name" : "Stratux",
        "client_port" : 4000,
    },
}


LATLONG_TO_RADIANS = math.pi / 180.0
RADIANS_TO_NM = 180.0 * 60.0 / math.pi

# Network interface singleton
NetIfaces = Interfaces()


def distance(lat0:float, lon0:float, lat1:float, lon1:float) -> float:
    """compute distance in nm between two points"""
    lat0 *= LATLONG_TO_RADIANS
    lat1 *= LATLONG_TO_RADIANS
    lon0 *= -LATLONG_TO_RADIANS
    lon1 *= -LATLONG_TO_RADIANS
    radians = math.acos(math.sin(lat0)*math.sin(lat1)+math.cos(lat0)*math.cos(lat1)*math.cos(lon0-lon1))
    return(radians*RADIANS_TO_NM)


def distance_short(lat0:float, lon0:float, lat1:float, lon1:float) -> float:
    """compute distance in nm between two points that are close to each other"""
    lat0 *= LATLONG_TO_RADIANS
    lat1 *= LATLONG_TO_RADIANS
    lon0 *= -LATLONG_TO_RADIANS
    lon1 *= -LATLONG_TO_RADIANS
    radians = 2.0*math.asin(math.sqrt((math.sin((lat0-lat1)/2.0))**2 + math.cos(lat0)*math.cos(lat1)*(math.sin((lon0-lon1)/2.0))**2))
    return(radians*RADIANS_TO_NM)


def horizontal_speed(distance:float, seconds:float) -> int:
    """compute integer speed in knots for a distance traveled in some number of seconds"""
    return(int(3600.0 * distance / seconds))



def main(argv=None) -> int:
    
    uat_unit_types = UAT_UNIT.keys()

    # get default network interface device
    try:
        def_interface = NetIfaces.ipv4_all_interfaces()[0]
    except IndexError:
        def_interface = NetIfaces.ipv4_all_interfaces(include_loopback=True)[0]  # loopback device

    argParser = argparse.ArgumentParser(description=__doc__, epilog="")

    # optional arguments
    argParser.add_argument('-v', '--verbose', action='store_true', help="verbose reporting")
    argParser.add_argument('--unit', choices=uat_unit_types, default=DEF_UNIT_NAME, help="UAT unit type (default: '%(default)s')")
    argParser.add_argument("--interface", metavar='NAME', type=str, default=def_interface, help='receive interface name (default: %(default)s')
    argParser.add_argument('--subnetbcast', action='store_true', default=False, help='broadcast to subnet instead of specific hosts')
    argParser.add_argument('--angle', metavar='DEG', type=float, default=DEF_START_ANGLE, help="simulation start angle (default: '%(default)s')")
    argParser.add_argument('--latitude', metavar='D.DD', type=float, default=DEF_CENTER_LAT, help="center latitude (default: '%(default)s')")
    argParser.add_argument('--longitude', metavar='D.DD', type=float, default=DEF_CENTER_LON, help="center longitude (default: '%(default)s')")
    argParser.add_argument('--radius', metavar='D.DD', type=float, default=DEF_PATH_RADIUS, help="path radius in degrees (default: '%(default)s')")
    argParser.add_argument('--altitude', metavar='D', type=int, default=DEF_ALTITUDE_MEAN, help="mean altitude (default: '%(default)s')")
    argParser.add_argument('--altitudeDelta', metavar='D', type=int, default=DEF_ALTITUDE_DELTA, help="altitude delta (default: '%(default)s')")
    argParser.add_argument('--port', metavar='INT', type=int, default=None, help="client network port '%(default)s')")
    argParser.add_argument('--callsign', metavar='STR', default=DEF_CALLSIGN, help="UAT unit type (default: '%(default)s')")
    argParser.add_argument('--bandits', metavar='NUM', type=int, default=DEF_NUM_BANDITS, help="number of bandits (default: '%(default)s')")
    
    # positional arguments
    argParser.add_argument('clients', metavar='HOST', nargs='*', help="network client(s) to whom to send data")

    args = argParser.parse_args(argv[1:])

    # setup logging
    logLevel = DEF_LOG_LEVEL
    if args.verbose is True:
        logLevel = logging.DEBUG
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logLevel)

    # error checking for arguments
    if args.port is None:
        args.port = UAT_UNIT[args.unit]["client_port"]
    if args.port < 1 or args.port > 65535:
        logging.error("'port' must be in the range 1 to 65535")
        sys.exit(1)

    # network transmission target(s)
    if args.clients is None:
        args.clients = []
    if args.subnetbcast == True:
        iface = NetIfaces.ipv4_details_by_name(args.interface)
        if iface is not None:
            args.clients.append(iface.broadcast)
    if len(args.clients) == 0:
        logging.error("must specify at least one HOST or use --subnetbcast")
        sys.exit(1)

    # transmission socket
    sockOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockOut.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sockOut.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # add common objects to options
    args.socket = sockOut
    args.unitName = UAT_UNIT[args.unit]["name"]

    return(run_simulation(args))


def run_simulation(args):

    print("Simulating %s UAT." % (args.unitName))
    print("Transmitting to:")
    for client in args.clients:
        print("    %s:%s" % (client, args.port))
    
    packetTotal = 0
    encoder = gdl90.encoder.Encoder()
    
    latCenter = args.latitude
    longCenter = args.longitude
    pathRadius = args.radius
    altMean = args.altitude
    altDelta = args.altitudeDelta
    simtime = 0.0
    uptime = 0

    aircraftTuple = namedtuple('Aircraft', 'type callsign address latitude longitude altitude hvelocity vvelocity heading angle0 avelocity emitCat')
    
    # ADS-B towers:
    towers = [
        (29.888890, -97.865556, 'HYI01'),
        (30.463333, -99.736390, 'TX009'),
        (31.203056, -97.051111, 'TX021'),
        (30.586667, -97.682222, 'TX024'),
        (31.598056, -100.160000, 'TX028'),
    ]

    aircraft = []

    # own ship
    (lat, lon, hvelo, vvelo, alt, hdg) = calculate_position(simtime,args.angle,DEF_ANGULAR_VELOCITY,latCenter,longCenter,pathRadius,altMean,altDelta)
    emitCat = 1
    ownship = aircraftTuple._make([
        'Ownship', args.callsign, random.randrange(2**24), 
        lat, lon, alt, hvelo, vvelo, hdg, args.angle, DEF_ANGULAR_VELOCITY, emitCat
    ])
    aircraft.append(ownship)

    banditAngleStart = args.angle + 45      # starting offset from ownship
    banditAngleDelta = 360 / args.bandits   # angle between bandits
    banditAltitudeMin = DEF_BANDIT_ALTITUDE - int(DEF_BANDIT_ALTITUDE_DELTA / 2)
    banditAltitudeMax = DEF_BANDIT_ALTITUDE + int(DEF_BANDIT_ALTITUDE_DELTA / 2)
    for n in range(args.bandits):
        angle = banditAngleStart + (banditAngleDelta * n)
        (lat, lon, hvelo, vvelo, alt, hdg) = calculate_position(simtime,angle,DEF_BANDIT_ANGULAR_VELOCITY,latCenter,longCenter,pathRadius,0,0)
        alt = random.randint(banditAltitudeMin, banditAltitudeMax)   # make altitude constant
        callsign = DEF_BANDIT_PREFIX + "%d" % (n)
        emitCat = random.randint(1, 7)  # 1=light, ..., 7=rotorcraft
        bandit = aircraftTuple._make([
            'Traffic', callsign, random.randrange(2**24),
            lat, lon, alt, hvelo, vvelo, hdg, angle, DEF_BANDIT_ANGULAR_VELOCITY, emitCat
        ])
        aircraft.append(bandit)

    while True:
        timeStart = time.time()  # mark start time of message burst
        simtime = float(uptime)
        
        # Heartbeat Message
        buf = encoder.msgHeartbeat()
        packetTotal += sendto_hosts(args.socket, args.clients, args.port, buf)

        # Stratux Heartbeat Message
        if args.unit == "stratux":
            buf = encoder.msgStratuxHeartbeat()
            packetTotal += sendto_hosts(args.socket, args.clients, args.port, buf)
        
        # Hilton Software SX Heartbeat Message
        if args.unit == "stratux":
            buf = encoder.msgSXHeartbeat(towers=towers)
            packetTotal += sendto_hosts(args.socket, args.clients, args.port, buf)

        for ac in aircraft:
            (lat, lon, hvelo, vvelo, alt, hdg) = calculate_position(simtime, ac.angle0, ac.avelocity, latCenter, longCenter, pathRadius,altMean,altDelta)
            emitCat = ac.emitCat

            if ac.type == "Ownship":
                # Ownership Report
                buf = encoder.msgOwnshipReport(latitude=lat, longitude=lon, altitude=alt, hVelocity=hvelo, vVelocity=vvelo, trackHeading=hdg, callSign=ac.callsign, emitterCat=emitCat)
                packetTotal += sendto_hosts(args.socket, args.clients, args.port, buf)
        
                # Ownership Geometric Altitude
                buf = encoder.msgOwnshipGeometricAltitude(altitude=alt, merit=10)
                packetTotal += sendto_hosts(args.socket, args.clients, args.port, buf)

                # On-screen status output
                uptime += 1
                if uptime % 10 == 0:
                    print("Uptime %d, lat=%3.6f, long=%3.6f, altitude=%d, heading=%d" % (uptime, lat, lon, alt, hdg))


            if ac.type == "Traffic" or ac.type == "Ownship":
                alt = ac.altitude   # traffic altitudes are constant
                vvelo = 0           # zero since altitude is constant
                buf = encoder.msgTrafficReport(latitude=lat, longitude=lon, altitude=alt, hVelocity=hvelo, vVelocity=vvelo, trackHeading=hdg, callSign=ac.callsign, address=ac.address, emitterCat=emitCat)
                packetTotal += sendto_hosts(args.socket, args.clients, args.port, buf)

        # GPS Time, Custom 101 Message for Skyradar
        if args.unit == "skyradar":
            buf = encoder.msgGpsTime(count=packetTotal)
            packetTotal += sendto_hosts(args.socket, args.clients, args.port, buf)
            
        # Custom 101 Message for ForeFlight
        if args.unit == "stratux":
            buf = encoder.msgForeFlightMessage101('12345678')
            packetTotal += sendto_hosts(args.socket, args.clients, args.port, buf)
        
        # Delay for the rest of this second
        time.sleep(1.0 - (time.time() - timeStart))



def calculate_position(simtime, startAngle, angularVelo, latCenter, lonCenter, pathRadius, altitudeMean, altitudeDelta):
    """calculate position, velocity, and heading
    @simtime: simulation current time (float)
    @startAngle: aircraft's starting angle (float deg)
    @angularVelo: aircraft's angular velocity (float deg)
    @latCenter: latitude of center point
    @lonCenter: longitude of center point
    @pathRadius: radius of path circle (float deg)
    @altitudeMean: mean altitude between min/max
    @altitudeDelta: distance between min/max altitudes
    Return: (lat, lon, hvelo, vvelo, altitude, heading)"""

    degrees_to_radians = lambda d: (d / 180.0) * math.pi
    calculate_latitude = lambda a: latCenter - (pathRadius * math.sin(a))
    calculate_longitude = lambda a: lonCenter + (pathRadius * math.cos(a))
    
    currAngle = (startAngle + (angularVelo * simtime)) % 360.0
    currAngleRad = degrees_to_radians(currAngle)
    nextAngle = (currAngle + angularVelo) % 360.0
    nextAngleRad = degrees_to_radians(nextAngle)

    currLat = calculate_latitude(currAngleRad)
    currLon = calculate_longitude(currAngleRad)
    nextLat = calculate_latitude(nextAngleRad)
    nextLon = calculate_longitude(nextAngleRad)

    altitudeHalfDelta = altitudeDelta / 2.0
    currAlt = int(altitudeMean + altitudeHalfDelta * math.sin(simtime / DEF_ALTTIUDE_DIV))
    nextAlt = int(altitudeMean + altitudeHalfDelta * math.sin((simtime + 1.0) / DEF_ALTTIUDE_DIV))
    vertVelo = (nextAlt - currAlt) * 60
    
    headingSign = 1.0
    headingTangent = 180.0
    if angularVelo < 0.0:  
        headingSign = -1.0
        headingTangent = 0.0
    heading = int((headingTangent + (currAngle * headingSign)) % 360.0)
    if angularVelo < 0.0: 
        heading = 360.0 - heading
        
    distanceMoved = distance_short(currLat, currLon, nextLat, nextLon)
    horzVelo = horizontal_speed(distanceMoved, 1.0)

    return([currLat, currLon, horzVelo, vertVelo, currAlt, heading])


def sendto_hosts(sock, destHosts, destPort, buf):
    """send buffer to a list of hosts
    @sock: UDP socket from which to transmit
    @destHosts: list of destination hosts
    @destPort: destination port
    @buf: data buffer to send
    Return: number of packets transmitted"""
    for destHost in destHosts:
        sock.sendto(buf, (destHost, destPort))
    return(len(destHosts))



if __name__ == "__main__":
    sys.exit(main(sys.argv))
