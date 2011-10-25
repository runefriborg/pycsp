
import socket
import osprocess


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
        #print("Send(after): %s" % (str(self.sock.getsockname())))
        return res

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

    t_id = osprocess.getProcName()

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


EXPIRATION_LIMIT = 10

def sendall(addr, data):
    global stored_connections

    t_id = osprocess.getProcName()
    sock = stored_connections[t_id][addr]
    return sock.sendall(data)
    

def close(addr):
    global stored_connections, usage_connections

    t_id = osprocess.getProcName()

    if (usage_connections[t_id][addr] > EXPIRATION_LIMIT):
        sock = stored_connections[t_id][addr]

        del usage_connections[t_id][addr]
        del stored_connections[t_id][addr]
        
        sock.close()
        #print("Disconnect: %s" % (str(addr)))

def closeall():
    global stored_connections, usage_connections

    t_id = osprocess.getProcName()

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

