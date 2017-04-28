#!/usr/bin/env python

from __future__ import print_function
import bluetooth
import struct

def make_lc(n):
    if -32 < n < 32:
        return [n & 0x3f]
    if -128 < n < 128:
        return [0x81, n & 0xff]
    if -32768 < n < 32768:
        return [0x82, n & 0xff, (n >> 8) & 0xff]
    return [0x83, n & 0xff, (n >> 8) & 0xff, (n >> 16) & 0xff, (n >> 24) & 0xff]

class VMError(RuntimeError):
    pass

class Instruction:        
    def primpar(self, n):
        if type(n) is int:
            return "".join([chr(x) for x in make_lc(n)])
        elif type(n) is str:
            return "\x80" + n + "\x00"
        else:
            raise RuntimeError, "Unknown type"

    def beep(self):
        return self.tone(2, 880, 500)
    
    def tone(self, volume, frequency, duration_ms):
        return self.sound_tone(volume, frequency, duration_ms)

    def sound_break(self):
        return "\x94" + self.primpar(0)

    def sound_tone(self, volume, frequency, duration_ms):
        return "\x94" + self.primpar(1) + \
            self.primpar(volume) + \
            self.primpar(frequency) + \
            self.primpar(duration_ms)

    def sound_play(self, volume, filename):
        return "\x94" + self.primpar(2) + \
            self.primpar(volume) + \
            self.primpar(filename)

    def sound_repeat(self, volume, filename):
        return "\x94" + self.primpar(3) + \
            self.primpar(volume) + \
            self.primpar(filename)

    def sound_ready(self):
        return "\x96"
    
    def output_step_speed(self, layer = 0, nos = 0, speed = 0,
                          step_begin = 0, step_do = 0, step_end = 0, brake = 0):
        return "\xae" + \
            self.primpar(layer) + \
            self.primpar(nos) + \
            self.primpar(speed) + \
            self.primpar(step_begin) + \
            self.primpar(step_do) + \
            self.primpar(step_end) + \
            self.primpar(brake)

    def output_step_sync(self, layer = 0, nos = 0, speed = 0,
                         turn = 0, step = 0, brake = 0):
        return "\xb0" + \
            self.primpar(layer) + \
            self.primpar(nos) + \
            self.primpar(speed) + \
            self.primpar(turn) + \
            self.primpar(step) + \
            self.primpar(brake)

    def output_ready(self, layer = 0, nos = 0):
        return "\xaa" + \
            self.primpar(layer) + \
            self.primpar(nos)

    def output_start(self, layer = 0, nos = 0):
        return "\xa6" + \
            self.primpar(layer) + \
            self.primpar(nos)

def u16(n):
    return chr(n & 0xff) + \
        chr((n >> 8) & 0xff)

def u32(n):
    return chr(n & 0xff) + \
        chr((n >> 8) & 0xff) + \
        chr((n >> 16) & 0xff) + \
        chr((n >> 24) & 0xff)

def unpack_u16(s):
    return struct.unpack("<H", s)[0]

def unpack_u32(s):
    return struct.unpack("<L", s)[0]

class SysInstruction(Instruction):
    def begin_download(self, length, filename):
        """The VM will download *length* bytes and store them at *filename*"""
        return chr(0x92) + u32(length) + filename + chr(0)

    def continue_download(self, handle, data):
        return chr(0x93) + chr(handle) + data

    def begin_upload(self, length, filename):
        """The VM will upload *length* bytes from the file named *filename*"""
        return chr(0x94) + u16(length) + filename + chr(0)

    def continue_upload(self, handle, length):
        return chr(0x95) + chr(handle) + u16(length)

    def close_filehandle(self, handle):
        return chr(0x98) + chr(handle)

    def list_files(self, buf_size, filename):
        return chr(0x99) + u16(buf_size) + filename + chr(0)

    def list_open_handles(self):
        return chr(0x9d)

class MessageSender:
    def __init__(self, socket):
        self.counter = 0
        self.socket = socket

    def msgid(self):
        self.counter += 1
        return self.counter

    def u16(self, n):
        return chr(n & 0xff) + chr((n >> 8) & 0xff)
    
    def direct_command(self, instr_bytes):
        cmd_type = 0x80
        var_alloc = 0           # FIXME
        bytes = self.u16(self.msgid()) + chr(cmd_type) + \
                self.u16(var_alloc) + instr_bytes

        packet = self.u16(len(bytes)) + bytes
        print("->")
        print(repr(packet))
        self.socket.send(packet)
    
    def direct_command_with_reply(self, instr_bytes):
        cmd_type = 0x00
        var_alloc = 0           # FIXME
        bytes = self.u16(self.msgid()) + chr(cmd_type) + \
                self.u16(var_alloc) + instr_bytes

        packet = self.u16(len(bytes)) + bytes
        print("->", repr(packet), sep="")
        self.socket.send(packet)

        reply = self.recv_packet()
        print("<-", repr(reply), sep="")

    def system_command(self, instr_bytes):
        cmd_type = 0x81
        bytes = self.u16(self.msgid()) + chr(cmd_type) + \
                instr_bytes

        packet = self.u16(len(bytes)) + bytes
        print("->", repr(packet), sep="")
        self.socket.send(packet)

    def unmarshall_packet(self, bytes):
        msgid = unpack_u16(bytes[0:2])
        return msgid, bytes[2:]

    def recv_packet(self):
        buf = self.socket.recv(2)
        print("R<-", repr(buf), sep="")
        size = unpack_u16(buf[0:2])

        res = ""
        while len(res) < size:
            buf = self.socket.recv(min(512, size - len(res)))
            print("R<-", repr(buf), "(", len(buf), ")", sep="")
            res += buf
        if len(res) > size:
            raise "AARG"
        return res

    def system_command_with_reply(self, instr_bytes):
        cmd_type = 0x01
        cmd_id = self.msgid()
        bytes = self.u16(cmd_id) + chr(cmd_type) + \
                instr_bytes

        packet = self.u16(len(bytes)) + bytes
        print("->", repr(packet), sep="")
        self.socket.send(packet)

        reply = self.recv_packet()
        print("<-", repr(reply), sep="")

        id, reply2 = self.unmarshall_packet(reply)
        assert id == cmd_id
        rep_type = ord(reply2[0]) # 03 sysreply, 05 syserror
        rep_cmd = ord(reply2[1])
        rep_status = ord(reply2[2])
        if rep_type == 0x05:
            raise VMError, "Error: {0}".format(rep_status)
        payload = reply2[3:]
        return payload

host = "00:16:53:53:EE:8C" # "KRALICEK"
port = 1                   # the rfcomm port ev3 uses
sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((host, port))

ins = Instruction()
sins = SysInstruction()
ms = MessageSender(sock)

MOTOR_B = 2
MOTOR_C = 4

instrs = [
    ins.tone(2, 1760, 500),
    ins.sound_ready(),

    ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                          speed = 50,
                          step_do = 1080),
    ins.output_ready(nos = MOTOR_B | MOTOR_C),
    
    ins.tone(2, 1760, 500),
    ins.sound_ready(),

    ins.output_step_sync(nos = MOTOR_B | MOTOR_C,
                         speed = +30,
                         turn = 200,
                         step = 1000),
    ins.output_ready(nos = MOTOR_B | MOTOR_C),
    
    ins.tone(2, 1760, 500),
    ins.sound_ready(),

    ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                          speed = 50,
                          step_do = 1080),
    ins.output_ready(nos = MOTOR_B | MOTOR_C),

    ins.beep(),
    ins.sound_ready(),
]

def fwbk(step):
    ins = Instruction()
    return "".join([
        ins.output_step_sync(nos = MOTOR_B | MOTOR_C,
                             speed = 50,
                             turn = 0,
                             step = step),
        ins.output_ready(nos = MOTOR_B | MOTOR_C),
        ins.output_step_sync(nos = MOTOR_B | MOTOR_C,
                             speed = 50,
                             turn = 0,
                             step = -step),
        ins.output_ready(nos = MOTOR_B | MOTOR_C),
    ])

def upload(fname):
    bufsize = 1024
    sinstr = sins.begin_upload(bufsize, "/home/root/lms2012/prjs/" + fname)
    p = ms.system_command_with_reply(sinstr)
    size = unpack_u32(p[0:4])
    handle = ord(p[4])
    fdata = p[5:]

    while True:
        sinstr = sins.continue_upload(handle, bufsize)
        try:
            p = ms.system_command_with_reply(sinstr)
        except VMError:
            break
        rhandle = ord(p[0])
        fdata += p[1:]

    with open("upload.bin", "w") as f:
        f.write(fdata)

turnstep = 450
while True:
    instr = None
    print("(ts={0}) > ".format(turnstep), end = '')
    cmd = raw_input()
    if cmd == "q":
        break
    elif cmd == "k":
        instr = ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                                      speed = 75,
                                      step_begin = 180,
                                      step_do = 360,
                                      step_end = 180)
    elif cmd == "z":
        instr = ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                                      speed = -75,
                                      step_begin = 180,
                                      step_do = 360,
                                      step_end = 180)
    elif cmd == "l":
        instr = ins.output_step_sync(nos = MOTOR_B | MOTOR_C,
                                     speed = +30,
                                     turn = -200,
                                     step = turnstep)
    elif cmd == "r":
        instr = ins.output_step_sync(nos = MOTOR_B | MOTOR_C,
                                     speed = +30,
                                     turn = +200,
                                     step = turnstep)
    elif cmd == "+":
        turnstep += 50
        continue
    elif cmd == "-":
        turnstep -= 50
        continue
    elif cmd == "f":
        instr = ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                                      speed = 50,
                                      step_begin = 30,
                                      step_do = 30,
                                      step_end = 30)
    elif cmd == "b":
        instr = ins.output_step_speed(nos = MOTOR_B | MOTOR_C,
                                      speed = -50,
                                      step_begin = 30,
                                      step_do = 30,
                                      step_end = 30)
    elif cmd == "p":
#        instr = ins.sound_repeat(2, "../prjs/tracker/idle")
        instr = ins.sound_play(100, "../prjs/mluveni/huu")

    elif cmd == "s":
        instr = ins.sound_break()

    elif cmd[0:2] == "L ":
        sinstr = sins.list_files(9999, "/home/root/lms2012/prjs/" + cmd[2:])
        p = ms.system_command_with_reply(sinstr)
        l = p[0:4]
        print(p[4:])

    elif cmd == "U":
        upload("SD_Card/MindCub3r-v2p1/MindCub3r.rbf")

    elif cmd[0:2] == "U ":
        fname = cmd[2:]
        upload(fname)

    elif cmd == "D":
        with open("../sound-rsf/huu.rsf") as f:
            contents = f.read()

        sinstr = sins.begin_download(len(contents), "/home/root/lms2012/prjs/mluveni/huu.rsf")
        p = ms.system_command_with_reply(sinstr)
        handle = ord(p[0])

        sinstr = sins.continue_download(handle, contents)
        p = ms.system_command_with_reply(sinstr)

        sinstr = sins.close_filehandle(handle)
        try:
            p = ms.system_command_with_reply(sinstr)
        except RuntimeError:
            pass                # why does it reply Unknown Handle?

    else:
        print("?")

    if instr is not None:
        ms.direct_command_with_reply(instr)
        instr = ins.output_ready(nos = MOTOR_B | MOTOR_C)
        ms.direct_command_with_reply(instr)


sock.close()
