# USB Communication with Python and PyUSB

Say we have a robot, with a USB connection, and command documentation.
The only thing missing is knowing how to send a command over USB.
Let's learn the basic concepts needed for that.


![Kralicek catching Pokemon](http://i.imgur.com/hzY88OV.jpg)

### Installing the Library

We'll use the [pyusb](https://github.com/walac/pyusb) Python library.
On openSUSE we install it from the main RPM repository:

```console
sudo zypper install python-usb
```

On other systems we can use the`pip` tool:

```console
pip install --user pyusb
```

### Navigating USB Concepts

To send a command, we need an Endpoint.
To get to the endpoint we need to descend down the hierarchy of

1. Device
2. Configuration 
3. Interface
4. Alternate setting
5. Endpoint

First we import the library.

```py
#!/usr/bin/env python2

import usb.core
```

The device is identified with a vendor:product pair included in `lsusb` output.

> `Bus 002 Device 043: ID 0694:0005 Lego Group`

```py
VENDOR_LEGO = 0x0694
PRODUCT_EV3 = 5
device = usb.core.find(idVendor=VENDOR_LEGO, idProduct=PRODUCT_EV3)
```

A Device may have multiple Configurations, and only one can be active at
a time. Most devices have only one. Supporting multiple Configurations
is reportedly useful for offering more/less features when more/less
power is available. EV3 has only one configuration.

```py
configuration = device.get_active_configuration()
```

A physical Device may have multiple Interfaces active at a time.
A typical example is a scanner-printer combo. An Interface may have multiple
Alternate Settings. They are kind of like Configurations, but easier to
switch.
I don't quite understand this, but they say that if you need Isochronous
Endpoints (read: audio or video), you must go to a non-primary
Alternate Setting. Anyway, EV3 has only one Interface with one Setting.

```py
INTERFACE_EV3 = 0
SETTING_EV3 = 0
interface = configuration[(INTERFACE_EV3, SETTING_EV3)]
```

An Interface will typically have multiple Endpoints. The Endpoint 0 is
reserved for control functions by the USB standard so we need to use Endpoint
1 here.

The standard distinguishes between input and output endpoints, as well as four
transfer types, differing in latency and reliability. The nice thing is that
the Python library nicely allows to abstract all that away (unlike cough Ruby
cough) and we simply say to `write` to a non-control Endpoint.


```py
ENDPOINT_EV3 = 1
endpoint = interface[ENDPOINT_EV3]

# make the robot beep
command = '\x0F\x00\x01\x00\x80\x00\x00\x94\x01\x81\x02\x82\xE8\x03\x82\xE8\x03'
endpoint.write(command)
```

### The Full Script

(link it)

### Other than Robots?

Robots are great fun but unfortunately they do not come bundled with every
computer. Do you know of a device that we could use for demonstration
purposes? Everyone has a USB keyboard and mouse but I guess the OS will claim
them for input and not let you play.

### What Next

- [PyUSB](https://walac.github.io/pyusb/)
- [PyUSB tutorial](https://github.com/walac/pyusb/blob/master/docs/tutorial.rst)
- [USB in a nutshell](http://www.beyondlogic.org/usbnutshell/usb1.shtml) goes
  deeper, and is aimed more at firmware developers for the devices, but still
  is much shorter than the 650 page USB 2.0 specification
- EV3 documentation at
  [Mindstorms Downloads](https://www.lego.com/en-gb/mindstorms/downloads)

