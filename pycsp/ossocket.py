

import socket
import osprocess

EXPIRATION_LIMIT = 10

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
        return self.sock.recv(c)

    def close(self):
        if self.sock:
            self.sock.close()

    def getsockname(self):
        return self.sock.getsockname()


def DebugSocket(sock):
    """ Overwrite Debugsocket class """
    return sock

def getID():
    t, name = osprocess.getThreadAndName()
    if name == "MainThread":
        id = "__mainproc__"
    else:
        id = t.id
    return id

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



stored_connections = {}
usage_connections = {}

def connect(addr):
    global stored_connections, usage_connections

    t_id = getID()

    # Lookup connection
    if stored_connections.has_key(t_id):
        if stored_connections[t_id].has_key(addr):
            #print "REUSE of socket"
            usage_connections[t_id][addr] += 1
            return DebugSocket(stored_connections[t_id][addr])
    
    #print("Connect: %s" % (str(addr)))

    # Create IPv4 TCP socket (TODO: add support for IPv6)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Disable Nagle's algorithem, to enable faster send
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    # Connect
    sock.connect(addr)

    # Save connection
    if stored_connections.has_key(t_id):
        stored_connections[t_id][addr] = sock
        usage_connections[t_id][addr] = 1
    else:
        stored_connections[t_id] = {addr:sock}
        usage_connections[t_id] = {addr:1}

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
    global stored_connections

    t_id = getID()
    sock = stored_connections[t_id][addr]
    return sock.sendall(data)
    

def close(addr):
    global stored_connections, usage_connections

    t_id = getID()

    if (usage_connections[t_id][addr] > EXPIRATION_LIMIT):
        sock = stored_connections[t_id][addr]

        del usage_connections[t_id][addr]
        del stored_connections[t_id][addr]
        
        sock.close()
        #print("Disconnect: %s" % (str(addr)))

def closeall():
    global stored_connections, usage_connections

    t_id = getID()

    for addr in stored_connections[t_id]:
        sock = stored_connections[t_id][addr]
        sock.close()
        #print("Disconnect: %s" % (str(addr)))

    del stored_connections[t_id]
    del usage_connections[t_id]
    

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

