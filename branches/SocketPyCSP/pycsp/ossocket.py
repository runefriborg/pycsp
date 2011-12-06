
import time
import errno
import socket
import threading
from exceptions import *
from pycsp.common.const import *


def _connect(addr):
    connected = False
    t1 = None
    sock = None
    while (not connected):
        try:
            # Create IPv4 TCP socket (TODO: add support for IPv6)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Disable Nagle's algorithem, to enable faster send
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            # Connect to addr
            sock.connect(addr)
            connected = True
        except socket.error, (value,message):
            print value, message
            if sock:
                sock.close()
            if value != errno.ECONNREFUSED:            
                raise Exception("Fatal error: Could not open socket: " + message)
        if not connected:
            if t1 == None:
                t1 = time.time()
            else:
                if (time.time()-t1) > CONNECT_TIMEOUT:
                    raise SocketConnectException()
            time.sleep(CONNECT_RETRY_DELAY)

    return sock


def getThread():
    try:
        # compatible with Python 2.6+
        t = threading.current_thread()
    except AttributeError:
        # compatible with Python 2.5- 
        t = threading.currentThread()
    return t


EXPIRATION_LIMIT = 100

class DebugSocket():
    def __init__(self, sock):
        self.sock = sock

    def fileno(self):
        return self.sock.fileno()

    def accept(self):
        sock, addr = self.sock.accept()
        return (DebugSocket(sock), addr)

    def sendall(self, val):
        #print("Send(before): %s" % (str(self.sock.getsockname())))
        res = self.sock.sendall(val)
        return res
        #print("Send(after): %s" % (str(self.sock.getsockname())))

    def recv(self, c):
        data = self.sock.recv(c)
        return data

    def close(self):
        if self.sock:
            self.sock.close()

    def getsockname(self):
        return self.sock.getsockname()


#def DebugSocket(sock):
#    """ Overwrite Debugsocket class """
#    return sock

def start_server(server_addr=('', 0)):
    ok = False
    t1 = None
    sock = None
    while (not ok):
        try:
            # Create IPv4 TCP socket (TODO: add support for IPv6)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Disable Nagle's algorithem, to enable faster send
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            # Bind to address
            sock.bind(server_addr)
            ok = True
        except socket.error, (value,message):
            print value, message
            if sock:
                sock.close()
            if value != errno.EADDRINUSE:            
                raise Exception("Fatal error: Could not bind to socket: " + message)
        if not ok:
            if t1 == None:
                t1 = time.time()
            else:
                if (time.time()-t1) > BIND_TIMEOUT:
                    raise SocketBindException()
            time.sleep(BIND_RETRY_DELAY)
    
    # Obtain binded addresses
    address = sock.getsockname()

    # Initiate listening for connections. Create queue of 5 for unaccepted connections
    sock.listen(5)

    return DebugSocket(sock), address


def connect(addr):
    t = getThread()

    # Lookup connection
    if t.__dict__.has_key("conn"):
        if t.conn.has_key(addr):
            t.usage[addr] += 1
            return DebugSocket(t.conn[addr])
    
    sock = _connect(addr)

    # Save connection
    if t.__dict__.has_key("conn"):
        t.conn[addr] = sock
        t.usage[addr] = 1
    else:
        t.conn = {addr:sock}
        t.usage = {addr:1}

    return DebugSocket(sock)



def recvall(sock, msg_len):
    """
    A fast string concatenation in a loop that continues until the entire msg has been received
    """
    msg_len_received = 0
    msg_chunks = []
    while msg_len_received < msg_len:
        chunk = sock.recv(msg_len - msg_len_received)
        if chunk == '':
            raise SocketClosedException()
        msg_chunks.append(chunk)
        msg_len_received += len(chunk)
    return "".join(msg_chunks)
    

def sendall(addr, data):
    t = getThread()
    return t.conn[addr].sendall(data)
    

def close(addr):
    t = getThread()

    if (t.usage[addr] > EXPIRATION_LIMIT):
        sock = t.conn[addr]

        del t.conn[addr]
        del t.usage[addr]
        
        sock.close()
        #print("Disconnect: %s" % (str(addr)))

def closeall():
    t = getThread()

    for addr in t.conn:
        sock = t.conn[addr]
        sock.close()
        #print("Disconnect: %s" % (str(addr)))

    t.conn = {}
    t.usage = {}

def connectNOcache(addr):
    sock = _connect(addr)
    return DebugSocket(sock)

def closeNOcache(sock):
    sock.close()

