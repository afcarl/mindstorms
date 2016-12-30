#!/usr/bin/env python2

# adapted from
# https://github.com/karulis/pybluez/blob/master/examples/simple/rfcomm-client.py

import bluetooth

host = "00:16:53:53:EE:8C" # "KRALICEK"
port = 1                   # the rfcomm port ev3 uses
beep_command = \
    '\x0F\x00\x01\x00\x80\x00\x00\x94\x01\x81\x02\x82\xE8\x03\x82\xE8\x03'

sock = bluetooth.BluetoothSocket(RFCOMM)
sock.connect((host, port))
sock.send(beep_command)
sock.close()
