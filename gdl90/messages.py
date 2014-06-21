#
# messages.py
#

"""GDL messages; these are only the output messages"""

from collections import namedtuple

def _parseHeartbeat(msgBytes):
    """GDL90 message type 0x00"""
    assert len(msgBytes) == 7
    assert msgBytes[0] == 0x00
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


def _parseUplinkData(msgBytes):
    """GDL90 message type 0x07"""
    assert len(msgBytes) == 436
    assert msgBytes[0] == 0x07
    msg = namedtuple('UplinkData', 'MsgType TimeOfReception Header Data')
    fields = ['UplinkData']
    
    fields.append(_unsigned24(msgBytes[1:], littleEndian=True))
    fields.append(msgBytes[4:12]) ;# UAT header
    fields.append(msgBytes[12:]) ;# data
    
    return msg._make(fields)


def _parseOwnershipReport(msgBytes):
    """GDL90 message type 0x0A"""
    assert len(msgBytes) == 28
    assert msgBytes[0] == 0x0a
    msg = namedtuple('OwnershipReport', 'MsgType Status Type Address Latitude Longitude Altitude Misc NavIntegrityCat NavAccuracyCat HVelocity VVelocity TrackHeading EmitterCat CallSign Code')
    return msg._make(_parseMessageType10and20('OwnershipReport', msgBytes))


def _parseOwnershipGeometricAltitude(msgBytes):
    """GDL90 message type 0x0B"""
    assert len(msgBytes) == 5
    assert msgBytes[0] == 0x0b
    msg = namedtuple('OwnershipGeometricAltitude', 'MsgType Altitude VerticalMetrics')
    fields = ['OwnershipGeometricAltitude']
    
    fields.append(_signed16(msgBytes[1:]) * 5) ;# height in 5 ft increments
    fields.append((msgBytes[3] << 8) + msgBytes[4])
    
    return msg._make(fields)


def _parseTrafficReport(msgBytes):
    """GDL90 message type 0x14"""
    assert len(msgBytes) == 28
    assert msgBytes[0] == 0x14
    msg = namedtuple('TrafficReport', 'MsgType Status Type Address Latitude Longitude Altitude Misc NavIntegrityCat NavAccuracyCat HVelocity VVelocity TrackHeading EmitterCat CallSign Code')
    return msg._make(_parseMessageType10and20('TrafficReport', msgBytes))


def _parseMessageType10and20(msgType, msgBytes):
    """parse the fields for ownership and traffic reports"""
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
    
    fields.append(_thunkByte(msgBytes[14], 0xff, 4) + _thunkByte(msgBytes[15], 0xf0, -4)) ;# horizontal velocity
    
    # 12-bit signed value of 64 fpm increments
    vertVelo = _thunkByte(msgBytes[15], 0x0f, 8) + _thunkByte(msgBytes[16])
    if vertVelo > 2047:
        vertVelo -= 4096
    fields.append(vertVelo * 64) ;# vertical velocity
    
    trackIncrement = 360.0 / 256
    fields.append(msgBytes[17] * trackIncrement) ;# track/heading
    
    fields.append(msgBytes[18]) ;# emitter category
    fields.append(str(msgBytes[19:27]).rstrip()) ;# call sign
    fields.append(_thunkByte(msgBytes[27], 0xf0, -4)) ;# code
    
    return fields


def _parseGpsTime(msgBytes):
    """GDL90 message type 0x65"""
    assert len(msgBytes) == 12
    assert msgBytes[0] == 0x65
    msg = namedtuple('GpsTime', 'MsgType Hour Minute Waas')
    fields = ['GpsTime']
    
    fields.append(msgBytes[7]) # UTC hour
    fields.append(msgBytes[8]) # UTC minute

    waas = None
    if msgBytes[3] == ord('1'):
        waas = False
    elif msgBytes[3] == ord('2'):
        waas = True
    fields.append(waas)
    
    return msg._make(fields)


def _unsigned24(data, littleEndian=False):
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


def _signed24(data, littleEndian=False):
    """return a 24-bit signed integer with selectable Endian"""
    val = _unsigned24(data, littleEndian)
    if val > 8388607:
        val -= 16777216
    return val


def _unsigned16(data, littleEndian=False):
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


def _signed16(data, littleEndian=False):
    """return a 16-bit signed integer with selectable Endian"""
    val = _unsigned16(data, littleEndian)
    if val > 32767:
        val -= 65536
    return val


def _thunkByte(c, mask=0xff, shift=0):
    """extract an integer from a byte applying a mask and a bit shift
    @c character byte
    @mask the AND mask to get the desired bits
    @shift negative to shift right, positive to shift left, zero for no shift
    """
    val = c & mask
    if shift < 0:
        val = val >> abs(shift)
    elif shift > 0:
        val = val << shift
    return val


MessageIDMapping = {
    0x00 : _parseHeartbeat,
    0x07 : _parseUplinkData,
    0x0a : _parseOwnershipReport,
    0x0b : _parseOwnershipGeometricAltitude,
    0x14 : _parseTrafficReport,
    0x65 : _parseGpsTime,
}


def messageToObject(data):
    """convert a raw message into an object"""
    if not len(data) > 0:
        return None
    msgId = data[0]
    if not msgId in MessageIDMapping.keys():
        return None
    msgObj = MessageIDMapping[msgId](data)
    return msgObj