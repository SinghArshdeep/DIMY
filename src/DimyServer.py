import pickle
import struct
from socket import *
import threading
from bloom_filter import *
from bitarray import bitarray

ip = 'localhost'
port = 55000
lock = threading.Lock()
bloom_filter = BloomFilter(800000)


# Makes a structure to send over the TCP connection.
# Code taken from https://newbedev.com/python-socket-receive-large-amount-of-data/
def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall2(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    return recvall2(sock, msglen)


def recvall2(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


# Adds new bloom filter to the master bloom filter
def newBloomFilter(filter):
    global bloom_filter
    print("\n!!!!!!!!!!!!!!!!!!!!!!!! New Close Contacts Added !!!!!!!!!!!!!!!!!!!!!!!!\n")
    print("\nThe CBF has", str(filter.getBloomFilter().count(1)), 'bits set\n')
    lock.acquire()
    bloom_filter.union(filter)
    print("The MASTER CBF has", str(
        bloom_filter.getBloomFilter().count(1)), 'bits set\n')
    lock.release()


# Match a query bloom filter to the master filter
def matchqbf(filter):
    global bloom_filter
    print("\n----------------Matching records.", "The QBF has",
          str(filter.getBloomFilter().count(1)), 'bits set\n')
    lock.acquire()
    print("The MASTER CBF has", str(
        bloom_filter.getBloomFilter().count(1)), 'bits set\n')
    filter.intersection(bloom_filter)
    count = filter.getBloomFilter().count(1)
    lock.release()
    print("No of bits matched", count)
    if count > 2:
        print(
            "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! MATCH FOUND !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        return "Matched"
    return "Not Matched"


# handles a client connection by processing their request
def handle_client(connectionSocket):
    qbf = BloomFilter()
    data = pickle.loads(recv_msg(connectionSocket))
    # print(data)
    temp = bitarray()
    temp.frombytes(data['data'])
    qbf.setBitArray(temp)
    msg = 'ERRROR'
    if data['request'] == "query":
        msg = matchqbf(qbf)
    elif data['request'] == "upload":
        newBloomFilter(qbf)
        msg = "Upload successfull"

    # Sending response
    connectionSocket.send(str.encode(msg))
    connectionSocket.close()


# Creates new threads to handle a client connection
def server():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSocket.bind((ip, port))
    serverSocket.listen(10)

    print("\nThe server is listening on PORT ", port)

    while 1:

        connectionSocket, addr = serverSocket.accept()
        # print(f'Accepted connection from {addr}')
        c_thread = threading.Thread(
            target=handle_client, args=(connectionSocket,))
        c_thread.start()


# main function
if __name__ == "__main__":
    server()
