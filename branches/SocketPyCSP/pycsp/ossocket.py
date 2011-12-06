

import socket
import threading

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
    
    # Create IPv4 TCP socket (TODO: add support for IPv6)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Disable Nagle's algorithem, to enable faster send
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    # Bind to address
    s.bind(server_addr)
    
    # Obtain binded addresses
    address = s.getsockname()

    # Initiate listening for connections. Create queue of 5 for unaccepted connections
    s.listen(5)

    return DebugSocket(s), address


def connect(addr):
    t = getThread()

    # Lookup connection
    if t.__dict__.has_key("conn"):
        if t.conn.has_key(addr):
            t.usage[addr] += 1
            return DebugSocket(t.conn[addr])
    
    #print("Connect: %s" % (str(addr)))

    # Create IPv4 TCP socket (TODO: add support for IPv6)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Disable Nagle's algorithem, to enable faster send
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    # Connect
    sock.connect(addr)

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
    # Create IPv4 TCP socket (TODO: add support for IPv6)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Disable Nagle's algorithem, to enable faster send
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    # Connect
    sock.connect(addr)

    return DebugSocket(sock)

def closeNOcache(sock):
    sock.close()

