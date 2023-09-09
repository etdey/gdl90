#!/usr/bin/env python
#
# test_decoder.py
#

import messages

def test_msg_0():
    print("Message type 0:")
    data = bytearray([0x00, 0x81, 0x00, 0xf0, 0xba, 0x01, 00])
    msg = messages.messageToObject(data)
    print(msg)
    print()


def test_msg_20():
    print("Message type 20:")
    data = bytearray([0x14, 0x00, 0xab, 0x45, 0x49, 0x1f, 0xef, 0x15,
                      0xa8, 0x89, 0x78, 0x0f, 0x09, 0xa9, 0x07, 0xb0,
                      0x01, 0x20, 0x01, 0x4e, 0x38, 0x32, 0x35, 0x56,
                      0x20, 0x20, 0x20, 0x00])
    msg = messages.messageToObject(data)
    print(msg)
    print()
    

if __name__ == '__main__':
    test_msg_0()
    test_msg_20()
