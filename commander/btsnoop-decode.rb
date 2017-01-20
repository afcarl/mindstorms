#!/usr/bin/env ruby
# Extract the serial communication data from a Bluetooth btsnoop capture

# http://www.fte.com/webhelp/FTS4BT/Content/Technical_Information/BT_Snoop_File_Format.htm

require "pp"
require "yaml"

class Btsnoop
  def initialize(io)
    sig = io.read(8)
    if sig != "btsnoop\x00"
      raise "Btsnoop signature not found"
    end

    version = io.read(4).unpack("L>").first
    raise "Btsnoop version unknown" unless version == 1

    @datalink = io.read(4).unpack("L>").first
    @io = io
  end

  def each_packet(&block)
    while not @io.eof?
      header = @io.read(24)
      orig_size, size, flags, drops, timestamp = header.unpack("L>L>L>L>Q>")
      data = @io.read(size)
      block.call(orig_size, size, flags, drops, timestamp, data)
    end
  end

  def each_packet_data(&block)
    each_packet do |_o, _s, flags, _d, _t, data|
      direction = flags.even? ? :sent : :received
      block.call(direction, data)
    end
  end
end

def assert_eq(expected, actual)
  raise "Expected #{expected} (#{expected.to_s(16)}), actual #{actual}" unless expected == actual
end

def hexdump(s)
  s.chars.map { |c| format("%02X", c.ord) }.join("")
end

def parse_hci_h4(data, &block)
  type = data[0].ord
  block.call(type, data[1 .. -1])
end

def parse_acl(data, &block)
  ugh, len = data[0, 4].unpack("S<S<")
  inner = data[4 .. -1]
  block.call(ugh, len, inner)
end

def parse_l2cap(data, &block)
  len, channel = data[0, 4].unpack("S<S<")
#  print "LEN #{len} CHAN #{channel} "
  inner = data[4 .. -1]
  block.call(len, channel, inner)
end

def parse_rfcomm(data, &block)
  dlci = data[0].ord
  channel = dlci >> 3
  credits_size = (data[1].ord & 0x10) == 0 ? 0 : 1
  len = data[2].ord
  if len.odd?
    addr_size = 1
    len = len >> 1
  else
    addr_size = 2
    len = (len + 256 * data[3].ord) / 2
  end
  return unless channel > 0 && len > 0
  inner = data[2 + addr_size + credits_size .. -2]
  assert_eq(len, inner.size)
  block.call(inner)
end

serial_comm = []

in_filename = ARGV[0] || "btsnoop_hci.log"
File.open(in_filename) do |f|
  bts = Btsnoop.new(f)
  bts.each_packet_data do |direction, data1|
    parse_hci_h4(data1) do |type, data2|
      if type == 2              # ACL
        parse_acl(data2) do |_, _len, data3|
          parse_l2cap(data3) do |_len, chan, data4|
            if chan != 1        # control channel
              parse_rfcomm(data4) do |serial_data|
                serial_comm << {
                  "sent" => direction == :sent,
                  "hexdata" => hexdump(serial_data)
                }
              end
            end
          end
        end
      end
    end
  end
end

File.write(in_filename + ".yaml", YAML.dump(serial_comm))
