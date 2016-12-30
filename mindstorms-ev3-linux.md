

December 27th, 2016

## Introduction

Santa brought me a Lego Mindstorms set, yay!
(It's the third generation, EV3, 31313)

How can we control the robots?

- The controller brick has a demo program.

  Go forward, rotate the tool (name?), go back.
  That gets old quick

- There is a IR controller brick (which needs the brick to have an IR sensor
  attached)

  Much better, but we have to switch channels on the IR controller if we want
  to control both the motion motors and the tool motor. Also, it can only go
  full speed forward or full speed back, no medium speed.

- A "Commander" app for Android phones/tablets and for Apple devices

  It has no drawbacks of the IR controller: talks via Bluetooth, so no
  additional sensor is needed, controls all functions, with analog control of
  motion motors.

- A "Programmer" app for phones/tablets

  (it is missing the Color sensor?!)

- An IDE. For Windows, or Mac. No Linux.  (ev3dev exists, OK, but we want to
  target the original firmware for now)


## Problem

The Commander app can only control the Gripper claw quickly. That means if we
try to grab a hard object, it may bounce and slip away. So I want to make a
controller that grips slowly.

## Plan

We will connect the brick to a linux computer with a USB cable (included in
the set), learn a bit about USB communication: how to send a command to a
specific device.

We will download the EV3 developer documentation (Communication Developer Kit,
Firmware Developer Kit)
and learn how to compose a simple command for the brick: a beep.

Hopefully we will later learn how to do more complex things.

### USB Communication

Get a computer with Python. I have openSUSE.

Install the Python USB library, pyusb: `sudo zypper install python-usb`

Run this script, (as root, to have rights to the USB device)

(include mindstorms-ev3-linux.py)


### EV3 Bytecode

How did we know what the command should be?

[Mindstorms Downloads](https://www.lego.com/en-gb/mindstorms/downloads)

- [EV3 Communication Developer Kit (PDF)][ev3-cdk]
    - Section 4: "Direct Commands"
        - Subsection 4.2.5: "Play a 1kHz tone for 1 sec"

   |Bytes |Description|
   |------|-----------|
   |      |Header     |
   |0F00  |15 bytes follow |
   |0100  |message #1      |
   |80    |a direct command without a reply |
   |0000  |no space for variables needed    |
   |      |Payload                          |
   |94    |opSOUND, [EV3 Firmware Developer Kit][ev3-fdk] section 4.10 "Sound operations" |
   |01    |argument in this byte: 1 (COMMAND: TONE)              |
   |8102  |argument in 1 next byte: 2 (VOLUME: 0-100)            |
   |82E803|argument in 2 next bytes: 1000 (FREQUENCY: 250-10000) |
   |82E803|argument in 2 next bytes: 1000 (DURATION: in ms)      |



[ev3-cdk]: https://mi-od-live-s.legocdn.com/r/www/r/mindstorms/-/media/franchises/mindstorms%202014/downloads/firmware%20and%20software/advanced/lego%20mindstorms%20ev3%20communication%20developer%20kit.pdf?l.r2=1239680513
[ev3-fdk]: https://mi-od-live-s.legocdn.com/r/www/r/mindstorms/-/media/franchises/mindstorms%202014/downloads/firmware%20and%20software/advanced/lego%20mindstorms%20ev3%20firmware%20developer%20kit.pdf?l.r2=830923294

### Discovery Notes

DuckDuckGo: usb 0694:0005 linux
->
(nothing of relevance)

Google: usb 0694:0005 linux
->
...
http://everything.plus/LEGO_WeDO_USB_Hub_with_Linux/zBYpQw3MrLo.video
"Ah, a WeDo?"

google: lego wedo python
->
https://github.com/itdaniher/WeDoMore
->
https://github.com/itdaniher/WeDoMore/blob/master/wedo/__init__.py
)

### Another USB intro

USB Communication with Python

[include photo of Kralicek catching Pokemon]

Say we have a robot, with a USB connection, and command documentation.
The only thing missing is knowing how to send a command over USB.

We'll use the pyusb Python library
https://github.com/walac/pyusb

on openSUSE:
sudo zypper install python-usb

To send a command, we need an Endpoint.
To get to the endpoint we need to descend down the hierarchy of

1. Device
2. Configuration 
3. Interface
4. Alternate setting
5. Endpoint

The device is identified with a vendor:product pair included in `lsusb` output.
```
Bus 002 Device 043: ID 0694:0005 Lego Group 
```

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
endpoint = interface[ENDPOINT_EV3]
```

If an Interface uses multiple Endpoints, they will differ
in transfer modes:
- Control transfers
- Interrupt transfers (keyboard): data arrives soon, with error detection
- Isochronous transfers (camera): data arrives on time, or gets lost
- Bulk transfers (printer): all data arrives, sooner or later

Now you should beable to understand the verbose output of `lsusb -v`
