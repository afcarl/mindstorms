#!/usr/bin/env python2

# Send a BEEP command via USB to a Lego Mindstorms EV3 brick

import sys
import usb.core                 # https://walac.github.io/pyusb/

def ev3_write(command):
    # To send commands, we need an Endpoint.

    # To get to the endpoint we need to descend down the hierarchy of
    # 1. Device
    VENDOR_LEGO = 0x0694
    PRODUCT_EV3 = 5
    # 2. Configuration 
    CONFIGURATION_EV3 = 1       # 1-based
    # 3. Interface
    INTERFACE_EV3 = 0           # 0-based
    # 4. Alternate setting
    SETTING_EV3 = 0             # 0-based
    # 5. Endpoint
    ENDPOINT_EV3 = 1            # 0-based

    # 1. Device
    device = usb.core.find(idVendor=VENDOR_LEGO, idProduct=PRODUCT_EV3)
    if device is None:
        print("Is the brick connected and turned on?")
        sys.exit(1)

    # By default, the kernel will claim the device and make it available via
    # /dev/usb/hiddevN and /dev/hidrawN which also prevents us
    # from communicating otherwise. This removes these kernel devices.
    # Yes, it is weird to specify an interface before we get to a configuration.
    if device.is_kernel_driver_active(INTERFACE_EV3):
        print("Detaching kernel driver")
        device.detach_kernel_driver(INTERFACE_EV3)

    # 2. Configuration
    # A Device may have multiple Configurations, and only one can be active at
    # a time. Most devices have only one. Supporting multiple Configurations
    # is reportedly useful for offering more/less features when more/less
    # power is available.
    ## Because multiple configs are rare, the library allows to omit this:
    ## device.set_configuration(CONFIGURATION_EV3)
    configuration = device.get_active_configuration()

    # 3. Interface
    # A physical Device may have multiple Interfaces active at a time.
    # A typical example is a scanner-printer combo.
    #
    # 4. Alternate setting
    # I don't quite understand this, but they say that if you need Isochronous
    # Endpoints (read: audio or video), you must go to a non-primary
    # Alternate Setting.
    interface = configuration[(INTERFACE_EV3, SETTING_EV3)]

    # 5. Endpoint
    # The Endpoint 0 is reserved for control functions
    # so we use Endpoint 1 here.
    # If an Interface uses multiple Endpoints, they will differ
    # in transfer modes:
    # - Interrupt transfers (keyboard): data arrives soon, with error detection
    # - Isochronous transfers (camera): data arrives on time, or gets lost
    # - Bulk transfers (printer): all data arrives, sooner or later
    endpoint = interface[ENDPOINT_EV3]

    # Finally!
    endpoint.write(command)

beep_command = \
    '\x0F\x00\x01\x00\x80\x00\x00\x94\x01\x81\x02\x82\xE8\x03\x82\xE8\x03'
ev3_write(beep_command)
