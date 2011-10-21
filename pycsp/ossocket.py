
import socket


class DebugSocket():
    def __init__(self, sock):
        self.sock = sock

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
        addr = self.sock.getsockname()
        res = self.sock.close()
        #print("Disconnect: %s" % (str(addr)))
        return res
    


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
    print("Connect: %s" % (str(addr)))

    # Create IPv4 TCP socket (TODO: add support for IPv6)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Disable Nagle's algorithem, to enable faster send
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    # Connect
    sock.connect(addr)

    return DebugSocket(sock)


