#!/usr/bin/env ruby
require_relative "savefile"


def each_pcap_packet_data(pcap_filename, &block)
  File.open(pcap_filename) do |io|
    header = Pcap::Savefile::GlobalHeader.from_io(io)
    raise unless header.network == 201 # LINKTYPE_BLUETOOTH_HCI_H4_WITH_PHDR

    while not io.eof? do
      packet = Pcap::Savefile::Packet.from_io(io)
      block.call(packet.data)
    end
  end
end

def hexdump(s)
  s.chars.map { |c| format("%02X", c.ord) }.join(" ")
end

def handle_hci_h4(s)
  rcvd = s[0, 4].unpack("L>").first
  case rcvd
  when 0
    print "SENT "
  when 1
    print "RCVD "
  else
    raise "Unhandled rcvd: #{rcvd}"
  end
  acl = s[4, 4]
  handle_l2cap(s[9 .. -1])
end

def assert_eq(expected, actual)
  raise "Expected #{expected} (#{expected.to_s(16)}), actual #{actual}" unless expected == actual
end

def handle_l2cap(s)
  len = s[0, 2].unpack("S<").first
  channel = s[2, 2].unpack("S<").first

  assert_eq(len, s[4 .. -1].size)

  case channel
  when 0x40, 0x41
    handle_rfcomm(s[4 .. -1])
  else
    puts "?"
  end
end

def handle_rfcomm(s)
  # sloppy!
  credits = (s[1].ord & 0x10) != 0
  long = (s[2].ord > 128)
  handle_rfcomm_data(s[(credits || long ? 4 : 3) .. -2])
end

def handle_rfcomm_data(s)
  handle_ev3(s)
end

def handle_ev3(s)
  print "EV3 "
  len = s[0, 2].unpack("S<").first
  data = s[2 .. -1]
  assert_eq(len, data.size) # rescue puts "!!!"

  puts hexdump(data)
  print "  "

  id = data[0, 2].unpack("S<").first
  type = data[2, 1].ord
  print "##{id} #{CMD_TYPES[type]} "

  if type == 0 or type == 0x80
    alloc = data[3, 2].unpack("S<").first
    globals = alloc & 0x03ff
    locals = alloc >> 10
    print "(G#{globals}, L#{locals}) "
    bytecodes = data[5, -1]
  else
    bytecodes = data[3, -1]
  end
  puts
end

CMD_TYPES = {
  0x01 => "SYSTEM_COMMAND_REPLY",
  0x81 => "SYSTEM_COMMAND_NO_REPLY",
  0x03 => "SYSTEM_REPLY",
  0x05 => "SYSTEM_ERROR",

  0x00 => "DIRECT_COMMAND_REPLY",
  0x80 => "DIRECT_COMMAND_NO_REPLY",
  0x02 => "DIRECT_REPLY",
  0x04 => "DIRECT_REPLY_ERROR",
}

each_pcap_packet_data("tracker.pcap") do |data|
#  print "DATA "
  handle_hci_h4(data)
end
