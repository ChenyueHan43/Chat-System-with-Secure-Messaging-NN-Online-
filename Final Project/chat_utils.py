import socket
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
import base64

# use local loop back address by default
#CHAT_IP = '127.0.0.1'
# CHAT_IP = socket.gethostbyname(socket.gethostname())
CHAT_IP = '127.0.0.1'#socket.gethostbyname(socket.gethostname())

CHAT_PORT = 1112
SERVER = (CHAT_IP, CHAT_PORT)

menu = "\n++++ Choose one of the following commands\n \
        time: calendar time in the system\n \
        who: to find out who else are there\n \
        c _peer_: to connect to the _peer_ and chat\n \
        ? _term_: to search your chat logs where _term_ appears\n \
        p _#_: to get number <#> sonnet\n \
        q: to leave the chat system\n\n"

S_OFFLINE   = 0
S_CONNECTED = 1
S_LOGGEDIN  = 2
S_CHATTING  = 3

SIZE_SPEC = 5

CHAT_WAIT = 0.2

def print_state(state):
    print('**** State *****::::: ')
    if state == S_OFFLINE:
        print('Offline')
    elif state == S_CONNECTED:
        print('Connected')
    elif state == S_LOGGEDIN:
        print('Logged in')
    elif state == S_CHATTING:
        print('Chatting')
    else:
        print('Error: wrong state')

def mysend(s, msg):
    #append size to message and send it
    msg = ('0' * SIZE_SPEC + str(len(msg)))[-SIZE_SPEC:] + str(msg)
    msg = msg.encode()
    total_sent = 0
    while total_sent < len(msg) :
        sent = s.send(msg[total_sent:])
        if sent==0:
            print('server disconnected')
            break
        total_sent += sent

def myrecv(s):
    #receive size first
    size = ''
    while len(size) < SIZE_SPEC:
        text = s.recv(SIZE_SPEC - len(size)).decode()
        if not text:
            print('disconnected')
            return('')
        size += text
    size = int(size)
    #now receive message
    msg = ''
    while len(msg) < size:
        text = s.recv(size-len(msg)).decode()
        if text == b'':
            print('disconnected')
            break
        msg += text
    #print ('received '+message)
    return (msg)

def text_proc(text, user):
    ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
    return('(' + ctime + ') ' + user + ' : ' + text) # message goes directly to screen

def generate_rsa_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return public_key, private_key

def serialize_public_key(pubkey):
    pem = pubkey.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem

def deserialize_public_key(pem_bytes):
    pubkey = serialization.load_pem_public_key(pem_bytes)
    return pubkey

def rsa_decrypt(cipher_bytes, private_key):
    plain_bytes = private_key.decrypt(
        cipher_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plain_bytes

def rsa_encrypt(plain_text: str, public_key):
    encrypted = public_key.encrypt(
        plain_text.encode(),   
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted