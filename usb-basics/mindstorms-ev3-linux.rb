#!/usr/bin/env ruby

# Send a BEEP command via USB to a Lego Mindstorms EV3 brick

require "libusb"                # https://github.com/larskanis/libusb

# To send commands, we need an Endpoint.

# To get to the endpoint we need to descend down the hierarchy of
# 1. Device
VENDOR_LEGO = 0x0694
PRODUCT_EV3 = 5
# 2. Configuration 
CONFIGURATION_EV3 = 1         # 1-based
# 3. Interface
INTERFACE_EV3 = 0             # 0-based
# 4. Alternate setting
SETTING_EV3 = 0               # 0-based
# 5. Endpoint
ENDPOINT_EV3 = 1              # 0-based

def ev3_write(command)
  # 1. Device
  usb = LIBUSB::Context.new
  device = usb.devices(idVendor: VENDOR_LEGO, idProduct: PRODUCT_EV3).first

  # 2. Configuration
  # A Device may have multiple Configurations, and only one can be active at
  # a time. Most devices have only one. Supporting multiple Configurations
  # is reportedly useful for offering more/less features when more/less
  # power is available.
  ## Because multiple configs are rare, the library allows to omit this:
  ## device.set_configuration(CONFIGURATION_EV3)

  # 3. Interface
  # A physical Device may have multiple Interfaces active at a time.
  # A typical example is a scanner-printer combo.
  #
  # 4. Alternate setting
  # I don't quite understand this, but they say that if you need Isochronous
  # Endpoints (read: audio or video), you must go to a non-primary
  # Alternate Setting.
  interface = device.interfaces[INTERFACE_EV3]

  # 5. Endpoint
  # The Endpoint 0 is reserved for control functions
  # so we use Endpoint 1 here.
  # If an Interface uses multiple Endpoints, they will differ
  # in transfer modes:
  # - Interrupt transfers (keyboard): data arrives soon, with error detection
  # - Isochronous transfers (camera): data arrives on time, or gets lost
  # - Bulk transfers (printer): all data arrives, sooner or later
  endpoint = interface.endpoints.find{|e| e.direction == :out}

  # Finally!
  device.open_interface(interface) do |handle|
    handle.interrupt_transfer(endpoint: endpoint, dataOut: command)
  end
end

beep_command = \
    "\x0F\x00\x01\x00\x80\x00\x00\x94\x01\x81\x02\x82\xE8\x03\x82\xE8\x03"
ev3_write(beep_command)
