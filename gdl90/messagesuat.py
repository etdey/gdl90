#
# messagesuat.py  -- UAT message decoder
#

"""UAT Message Decoder functions"""

from collections import namedtuple
from pprint import pprint

CHAR_ETX = chr(3)
CHAR_RS = chr(30)
CHAR_NULL = chr(0)
CHAR_TAB = chr(9)
CHAR_CR = chr(13)
CHAR_LF = chr(10)
DLAC2StrTable = [
    CHAR_ETX,  # 0  End-of-Text
    'A',  # 1
    'B',  # 2
    'C',  # 3
    'D',  # 4
    'E',  # 5
    'F',  # 6
    'G',  # 7
    'H',  # 8
    'I',  # 9
    'J',  # 10
    'K',  # 11
    'L',  # 12
    'M',  # 13
    'N',  # 14
    'O',  # 15
    'P',  # 16
    'Q',  # 17
    'R',  # 18
    'S',  # 19
    'T',  # 20
    'U',  # 21
    'V',  # 22
    'W',  # 23
    'X',  # 24
    'Y',  # 25
    'Z',  # 26
    CHAR_NULL,  # 27  Null
    '....',  # 28  Tab
    CHAR_RS,  # 29  Record Separator
    '%s%s' % (CHAR_CR, CHAR_LF),  # 30  CR+LF
    CHAR_NULL,  # 31  Change-Cipher (treated as Null)
    ' ',  # 32
    '!',  # 33
    '"',  # 34
    '#',  # 35
    '$',  # 36
    '%',  # 37
    '&',  # 38
    "'",  # 39
    '(',  # 40
    ')',  # 41
    '*',  # 42
    '+',  # 43
    ',',  # 44
    '-',  # 45
    '.',  # 46
    '/',  # 47
    '0',  # 48
    '1',  # 49
    '2',  # 50
    '3',  # 51
    '4',  # 52
    '5',  # 53
    '6',  # 54
    '7',  # 55
    '8',  # 56
    '9',  # 57
    ':',  # 58
    ';',  # 59
    '<',  # 60
    '=',  # 61
    '>',  # 62
    '?',  # 63
]

"""
MessageUATIDMapping = {
    0x00 : _parseHeartbeat,
    0x07 : _parseUplinkData,
    0x0a : _parseOwnershipReport,
    0x0b : _parseOwnershipGeometricAltitude,
    0x14 : _parseTrafficReport,
    0x65 : _parseGpsTime,
}
"""

def _decodeUatHeader(headerBytes):
    """decode a UAT header"""
    pass


def _extractIFrames(dataBytes):
    """extract a list of I-Frame tuples
    @dataBytes  the whole UAT data field (424 bytes)
    """

    iframeList=[]
    iframe = namedtuple('IFrame', 'Type Data')
    n=0
    while n < 424:
        if n >= 452:
            # Only two bytes left & not enough for another I-Frame
            break
        if dataBytes[n] == 0x00 and dataBytes[n+1] == 0x00:
            # Assume the rest of the dataBytes are all zeros
            break
        
        # 9-bit number with LSB in the top bit of the second byte
        framelen = (dataBytes[n] << 1) + (_thunkByte(dataBytes[n+1],mask=0x7f,shift=-7))
        
        frameType = _thunkByte(dataBytes[n+1],mask=0x0f)
        n += 2
        
        #print "iframe: n=%d, framelen=%d, n+framelen=%d (<424?)" % (n, framelen, n+framelen)
        iframeList.append(iframe._make([frameType, dataBytes[n:n+framelen]]))
        n += framelen
    return(iframeList)


def _extractAPDU(iframeData):
    if len(iframeData) < 4:
        #print "  **iframe too short for ADPU Header"
        return None
    
    apdu = namedtuple('ADPU', 'ProductID Hours Minutes Data')

    productId = _thunkByte(iframeData[0], mask=0x1f, shift=6) + _thunkByte(iframeData[1], mask=0xfc, shift=-2)
    hours = _thunkByte(iframeData[2], mask=0x7c, shift=-2)
    minutes = _thunkByte(iframeData[2], mask=0x03, shift=4) + _thunkByte(iframeData[3], mask=0xf0, shift=-4)
    
    #print "Product ID %d, %02d:%02d" % (productId, hours, minutes)
    
    return(apdu._make([productId, hours, minutes, iframeData[4:]]))



def dlac2string(msgIn):
    """convert DLAC 6-bit encoded message to ASCII string"""
    msgLength = len(msgIn)
    msgOutChars = []
    n = 0  # index into input message array; only increment when no more bits to use
    m = 0  # index into output message array; increment on every loop
    while n < msgLength:
        pos = m % 4
        #print "  msgLength=%d, n=%d, m=%d, pos=%d, msgIn[n]=%02x" % (msgLength,n,m,pos,msgIn[n])
        if pos == 0:
            d = _thunkByte(msgIn[n], mask=0xfc, shift=-2)
            # don't increment n since there are two more bits to use
        elif pos == 1:
            if not (n + 1 < msgLength):
                break
            d = _thunkByte(msgIn[n], mask=0x03, shift=4) + _thunkByte(msgIn[n+1], mask=0xf0, shift=-4)
            n += 1
        elif pos == 2:
            if not (n + 1 < msgLength):
                break
            d = _thunkByte(msgIn[n], mask=0x0f, shift=2) + _thunkByte(msgIn[n+1], mask=0xc0, shift=-6)
            n += 1
        elif pos == 3:
            d = _thunkByte(msgIn[n], mask=0x3f)
            n += 1
        assert(d >= 0 and d <= 63)
        msgOutChars.append(DLAC2StrTable[d])
        m += 1
    return(b"".join(msgOutChars))

    

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


def messageUatToObject(msg):
    """decode a UAT message named tuple.
    @msg namedtuple('UplinkData', 'MsgType TimeOfReception Header Data')
    Returns decoded UAT message namedtuple('APDUMessage', 'ProductID Hours Minutes IFrames')
    IFrames is a list of namedtuple('IFrame', 'Type Data')
    """
    
    assert(msg.MsgType == 'UplinkData')
    
    apduMsg = namedtuple('APDUMessage', 'ProductID Hours Minutes IFrames')

    #print "**** UAT Message ****"

    """
    print "UAT Header: (%d bytes)" % (len(msg.Header))
    hexstr = ""
    for n in range(len(msg.Header)):
        if (n % 4) == 0:  hexstr += " "
        hexstr += "%02x" % (msg.Header[n])
    print " " + hexstr
    """
    
    """
    print "UAT Data: (%d bytes)" % (len(msg.Data))
    hexstr = ""
    for n in range(len(msg.Data)):
        if (n % 4) == 0:  hexstr += " "
        hexstr += "%02x" % (msg.Data[n])
    print " " + hexstr
    """
    
    iframeNum = 0
    iframeList = _extractIFrames(msg.Data)
    if len(iframeList) == 0:
        #print "Null I-Frame"
        return
    for iframe in iframeList:
        #print "I-Frame %d, Type %d, Length %d bytes" % (iframeNum, iframe.Type, len(iframe.Data))
        """
        print "I-Frame Data: (%d bytes)" % (len(iframe.Data))
        hexstr = ""
        for n in range(len(iframe.Data)):
            if (n % 4) == 0:  hexstr += " "
            hexstr += "%02x" % (iframe.Data[n])
        print " " + hexstr
        """
        
        apdu = _extractAPDU(iframe.Data)
        if not apdu is None:
            if apdu.ProductID in [8,11,12,13,413]:
                print("APDU%03d: [%s]" % (apdu.ProductID, dlac2string(apdu.Data)))
            else:
                pass
                #print "APDU%03d: length=%d" % (apdu.ProductID, len(iframe.Data)-4)
        
        iframeNum += 1
