from debug import *
import socket

memory = [0] * 0xFFF
s = socket.socket()
clients = []
# Constants
IP = 'localhost'
PORT = 11431
MAX_CONNECTIONS = 1

alive = True


# Memory Functions
def readfrom(client, data):
    index = (data[0] << 8) | data[1]
    buffersize = data[2]
    buffer = bytearray(memory[index:index+buffersize])
    client[0].send(buffer)


def writeto(client, data):
    index = (data[0] << 8) | data[1]
    buffer = data[2:]
    for b in range(len(buffer)):
        memory[index + b] = buffer[b]


def stop(client, data):
    global alive
    alive = False

funcdict = {
    0: stop,
    1: readfrom,
    2: writeto
}


def init(rom="../roms/Trip8.ch8"):
    print("Memory Module")
    # Load Memory with Fonts and Chip8 Program
    fonts = [0xF0, 0x90, 0x90, 0x90, 0xF0,
             0x20, 0x60, 0x20, 0x20, 0x70,
             0xF0, 0x10, 0xF0, 0x80, 0xF0,
             0xF0, 0x10, 0xF0, 0x10, 0xF0,
             0x90, 0x90, 0xF0, 0x10, 0x10,
             0xF0, 0x80, 0xF0, 0x10, 0xF0,
             0xF0, 0x80, 0xF0, 0x90, 0xF0,
             0xF0, 0x10, 0x20, 0x40, 0x40,
             0xF0, 0x90, 0xF0, 0x90, 0xF0,
             0xF0, 0x90, 0xF0, 0x10, 0xF0,
             0xF0, 0x90, 0xF0, 0x90, 0x90,
             0xE0, 0x90, 0xE0, 0x90, 0xE0,
             0xF0, 0x80, 0x80, 0x80, 0xF0,
             0xE0, 0x90, 0x90, 0x90, 0xE0,
             0xF0, 0x80, 0xF0, 0x80, 0xF0,
             0xF0, 0x80, 0xF0, 0x80, 0x80]
    log("Loading Font Set...")
    for f in range(len(fonts)):
        memory[f] = fonts[f]
    log("Loading Program at "+rom+" into memory...")
    rom = open(rom, 'br').read()
    for f in range(len(rom)):
        memory[f + 0x200] = rom[f]

    # Setup Server
    log("Binding Socket to "+IP+":"+str(PORT)+"...")
    s.bind((IP, PORT))
    s.listen(MAX_CONNECTIONS)

    # Wait for Connection
    log("Waiting for a connection...")
    clients.append(s.accept())
    log("Connected by client from " + str(clients[0][1]))


def execute(header, client):
    size = (header[0] << 16) | (header[1] << 8) | (header[2])
    data = client[0].recv(size)
    instruction = header[3]
    funcdict[instruction](client, data)


def main():
    init()
    while alive:
        for client in clients:
            header = client[0].recv(4)
            if header == b'':
                continue
            #log("Received command from " + str(client[1]))
            execute(header, client)

try:
    main()
except Exception:
    input()
