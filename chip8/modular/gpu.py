from debug import *
import socket
import traceback

vram = [0] * 64 * 32
s = socket.socket()
display = socket.socket()
clients = []
# Constants
IP = 'localhost'
PORT = 11429
DISPLAYPORT = 11430
DISPLAYIP = 'localhost'
MAX_CONNECTIONS = 1

alive = True


# Display Communication Functions
def flip():
    display.send(bytearray(
        [0, 0x8, 0, 1]
    ) + bytearray(vram))


# Memory Functions
def draw(client, data):
    #log(data)
    px = data[0]
    py = data[1]
    height = data[2]
    row = 0
    flag = 0
    while row < height:
        curr_row = data[row + 3]
        pixel_offset = 1
        while pixel_offset < 9:
            pixel = (curr_row >> 8 - pixel_offset) & 1
            if pixel:
                if vram[((px + pixel_offset) % 64) + ((py + row) % 32) * 64 - 1]:
                    flag = 1
                    vram[((px + pixel_offset) % 64) + ((py + row) % 32) * 64 - 1] = 0
                else:
                    vram[((px + pixel_offset) % 64) + ((py + row) % 32) * 64 - 1] = 1
            pixel_offset += 1
        row += 1
    client[0].send(bytearray([flag]))
    flip()


def clearvram(client, data):
    global vram
    vram = [0] * 64 * 32


def stop(client, data):
    global alive
    display.send(bytearray([0, 0, 0, 0]))
    alive = False

funcdict = {
    0: stop,
    1: draw,
    2: clearvram
}


def init():
    print("GPU Module")
    # Setup Server
    log("Binding Socket to "+IP+":"+str(PORT)+"...")
    s.bind((IP, PORT))
    s.listen(MAX_CONNECTIONS)

    # Wait for CPU Connection
    log("Waiting for a CPU connection...")
    clients.append(s.accept())
    log("Connected by client from " + str(clients[0][1]))

    # Connect to a display
    log("Waiting for a Display Connection")
    display.connect((DISPLAYIP, DISPLAYPORT))
    log("Connected to a display")


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
    traceback.print_tb()
    input()
