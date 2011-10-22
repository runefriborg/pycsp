
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
        pass
        #addr = self.sock.getsockname()
        #res = self.sock.close()
        #print("Disconnect: %s" % (str(addr)))
        #return res
    

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


stored_connections = {}

def connect(addr):
    #print("Connect: %s" % (str(addr)))
    global stored_connections

    t_id = osprocess.getProcName()

    # Lookup connection
    if stored_connections.has_key(t_id):
        if stored_connections[t_id].has_key(addr):
            #print "REUSE of socket"
            return DebugSocket(stored_connections[t_id][addr])
    

    # Create IPv4 TCP socket (TODO: add support for IPv6)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Disable Nagle's algorithem, to enable faster send
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    # Connect
    sock.connect(addr)

    # Save connection
    if stored_connections.has_key(t_id):
        stored_connections[t_id][addr] = sock
    else:
        stored_connections[t_id] = {addr:sock}

    return DebugSocket(sock)


def close(sock):
    pass
