
import ConfigParser
import bluetooth

class Connection:
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read('.lms-connection')

        btaddr = config.get('connection', 'bluetooth')
        if bt is not None:
            port = 1                   # the rfcomm port ev3 uses
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.connect((btaddr, port))

class Everstorm:
    def krok(self):
        print "Udelam krok"

    def hura(self):
        print "Reknu 'Hura!'"
