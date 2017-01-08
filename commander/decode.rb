#!/usr/bin/env ruby
# Extract the serial communication data from a Bluetooth pcap capture

require_relative "savefile"
require "yaml"

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

def rfcomm_within_hci_h4(s)
  rcvd = s[0, 4].unpack("L>").first
  direction = case rcvd
  when 0
    :sent
  when 1
    :received
  else
    raise "Unhandled rcvd: #{rcvd}"
  end
  _acl = s[4, 4]
  serial_data = rfcomm_within_l2cap(s[9 .. -1])

  [direction, serial_data]
end

def assert_eq(expected, actual)
  raise "Expected #{expected} (#{expected.to_s(16)}), actual #{actual}" unless expected == actual
end

def rfcomm_within_l2cap(s)
  len = s[0, 2].unpack("S<").first
  _channel = s[2, 2].unpack("S<").first
  assert_eq(len, s[4 .. -1].size)

  handle_rfcomm(s[4 .. -1])
end

def hexdump(s)
  s.chars.map { |c| format("%02X", c.ord) }.join("")
end


def handle_rfcomm(s)
  # sloppy!
  credits = (s[1].ord & 0x10) != 0
  long = (s[2].ord > 128)

  s[(credits || long ? 4 : 3) .. -2]
end

serial_comm = []
each_pcap_packet_data(ARGV[0] || "tracker.pcap") do |data|
  direction, serial_data = rfcomm_within_hci_h4(data)
  serial_comm << {
    "sent" => direction == :sent,
    "hexdata" => hexdump(serial_data)
  }
end

print YAML.dump(serial_comm)
