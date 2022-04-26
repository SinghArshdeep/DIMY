import struct
import pickle
import sys
from bloom_filter import BloomFilter
from ecdsa import SECP128r1, ECDH
import subrosa
import socket
import threading
from hashlib import sha3_256
from time import sleep
from random import random
from collections import defaultdict

# Define some globals and locks
ip = 'localhost'
port = 55000
id_pub = None
hash = None
old_hash = b'temp'
ecdh = None
dbf = None
dbf_list = []
covid_free = 1
bloom_lock = threading.Lock()

# can only generate a new EphID when we have processed all received packets
hash_lock = threading.Lock()
print_lock = threading.Lock()


# Create a EphID for the client
def EphID():
    global ecdh
    ecdh = ECDH(curve=SECP128r1)
    ecdh.generate_private_key()
    return ecdh.get_public_key().to_string()


# Generate the encounter ID between the 2 nodes
# Uses Diffie - Hellman key exchange
def generateSecret(recv_key):
    global ecdh
    ecdh.load_received_public_key_bytes(recv_key)
    secret = ecdh.generate_sharedsecret_bytes()
    return secret


# Save and reset the daily bloom filter
def addResetDbf():
    global dbf_list, dbf, bloom_lock
    bloom_lock.acquire()
    dbf_list.append(dbf)
    if len(dbf_list) > 5:
        dbf_list.pop(0)
    dbf = BloomFilter(800000, 3)
    print("\nNew Daily Bloom filter created with",
          dbf.getBloomFilter().count(1), 'bits set\n')
    bloom_lock.release()


# Merge all the saved daily bloom filters into one
def combineDbfs():
    global dbf, dbf_list, bloom_lock
    bloom_filter = BloomFilter(800000, 3)
    bloom_lock.acquire()
    bloom_filter.union(dbf)
    temp = str(dbf.getBloomFilter().count(1))
    for i in dbf_list:
        temp = temp + ' + ' + str(i.getBloomFilter().count(1))
        bloom_filter.union(i)
    bloom_lock.release()
    with print_lock:
        print("\n\n==================== New bloom filter created",
              '====================\n')
        print("The bloom filter has", temp, '~', str(
            bloom_filter.getBloomFilter().count(1)), 'bits set\n')
    return bloom_filter


# Makes a structure to send over the TCP connection.
# Code taken from https://newbedev.com/python-socket-receive-large-amount-of-data/
def send_msg(sock, msg):
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)


# Sends the selected information and the bloom filter to the server
def contactServer(req):
    bloom_filter = combineDbfs()
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientSocket.connect((ip, port))
        msg = {'request': req, 'data': bloom_filter.getBloomFilter().tobytes()}
        send_msg(clientSocket, pickle.dumps(msg))
        response_data = clientSocket.recv(1024).decode()
        if response_data == 'Matched':
            print(
                "\n!!!!!!!!!!!!!!!!! You are a close contact. Isolate ASAP !!!!!!!!!!!!!!!!!\n")
        elif response_data == 'Not Matched':
            print(response_data, "\n-------------- You are safe!\n")
        else:
            print("Response data from server : ", response_data)
    except:
        print("!!!!!!!!!!!!!!!!! Error in contacting server !!!!!!!!!!!!!!!!!")
    finally:
        clientSocket.close()


#  Broadcast the EphID to all the nearby nodes
def sendToAll():
    global id_pub, hash, covid_free, hash_lock, old_hash, target_ports
    sock = socket.socket(family=socket.AF_INET,
                         type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    counter = 0
    id_pub = EphID()
    shares = subrosa.split_secret(id_pub, 3, 5)
    hash = sha3_256(id_pub).digest()
    with print_lock:
        print("\n\n==================== New EphID generated with hash",
              hash[:5], '====================')
        print('================================ No of chunks of EphID ',
              len(shares), "===============================")
    while covid_free:
        sleep(3)
        data = shares[counter].__bytes__() + b'||' + hash
        counter += 1
        if random() >= 0.5:
            print("Chunk No: ", counter, "sent")
            for p in target_ports:
                sock.sendto(data, ('', p))
        else:
            print("Chunk No: ", counter, "dropped")

        if counter == 5:
            with hash_lock:
                id_pub = EphID()
                old_hash = hash
                hash = sha3_256(id_pub).digest()
                shares = subrosa.split_secret(id_pub, 3, 5)
                counter = 0
                with print_lock:
                    print("\n\n==================== New EphID generated with hash",
                          hash[:5], '====================')
                    print('================================ No of chunks of EphID ',
                          len(shares), "===============================")


# Listen for any incoming shares from the nearby nodes
def receiver():
    global covid_free, dbf, hash, hash_lock, old_hash, my_port
    udpsock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udpsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udpsock.bind(('', my_port))
    hashes = defaultdict(list)

    while covid_free:

        try:
            share, new_hash = udpsock.recvfrom(1024)[0].split(b'||')
            with hash_lock:
                if new_hash != hash and new_hash != old_hash:
                    print("New share received:", len(
                        hashes[new_hash])+1, "\t\t\t\t\t     hash:", new_hash[:5])
                    hashes[new_hash].append(subrosa.Share.from_bytes(share))

                    if len(hashes[new_hash]) == 3:
                        recv_key = subrosa.recover_secret(hashes[new_hash])
                        temp_hash = sha3_256(recv_key).digest()
                        print(
                            "\t\t Hash generated for received EphID        ", temp_hash[:5])
                        if(new_hash == temp_hash):
                            secret = generateSecret(recv_key)
                            with print_lock:
                                print(
                                    "\n!!!!!!!!!!!!!!!!!!!!! Nodes in contact for atleast 9 seconds !!!!!!!!!!!!!!!!!!!!!")
                                print("\nEncounter ID: \t\t", secret)
                                dbf.add(secret)
                                secret = None
                                print(
                                    "\nEncounter ID added to daily bloom filter and deleted")
                                print("Daily Bloom filter has", dbf.getBloomFilter().count(
                                    1), 'bits set\n\n')
                        else:
                            print(
                                "\n!!!!!!!!!!!!!!!!!!!!!!!! Error in received packet hash !!!!!!!!!!!!!!!!!!!!!!!!\n")
        except:
            print(
                "!!!!!!!!!!!!!!!!!!!!!!!!! Error in receiving packet !!!!!!!!!!!!!!!!!!!!!!!!!")


# Contacts the server and checks if the node has come in contact with a positive case
def checkExposure():
    global dbf, port, covid_free
    dbf = BloomFilter(800000, 3)
    print("\nNew Daily Bloom filter created with",
          dbf.getBloomFilter().count(1), 'bits set\n')
    counter = 0

    while covid_free:
        sleep(90)
        counter += 1

        if counter == 6:
            counter = 0
            print('\nSending results to the server to check for close contact\n')
            contactServer("query")

        addResetDbf()


def getInput():
    global covid_free

    while covid_free:
        msg = input()

        if msg[0] == "c":
            with print_lock:
                print(
                    "\n\n==================================================================")
                print("\nUser Covid!!!!\nUploading close contacts to the server\n")
                print("User has to isolate^ at home.")
                print("\n\n\n^T&C apply.")
            contactServer("upload")
            covid_free = 0


# main function
def main():
    send = threading.Thread(name="Contacting Server", target=checkExposure)
    send.start()

    inputs = threading.Thread(name="Read Input", target=getInput)
    inputs.start()

    listen = threading.Thread(name="Receiving Shares", target=receiver)
    listen.start()

    broadcast = threading.Thread(name="Broadcast Shares", target=sendToAll)
    broadcast.start()


if len(sys.argv) != 3:
    print("%%%% Usage %%%% python3 Dimy.py my_port target_port/s")
    exit()

my_port = int(sys.argv[1])

ports = sys.argv[2].split(',')
target_ports = [int(x) for x in ports]
print("\nThe node is attached on port", my_port)
print("The node will broadcast EphID to", target_ports)
main()
