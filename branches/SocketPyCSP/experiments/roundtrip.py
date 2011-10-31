import struct
import cPickle as pickle
import threading
import socket
import select
import time

N=10000
EXPIRATION_LIMIT=1000

stored_connections = {}
usage_connections = {}


def DebugSocket(sock):
    """ Overwrite Debugsocket class """
    return sock


def compile_header(cmd, id, arg):
    """
    arg is often used as msg_size to indicate the size of the following pickle data section
    """
    return struct.pack(header_fmt, cmd, id, arg)


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
    s.listen(10)

    return DebugSocket(s), address



def connect(addr):
    global stored_connections, usage_connections

    t_id=42
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



def sendall(addr, data):
    global stored_connections

    t_id = 42
    sock = stored_connections[t_id][addr]
    return sock.sendall(data)
    

def close(addr):
    global stored_connections, usage_connections

    t_id = 42

    if (usage_connections[t_id][addr] > EXPIRATION_LIMIT):
        sock = stored_connections[t_id][addr]

        del usage_connections[t_id][addr]
        del stored_connections[t_id][addr]
        
        sock.close()
        #print("Disconnect: %s" % (str(addr)))


PING, PONG, SHUTDOWN = range(3)

# Header fields:
H_CMD, H_ID = range(2)
H_MSG_SIZE = 2
H_ARG = 2

# = : Native byte-order, standard size
# h : short, CMD
# l : long, ID
# l : long, payload size following this header
header_fmt = "=hll"
header_size = struct.calcsize(header_fmt)


def server():
    global server_address

    server_socket, server_address = start_server()

    active_socket_list = [server_socket]
    finished = False
    cnt = 0

    while (not finished):

        ready, _, exceptready = select.select(active_socket_list, [], [])
        for s in ready:
            if s == server_socket:
                conn, _ = server_socket.accept()
                active_socket_list.append(conn)
            else:

                recv_data = s.recv(header_size)
                if not recv_data:
                    # connection disconnected
                    active_socket_list.remove(s)
                    s.close()
                else:
                    
                    cnt += 1
                    header = struct.unpack(header_fmt, recv_data)

                    if header[H_CMD] == SHUTDOWN:
                        finished = True
                    
                    elif header[H_CMD] == PING:

                        payload = pickle.dumps("Hello World"+str(cnt), pickle.HIGHEST_PROTOCOL)
                        s.sendall(compile_header(PONG, 42, len(payload)))
                        s.sendall(payload)

                        
    # Close server and spawned sockets
    for s in active_socket_list:
        s.close()
    server_socket.close()

def client():
    global N, server_address

    for i in xrange(N):
        
        s = connect(server_address)
        s.sendall(compile_header(PING, 42, 0))        
        recv_data = s.recv(header_size)
        header = struct.unpack(header_fmt, recv_data)
        if header[H_CMD] == PONG:
            payload = pickle.loads(s.recv(header[H_MSG_SIZE]))
            #print payload
        else:
            raise Exception("ERROR!")
        close(server_address)
        
    print 'OK'
    sendall(server_address, compile_header(SHUTDOWN, 42, 0))
    


server_thread = threading.Thread(target=server, args=())
server_thread.start()

time.sleep(2)
client_thread = threading.Thread(target=client, args=())

t1 = time.time()
client_thread.start()
client_thread.join()
t2 = time.time()

print("Time: %f us") % (((t2-t1)/N)*1000000)
