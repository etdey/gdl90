#
# decoder.py
#

import sys
import datetime
from collections import deque
import messages
from gdl90.fcs import crcCheck
from messagesuat import messageUatToObject


class Decoder(object):
    """GDL-90 data link interface decoder class"""

    def __init__(self):
        self.format = 'normal'
        self.uatOutput = False
        self.inputBuffer = bytearray()
        self.messages = deque()
        self.parserSynchronized = False
        self.stats = {
            'msgCount' : 0,
            'resync' : 0,
            'msgs' : { 0 : [0, 0] },
        }
        self.reportFrequency = 10
        
        # altitude reporting in plotflight mode
        self.altitude = 0
        self.altitudeAge = 9999
        self.altitudeMaxAge = 5
        
        # setup internal time tracking
        self.gpsTimeReceived = False
        self.dayStart = None
        self.currtime = datetime.datetime.utcnow()
        self.heartbeatInterval = datetime.timedelta(seconds=1)
    
    
    def addBytes(self, data):
        """add raw input bytes for decode processing"""
        self.inputBuffer.extend(data)
        self._parseMessages()
    
    
    def _log(self, msg):
        sys.stderr.write('decoder.Decoder:' + msg + '\n')
    
    def _parseMessages(self):
        """parse input buffer for all complete messages"""
        
        if not self.parserSynchronized:
            if not self._resynchronizeParser():
                # false if we empty the input buffer
                return
        
        while True:
            # Check that buffer has enough bytes to use
            if len(self.inputBuffer) < 2:
                #self._log("buffer reached low watermark")
                return
            
            # We expect 0x7e at the head of the buffer
            if self.inputBuffer[0] != 0x7e:
                # failed assertion; we are not synchronized anymore
                #self._log("synchronization lost")
                if not self._resynchronizeParser():
                    # false if we empty the input buffer
                    return
            
            # Look to see if we have an ending 0x7e marker yet
            try:
                i = self.inputBuffer.index(chr(0x7e), 1)
            except ValueError:
                # no end marker found yet
                #self._log("no end marker found; leaving parser for now")
                return
            
            # Extract byte message without markers and delete bytes from buffer
            msg = self.inputBuffer[1:i]
            del(self.inputBuffer[0:i+1])
            
            # Decode the received message
            self._decodeMessage(msg)
        
        return
    
    
    def _resynchronizeParser(self):
        """throw away bytes in buffer until empty or resynchronized
        Return:  true=resynchronized, false=buffer empty & not synced"""
        
        self.parserSynchronized = False
        self.stats['resync'] += 1
        
        while True:
            if len(self.inputBuffer) < 2:
                #self._log("buffer reached low watermark during sync")
                return False
            
            # found end of a message and beginning of next
            if self.inputBuffer[0] == 0x7e and self.inputBuffer[1] == 0x7e:
                # remove end marker from previous message
                del(self.inputBuffer[0:1])
                self.parserSynchronized = True
                #self._log("parser is synchronized (end:start)")
                return True
            
            if self.inputBuffer[0] == 0x7e:
                self.parserSynchronized = True
                #self._log("parser is synchronized (start)")
                return True
            
            # remove everything up to first 0x7e or end of buffer
            try:
                i = self.inputBuffer.index(chr(0x7e))
                #self._log("removing leading bytes before marker")
            except ValueError:
                # did not find 0x7e, so blank the whole buffer
                i = len(self.inputBuffer)
                #self._log("removing all bytes in buffer since no markers")
            #self._log('inputBuffer[0:%d]=' % (len(self.inputBuffer)) +str(self.inputBuffer)[:+32])
            del(self.inputBuffer[0:i])
        
        raise Exception("_resynchronizeParser: unexpected reached end")

    
    def _decodeMessage(self, escapedMessage):
        """decode one GDL90 message without the start/end markers"""
        
        rawMsg = self._unescape(escapedMessage)
        if len(rawMsg) < 5:
            return False
        msg = rawMsg[:-2]
        crc = rawMsg[-2:]
        crcValid = crcCheck(msg, crc)
        
        """
        self.stats['msgCount'] += 1
        if (self.stats['msgCount'] % self.reportFrequency) == 0:
            print "Statistics: total msgs = %d, resyncs = %d" % (self.stats['msgCount'], self.stats['resync'])
            msgTypes = self.stats['msgs'].keys()
            msgTypes.sort()
            for mt in msgTypes:
                (g, b) = self.stats['msgs'][mt]
                print "  Messge #%d: %d good, %d bad" % (mt, g, b)
        """
        
        # Create a new entry for this message type if it doesn't exist
        if not msg[0] in self.stats['msgs'].keys():
            self.stats['msgs'][msg[0]] = [0,0]
        
        if not crcValid:
            self.stats['msgs'][msg[0]][1] += 1
            #print "****BAD CRC****"
            return False
        self.stats['msgs'][msg[0]][0] += 1
        
        """
        #if msg[0] in [0, 10, 11]:
        if msg[0] in [101]:
            print "msg%d: " % (msg[0])
            for m in [msg]:
                hexstr = ""
                for n in range(len(msg)):
                    if (n % 4) == 0:  hexstr += " "
                    hexstr += "%02x" % (msg[n])
                print " " + hexstr
        """
        
        m = messages.messageToObject(msg)
        if not m:
            return False
        
        if m.MsgType == 'Heartbeat':
            self.currtime += self.heartbeatInterval
            if self.format == 'normal':
                print 'MSG00: s1=%02x, s2=%02x, ts=%02x' % (m.StatusByte1, m.StatusByte2, m.TimeStamp)
            elif self.format == 'plotflight':
                self.altitudeAge += 1
        
        elif m.MsgType == 'OwnershipReport':
            if self.format == 'normal':
                print 'MSG10: %0.7f %0.7f %d %d %d' % (m.Latitude, m.Longitude, m.HVelocity, m.Altitude, m.TrackHeading)
            elif self.format == 'plotflight':
                if self.altitudeAge < self.altitudeMaxAge:
                    altitude = self.altitude
                else:
                    # revert to 25' resolution altitude from ownership report
                    altitude = m.Altitude
                
                # Must have the GPS time from a message 101 before outputting anything
                if not self.gpsTimeReceived:
                    return True
                print '%02d:%02d:%02d %0.7f %0.7f %d %d %d' % (self.currtime.hour, self.currtime.minute, self.currtime.second, m.Latitude, m.Longitude, m.HVelocity, altitude, m.TrackHeading)
        
        elif m.MsgType == 'OwnershipGeometricAltitude':
            if self.format == 'normal':
                print 'MSG11: %d %04xh' % (m.Altitude, m.VerticalMetrics)
            elif self.format == 'plotflight':
                self.altitude = m.Altitude
                self.altitudeAge = 0
        
        elif m.MsgType == 'TrafficReport':
            if self.format == 'normal':
                print 'MSG20: %0.7f %0.7f %dkt %dfpm %dft %02ddeg' % (m.Latitude, m.Longitude, m.HVelocity, m.VVelocity, m.Altitude, m.TrackHeading)
        
        elif m.MsgType == 'GpsTime':
            if not self.gpsTimeReceived:
                self.gpsTimeReceived = True
                utcTime = datetime.time(m.Hour, m.Minute, 0)
                self.currtime = datetime.datetime.combine(self.dayStart, utcTime)
            else:
                # correct time slips and move clock forward if necessary
                if self.currtime.hour < m.Hour or self.currtime.minute < m.Minute:
                    utcTime = datetime.time(m.Hour, m.Minute, 0)
                    self.currtime = datetime.datetime.combine(self.currtime, utcTime)
            
            if self.format == 'normal':
                print 'MSG101: %02d:%02d UTC (waas = %s)' % (m.Hour, m.Minute, m.Waas)
        
        elif m.MsgType == 'UplinkData' and self.uatOutput == True:
            messageUatToObject(m)
        
        return True
    
    
    def _unescape(self, msg):
        """unescape 0x7e and 0x7d characters in coded message"""
        msgNew = bytearray()
        escapeValue = 0x7d
        foundEscapeChar = False
        while True:
            try:
                i = msg.index(chr(escapeValue))
                foundEscapeChar = True
                msgNew.extend(msg[0:i]); # everything up to the escape character
                
                # this will throw an exception if nothing follows the escape
                escapedValue = msg[i+1] ^ 0x20
                msgNew.append(chr(escapedValue)); # escaped value
                del(msg[0:i+2]); # remove prefix bytes, escape, and escaped value
                
            except (ValueError, IndexError):
                # no more escape characters
                if foundEscapeChar:
                    msgNew.extend(msg)
                    return msgNew
                else:
                    return msg
        
        raise Exception("_unescape: unexpected reached end")
    
    
    def _messageHex(self, msg, prefix="", suffix="", maxbytes=32, breakint=4):
        """prints the hex contents of a message"""
        s = ""
        numbytes=len(msg)
        if numbytes > maxbytes:  numbytes=maxbytes
        for i in range(numbytes):
            s += "%02x" % (msg[i])
            if ((i+1) % breakint) == 0:
                s += " "
        return "%s%s%s" % (prefix, s.strip(), suffix)
    
