from pygame.locals import *
from debug import *
import socket
import pygame
import traceback

pygame.init()

s = socket.socket()
clients = []
# Constants
IP = 'localhost'
PORT = 11430
MAX_CONNECTIONS = 1

WIDTH = 640
HEIGHT = 320

bindings = {
    0: K_KP0,
    1: K_KP1,
    2: K_KP2,
    3: K_KP3,
    4: K_KP4,
    5: K_KP5,
    6: K_KP6,
    7: K_KP7,
    8: K_KP8,
    9: K_KP9,
    10: K_KP_PERIOD,
    11: K_KP_ENTER,
    12: K_KP_PLUS,
    13: K_KP_MINUS,
    14: K_KP_MULTIPLY,
    15: K_KP_DIVIDE
}

display = pygame.display.set_mode((WIDTH, HEIGHT))

alive = True


# Memory Functions
def flip(client, data):
    global display
    display.fill((0, 0, 0))
    for y in range(32):
        for x in range(64):
            if data[x + y*64]:
                pygame.draw.rect(display, (255, 255, 255), (x * 10, y * 10, 10, 10))
    pygame.display.flip()


def updatekeys(client, data):
    try:
        if get_focused():
            keys = get_pressed()
            keys = [keys[bindings[0]], keys[bindings[1]], keys[bindings[2]], keys[bindings[3]], keys[bindings[4]], keys[bindings[5]], keys[bindings[6]], keys[bindings[7]], keys[bindings[8]], keys[bindings[9]], keys[bindings[10]], keys[bindings[11]], keys[bindings[12]], keys[bindings[13]], keys[bindings[14]], keys[bindings[15]]]
            keypress = keys.index(1)
            client[0].send(bytearray(
                keys + [keypress]
            ))
        else:
            client[0].send(bytearray(
                [0] * 16 + [255]
            ))
    except:
        client[0].send(bytearray(
            [0] * 16 + [255]
        ))


def stop(client, data):
    global alive
    input()
    alive = False


funcdict = {
    0: stop,
    1: flip,
    2: updatekeys
}


def init():
    print("Display Module")
    # Setup Server
    log("Binding Socket to "+IP+":"+str(PORT)+"...")
    s.bind((IP, PORT))
    s.listen(MAX_CONNECTIONS)

    # Wait for Connection from a GPU
    log("Waiting for a connection...")
    clients.append(s.accept())
    log("Connected by client from " + str(clients[0][1]))

    # Wait for CPU to connect to IO socket
    #log("Waiting for an IO connection...")
    #clients.append(s.accept())
    #log("Connected by client from " + str(clients[1][1]))


def execute(header, client):
    size = (header[0] << 16) | (header[1] << 8) | (header[2])
    data = client[0].recv(size)
    instruction = header[3]
    funcdict[instruction](client, data)


def main():
    global alive
    init()
    while alive:
        for client in clients:
            header = client[0].recv(4)
            if header == b'':
                continue
            #log("Received command from " + str(client[1]))
            execute(header, client)
        for event in pygame.event.get():
            if event.type == QUIT:
                alive = False

try:
    main()
except Exception:
    traceback.print_tb()
    input()
