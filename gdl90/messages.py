#
# messages.py
#

"""GDL messages; these are only the output messages"""

from collections import namedtuple

def _parseHeartbeat(msgBytes:bytearray) -> namedtuple:
    """GDL90 message type 0"""
    assert len(msgBytes) == 7
    assert msgBytes[0] == 0
    msg = namedtuple('Heartbeat', 'MsgType StatusByte1 StatusByte2 TimeStamp MessageCounts')
    fields = ['Heartbeat']
    
    fields.append(msgBytes[1])
    statusByte2 = msgBytes[2]
    fields.append(statusByte2)
    
    timeStamp = _unsigned16(msgBytes[3:], littleEndian=True)
    if (statusByte2 & 0b10000000) != 0:
        timeStamp += (1 << 16)
    fields.append(timeStamp)
    
    uplinkCount = (msgBytes[5] & 0b11111000) >> 3
    basicLongCount = ((msgBytes[5] & 0b00000011) << 8) + msgBytes[6]
    fields.append((uplinkCount, basicLongCount))
    
    return msg._make(fields)


def _parseUplinkData(msgBytes:bytearray) -> namedtuple:
    """GDL90 message type 7"""
    assert len(msgBytes) == 436
    assert msgBytes[0] == 7
    msg = namedtuple('UplinkData', 'MsgType TimeOfReception Header Data')
    fields = ['UplinkData']
    
    fields.append(_unsigned24(msgBytes[1:4], littleEndian=True))
    fields.append(msgBytes[4:12]) ;# UAT header
    fields.append(msgBytes[12:]) ;# data
    
    return msg._make(fields)


def _parseOwnshipReport(msgBytes:bytearray) -> namedtuple:
    """GDL90 message type 10"""
    assert len(msgBytes) == 28
    assert msgBytes[0] == 10
    msg = namedtuple('OwnshipReport', 'MsgType Status Type Address Latitude Longitude Altitude Misc NavIntegrityCat NavAccuracyCat HVelocity VVelocity TrackHeading EmitterCat CallSign Code')
    return msg._make(_parseMessageType10and20('OwnshipReport', msgBytes))


def _parseOwnshipGeometricAltitude(msgBytes:bytearray) -> namedtuple:
    """GDL90 message type 11"""
    assert len(msgBytes) == 5
    assert msgBytes[0] == 11
    msg = namedtuple('OwnshipGeometricAltitude', 'MsgType Altitude VerticalMetrics')
    fields = ['OwnshipGeometricAltitude']
    
    fields.append(_signed16(msgBytes[1:]) * 5) ;# height in 5 ft increments
    fields.append((msgBytes[3] << 8) + msgBytes[4])
    
    return msg._make(fields)


def _parseTrafficReport(msgBytes:bytearray) -> namedtuple:
    """GDL90 message type 20"""
    assert len(msgBytes) == 28
    assert msgBytes[0] == 20
    msg = namedtuple('TrafficReport', 'MsgType Status Type Address Latitude Longitude Altitude Misc NavIntegrityCat NavAccuracyCat HVelocity VVelocity TrackHeading EmitterCat CallSign Code')
    return msg._make(_parseMessageType10and20('TrafficReport', msgBytes))


def _parseMessageType10and20(msgType:str, msgBytes:bytearray) -> namedtuple:
    """parse the fields for ownship and traffic reports"""
    fields = [msgType]
    
    fields.append(_thunkByte(msgBytes[1], 0x0b11110000, -4)) ;# status
    fields.append(_thunkByte(msgBytes[1], 0b00001111)) ;# type
    fields.append((msgBytes[2] << 16) + (msgBytes[3] << 8) + msgBytes[4]) ;# address
    
    latLongIncrement = 180.0 / (2**23)
    fields.append(_signed24(msgBytes[5:]) * latLongIncrement) ;# latitude
    fields.append(_signed24(msgBytes[8:]) * latLongIncrement) ;# longitude
    
    altMetric = _thunkByte(msgBytes[11], 0xff, 4) + _thunkByte(msgBytes[12], 0xf0, -4)
    fields.append((altMetric * 25) - 1000) ;# altitude in 25ft resolution
    
    fields.append(_thunkByte(msgBytes[12], 0x0f)) ;# misc
    fields.append(_thunkByte(msgBytes[13], 0xf0, -4)) ;# NIC
    fields.append(_thunkByte(msgBytes[13], 0x0f)) ;# NACp
    
    # horizontal velocity, 12-bit unsigned value in knots
    horzVelo = _thunkByte(msgBytes[14], 0xff, 4) + _thunkByte(msgBytes[15], 0xf0, -4)
    if horzVelo == 0xfff:  # no hvelocity info available
        horzVelo = 0
    fields.append(horzVelo)
    
    # vertical velocity, 12-bit signed value of 64 fpm increments
    vertVelo = _thunkByte(msgBytes[15], 0x0f, 8) + _thunkByte(msgBytes[16])
    if vertVelo == 0x800:   # no vvelocity info available
        vertVelo = 0
    elif (vertVelo >= 0x1ff and vertVelo <= 0x7ff) or (vertVelo >= 0x801 and vertVelo <= 0xe01):  # not used, invalid
        vertVelo = 0
    elif vertVelo > 2047:  # two's complement, negative values
        vertVelo -= 4096
    fields.append(vertVelo * 64) ;# vertical velocity
    
    trackIncrement = 360.0 / 256
    fields.append(msgBytes[17] * trackIncrement)  # track/heading, 0-358.6 degrees
    
    fields.append(msgBytes[18]) ;# emitter category

    # call sign; if blank, change to "-"
    callsign = str(msgBytes[19:27]).rstrip()  # call sign
    if callsign == "": callsign ="-"
    fields.append(callsign)

    fields.append(_thunkByte(msgBytes[27], 0xf0, -4))  # emergency/priority code
    
    return fields


def _parseCustomMessage101(msgBytes:bytearray) -> namedtuple:
    """Vendor specific message type 101
    Skyradar: GPS Time as a 12-byte or 21-byte message
    SkyEcho: Ownship plus GPS information as a 29-byte message
    """
    assert msgBytes[0] == 101  # should never be called unless true

    if len(msgBytes) in (12, 21):
        return _parseSkyradarGpsTime(msgBytes)
    elif len(msgBytes) == 29:
        return _parseSkyEchoOwnship(msgBytes)
    else:
        return None


def _parseSkyradarGpsTime(msgBytes:bytearray) -> namedtuple:
    """GDL90 message type 101 from Skyradar"""
    assert len(msgBytes) in (12, 21)
    assert msgBytes[0] == 101
    msg = namedtuple('GpsTime', 'MsgType Hour Minute Waas')
    fields = ['GpsTime']

    # validate UTC time elements and return None if invalid
    utcHour = msgBytes[7]
    utcMinute = msgBytes[8]
    if not (0 <= utcHour < 24) or not (0 <= utcMinute < 60):
        return None

    fields.append(utcHour)
    fields.append(utcMinute)

    # GPS fix quality: 0=no fix, 1=regular, 2=waas
    waas = None
    if msgBytes[3] == 0x31:  # '1'
        waas = False
    elif msgBytes[3] == 0x32:  # '2'
        waas = True
    fields.append(waas)
    
    return msg._make(fields)


def _parseSkyEchoOwnship(msgBytes:bytearray) -> namedtuple:
    """GDL90 message type 101 from SkyEcho2 -- placeholder"""
    return None


def _signed32(data:bytearray, littleEndian:bool=False) -> int:
    """return a 32-bit signed integer with selectable Endian"""
    val = _unsigned32(data, littleEndian)
    if val > 0x7FFFFFFF:
        val -= 0x100000000
    return val


def _unsigned32(data:bytearray, littleEndian:bool=False) -> int:
    """return a 32-bit unsigned integer with selectable Endian"""
    assert len(data) >= 4
    if littleEndian:
        b0 = data[3]
        b1 = data[2]
        b2 = data[1]
        b3 = data[0]
    else:
        b0 = data[0]
        b1 = data[1]
        b2 = data[2]
        b3 = data[3]
    val = (b0 << 24) + (b1 << 16) + (b2 << 8) + b3
    return val


def _unsigned24(data:bytearray, littleEndian:bool=False) -> int:
    """return a 24-bit unsigned integer with selectable Endian"""
    assert len(data) >= 3
    if littleEndian:
        b0 = data[2]
        b1 = data[1]
        b2 = data[0]
    else:
        b0 = data[0]
        b1 = data[1]
        b2 = data[2]
    
    val = (b0 << 16) + (b1 << 8) + b2
    return val


def _signed24(data:bytearray, littleEndian:bool=False) -> int:
    """return a 24-bit signed integer with selectable Endian"""
    val = _unsigned24(data, littleEndian)
    if val > 0x7FFFFF:
        val -= 0x1000000
    return val


def _unsigned16(data:bytearray, littleEndian:bool=False) -> int:
    """return a 16-bit unsigned integer with selectable Endian"""
    assert len(data) >= 2
    if littleEndian:
        b0 = data[1]
        b1 = data[0]
    else:
        b0 = data[0]
        b1 = data[1]
    
    val = (b0 << 8) + b1
    return val


def _signed16(data:bytearray, littleEndian:bool=False) -> int:
    """return a 16-bit signed integer with selectable Endian"""
    val = _unsigned16(data, littleEndian)
    if val > 0x7FFF:
        val -= 0x10000
    return val


def _thunkByte(byte:int, mask:int=0xff, shift:int=0) -> int:
    """extract a value from a byte by applying a mask and a bit shift

    Args:
        byte (int): The input byte to be thunked; should be in the range 0-255.
        mask (int, optional): The mask value used for bitwise AND operation
            (default is 0xff); should have the same number of bits as the input
            byte to ensure meaningful results.
        shift (int, optional): The number of bits to shift the result; can be
            positive (left shift) or negative (right shift).

    Returns:
        int: The extracted integer value. While the input value must be 8-bit,
            this result value can be greater when shifted left.

    Raises:
        ValueError: If the input byte is larger than 8-bits (greater than 255).

    Examples:
        >>> _thunkByte(0b11001100, 0b00111111, 2)
        48
        >>> _thunkByte(0b11001100, 0b00111100, -2)
        3

    """
    if ((byte & 0xFF) != byte):
        raise ValueError("input byte larger than 8-bits")
    
    val = byte & mask
    if shift < 0:
        val = val >> abs(shift)
    elif shift > 0:
        val = val << shift
    return val


MessageIDMapping = {
    0   : _parseHeartbeat,
    7   : _parseUplinkData,
    10  : _parseOwnshipReport,
    11  : _parseOwnshipGeometricAltitude,
    20  : _parseTrafficReport,
    101 : _parseCustomMessage101,
}


def messageToObject(data):
    """convert a raw message into an object"""
    if not len(data) > 0:
        return None
    msgId = data[0]
    if not msgId in list(MessageIDMapping.keys()):
        return None
    msgObj = MessageIDMapping[msgId](data)
    return msgObj
