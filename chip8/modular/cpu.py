from random import randrange
from debug import *
import socket
import time

Start = time.time()
frames = 0
alive = True

reg = [0] * 16
stack = []
index = 0x0
pc = 0x200
timerflag = time.time()
delay = 0
sound = 0

keys = [0] * 16
keypress = -1

# Sockets
memory = socket.socket()
MEMORYIP, MEMORYPORT = 'localhost', 11431
gpu = socket.socket()
GPUIP, GPUPORT = 'localhost', 11429
#display = socket.socket()
#DISPLAYIP, DISPLAYPORT = 'localhost', 11430


def readmemory(i, size):
    memory.send(bytearray(
        [0, 0, 3, 1, (i >> 8) & 0xF, i & 0xFF, size]
    ))
    return memory.recv(size)


def writememory(i, data):
    memory.send(bytearray(
        [0, 0, len(data) + 2, 2, i >> 8, i & 0xFF] + data
    ))


def draw(x, y, height, i):
    spritedata = readmemory(i, height)
    gpu.send(bytearray(
        [0, 0, 3 + height, 1] + [x, y, height]
    ) + spritedata)
    return gpu.recv(1)


def clearvram():
    gpu.send(bytearray(
        [0, 0, 0, 2]
    ))


def updatekeys():
    return [0] * 16, 0
    global keys, keypress
    display.send(bytearray(
        [0, 0, 0, 2]
    ))
    data = b''
    while data == b'':
        data = display.recv(17)
    keys = data[0:16]
    keypress = data[16]


def init():
    print("CPU Module")
    memory.connect((MEMORYIP, MEMORYPORT))
    log("Connected to memory")
    gpu.connect((GPUIP, GPUPORT))
    log("Connected to gpu")
    #display.connect((DISPLAYIP, DISPLAYPORT))
    #log("Connected to Display Input")


init()

while frames < 1000000:
    frames += 1
    # Retrieve OPCODE
    opcode = readmemory(pc, 2)
    opcode = (opcode[0] << 8) | opcode[1]
    #log(hex(opcode))
    a = opcode >> 12
    x = (opcode & 0x0F00) >> 8
    y = (opcode & 0x00F0) >> 4
    nnn = opcode & 0x0FFF
    kk = opcode & 0x00FF
    n = opcode & 0x000F

    # Increment Program Counter
    pc += 2

    # Execute OPCODE
    if a == 0x0:
        if kk == 0xE0:
            clearvram()

        elif kk == 0xEE:
            pc = stack.pop()

    elif a == 0x1:
        pc = nnn

    elif a == 0x2:
        stack.append(pc)
        pc = nnn

    elif a == 0x3:
        if reg[x] == kk:
            pc += 2

    elif a == 0x4:
        if reg[x] != kk:
            pc += 2

    elif a == 0x5:
        if reg[x] == reg[y]:
            pc += 2

    elif a == 0x6:
        reg[x] = kk

    elif a == 0x7:
        reg[x] = (reg[x] + kk) & 0xFF

    elif a == 0x8:
        if n == 0x0:
            reg[x] = reg[y] & 0xFF

        elif n == 0x1:
            reg[x] |= reg[y]
            reg[x] &= 0xFF

        elif n == 0x2:
            reg[x] &= reg[y] & 0xFF

        elif n == 0x3:
            reg[x] = (reg[x] ^ reg[y]) & 0xFF

        elif n == 0x4:
            reg[0xF] = 0
            reg[x] += reg[y]
            if reg[x] > 0xFF:
                reg[0xF] = 1
                reg[x] &= 0xFF

        elif n == 0x5:
            if reg[x] > reg[y]:
                reg[0xF] = 1
            else:
                reg[0xF] = 0
            reg[x] = (reg[x] - reg[y]) & 0xFF

        elif n == 0x6:
            reg[0xF] = reg[x] & 0x01
            reg[x] >>= 1

        elif n == 0x7:
            if reg[y] > reg[x]:
                reg[0xF] = 1
            else:
                reg[0xF] = 0
            reg[x] = (reg[y] - reg[x]) & 0xFF

        elif n == 0xE:
            reg[0xF] = (reg[x] & 0x80) >> 7
            reg[x] <<= 1
            reg[x] &= 0xFF

    elif a == 0x9:
        if reg[x] != reg[y]:
            pc += 2

    elif a == 0xA:
        index = nnn

    elif a == 0xB:
        pc = reg[0x0] + nnn

    elif a == 0xC:
        reg[x] = randrange(256) & kk

    elif a == 0xD:
        #start = time.time()
        reg[0xF] = draw(reg[x], reg[y], n, index)
        #print("Draw Time:", time.time()-start)

    elif a == 0xE:
        if kk == 0x9E:
            if keys[reg[x] & 0xF]:
                pc += 2

        elif kk == 0xA1:
            if not keys[reg[x] & 0xF]:
                pc += 2

    elif a == 0xF:
        if kk == 0x07:
            reg[x] = delay

        elif kk == 0x0A:
            if keypress == 255:
                pc -= 2
            else:
                reg[x] = keypress

        elif kk == 0x15:
            delay = reg[x]

        elif kk == 0x18:
            sound = reg[x]

        elif kk == 0x1E:
            reg[0xF] = 0
            index += reg[x]
            if index > 0xFFF:
                reg[0xF] = 1
                index &= 0xFFF

        elif kk == 0x29:
            index = reg[x] * 5

        elif kk == 0x33:
            data = [
                int(reg[x] / 100),
                int(reg[x] / 10) % 10,
                reg[x] % 10
            ]
            writememory(index, data)

        elif kk == 0x55:
            data = []
            for r in range(x+1):
                memory[r] = reg[r]
            writememory(index, data)
            index += x + 1

        if kk == 0x65:
            data = readmemory(index, x+1)
            for r in range(x+1):
                reg[r] = data[r]
            index += x + 1

    # Decrement Timers
    if time.time() - timerflag >= 1/60:
        if delay > 0:
            delay -= 1
        if sound > 0:
            sound -= 1
        timerflag = time.time()
    updatekeys()

print("FPS: ", frames/(time.time()-Start))
input()
