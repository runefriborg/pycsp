"""
Socket abstraction module

Allows reusing previously opened sockets.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""
import time
import errno
import socket
import sys
import threading
from exceptions import *
from configuration import *
from pycsp.common.const import *

SOCKETS_MAX_REUSE = 100
STDERR_OUTPUT = False

conf = Configuration()

cacheSockets = threading.local()
cacheUsage = threading.local()

def _connect(addr, reconnect=True):
    """
    Make a connection with the Nagle algorithm disabled.

    Retries connecting, if the connection is refused. Aborts after a specified time.
    """
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
            if not reconnect:
                return False
            
            if STDERR_OUTPUT:
                sys.stderr.write("PyCSP socket issue (%d): %s\n" % (value, message))
            if sock:
                sock.close()
            if value != errno.ECONNREFUSED:            
                raise Exception("Fatal error: Could not open socket: " + message)
        if not connected:
            if t1 == None:
                t1 = time.time()
            else:
                if (time.time()-t1) > conf.get(SOCKETS_CONNECT_TIMEOUT):
                    raise SocketConnectException()
            time.sleep(conf.get(SOCKETS_CONNECT_RETRY_DELAY))

    return sock


def start_server(server_addr=('', 0)):
    """
    Bind to address and port with the Nagle algorithm disabled.

    Retries binding, if the address and port is in use. Aborts after a specified time.
    """
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
            if STDERR_OUTPUT:
                sys.stderr.write("PyCSP socket issue (%d): %s\n" % (value, message))
            if sock:
                sock.close()
            if value != errno.EADDRINUSE:            
                raise Exception("Fatal error: Could not bind to socket: " + message)
        if not ok:
            if t1 == None:
                t1 = time.time()
            else:
                if (time.time()-t1) > conf.get(SOCKETS_BIND_TIMEOUT):
                    raise SocketBindException()
            time.sleep(conf.get(SOCKETS_BIND_RETRY_DELAY))
    
    # Obtain binded addresses
    address = sock.getsockname()

    # Initiate listening for connections. Create queue of 5 for unaccepted connections
    sock.listen(5)

    return sock, address


def connect(addr, reconnect=True):
    """
    Retrieve old connection or acquire new connection

    If reconnect = False, connect returns False instead of socket, when unable to connect to host.
    """
    
    # Lookup connection
    if cacheSockets.__dict__.has_key(addr):
        sock = cacheSockets.__dict__[addr]
        cacheUsage.__dict__[sock] += 1
        return sock

    sock = _connect(addr, reconnect)

    # Save connection
    cacheSockets.__dict__[addr] = sock
    cacheUsage.__dict__[sock] = 1

    return sock


def recvall(sock, msg_len):
    """
    A fast string concatenation in a loop that continues until the entire msg has been received
    """
    msg_len_received = 0
    msg_chunks = []
    try:
        while msg_len_received < msg_len:
            chunk = sock.recv(msg_len - msg_len_received)
            if chunk == '':
                raise SocketClosedException()
            msg_chunks.append(chunk)
            msg_len_received += len(chunk)
    except socket.error, (value,message):
        if STDERR_OUTPUT:
            sys.stderr.write("PyCSP socket issue (%d): %s\n" % (value, message))
        raise SocketClosedException()
        
    return "".join(msg_chunks)
    
def sendallNOreconnect(sock, data):
    """
    Send all data on socket. Do not reconnect on error.
    """
    try:
        sock.sendall(data)
    except socket.error, (value,message):
        if STDERR_OUTPUT:
            sys.stderr.write("PyCSP socket issue (%d): %s\n" % (value, message))
        # TODO make exceptions depending on the error value

        # Expire socket
        addr = None
        for item in cacheSockets.__dict__.items():
            if (item[1] == sock):
                addr = item[0]
                forceclose(addr)

        if addr == None:
            raise Exception("Fatal error: Could not find cached socket " + str(sock))

        raise SocketSendException()


def sendall(sock, data):
    """
    Send all data on socket. Reconnect once if socket fails and the socket was cached.

    Warning: Provided socket may be invalidated and replaced, thus use like this:
    sock = sendall(sock, shipped_data)
    
    """
    ok = False
    
    while (not ok):
        try:
            sock.sendall(data)
            ok = True
        except socket.error, (value,message):
            if STDERR_OUTPUT:
                sys.stderr.write("PyCSP socket issue (%d): %s\n" % (value, message))
            # TODO make exceptions depending on the error value

            if cacheUsage.__dict__[sock] == 1:
                # The socket was new, thus no reconnection
                raise SocketSendException()
            else:
                # Expire socket
                addr = None
                for item in cacheSockets.__dict__.items():
                    if (item[1] == sock):
                        addr = item[0]
                        forceclose(addr)

                if addr == None:
                    raise Exception("Fatal error: Could not find cached socket " + str(sock))

                # Reconnect
                sock = connect(addr)

    # Return "possibly new" socket
    return sock

        
def close(addr):
    """
    Check thread sockets use value and close if socket is expired.
    """
    if cacheSockets.__dict__.has_key(addr):
        sock = cacheSockets.__dict__[addr]
    
        if (cacheUsage.__dict__[sock] > SOCKETS_MAX_REUSE):

            del cacheSockets.__dict__[addr]
            del cacheUsage.__dict__[sock]
        
            sock.close()

def forceclose(addr):
    """
    Close socket and remove cached socket
    """
    if cacheSockets.__dict__.has_key(addr):
        sock = cacheSockets.__dict__[addr]

        del cacheSockets.__dict__[addr]
        del cacheUsage.__dict__[sock]
        
        sock.close()
    
def closeall():
    """
    Close all sockets owned by thread
    """
    for addr in cacheSockets.__dict__:
        sock = cacheSockets.__dict__[addr]
        sock.close()

    
    cacheSockets.__dict__ = {}
    cacheUsage.__dict__ = {}

def connectNOcache(addr):
    """
    Connect to addr circumventing the cached sockets
    """
    sock = _connect(addr)
    return sock

def closeNOcache(sock):
    """
    Close socket created with connectNOcache
    """
    sock.close()