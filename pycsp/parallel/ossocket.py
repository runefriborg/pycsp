"""
Socket abstraction module

Allows reusing previously opened sockets.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

import time
import errno
import threading
import os, platform
import socket
import sys
from pycsp.parallel.exceptions import *
from pycsp.parallel.configuration import *
from pycsp.parallel.const import *

PLATFORM_SYSTEM = platform.system()
STDERR_OUTPUT = False

conf = Configuration()    

# Functions for retrieving LAN ip addresses
if os.name != "nt":
    import fcntl
    import struct
    
    def _get_interface_ip(ifname):
    	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    	ip = socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15])
    		)[20:24])
        s.close()
        return ip
    
def _get_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
    	interfaces = ["eth0","eth1","eth2","wlan0","wlan1","wifi0","ath0","ath1","ppp0"]
    	for ifname in interfaces:
            try:
                ip = _get_interface_ip(ifname)
                break;
            except IOError:
                pass
    return ip
    


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
            #print getThreadAndName(init=False), "connect", addr
            # Create IPv4 TCP socket (TODO: add support for IPv6)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Disable Nagle's algorithem, to enable faster send
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            # Connect to addr
            sock.connect(addr)

            connected = True
        except socket.error as e:
            if not reconnect:
                return False
            
            if STDERR_OUTPUT:
                sys.stderr.write("PyCSP socket issue (%d): %s\n" % (e.errno, e.message))
            if sock:
                sock.close()
            if e.errno != errno.ECONNREFUSED:
                raise Exception("Fatal error: Could not open socket: " + e.message)
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
            if PLATFORM_SYSTEM == 'Darwin':
                # This is an awfull hack for darwin systems. There is a flaw in
                # the module function socket.bind(addr), which may cause socket.bind(addr)
                # to block when multiple OS processes try to bind at the same time.
                time.sleep(0.1)


            # Create IPv4 TCP socket (TODO: add support for IPv6)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Disable Nagle's algorithem, to enable faster send
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            # Enable reuse of sockets in TIME_WAIT state.  
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to address
            sock.bind(server_addr)

            # Initiate listening for connections. Create queue of 5 for unaccepted connections
            sock.listen(5)

            ok = True
            
        except socket.error as e:
            if STDERR_OUTPUT:
                sys.stderr.write("PyCSP socket issue (%d): %s\n" % (e.errno, e.message))
            if sock:
                sock.close()
            if e.errno != errno.EADDRINUSE:       
                raise Exception("Fatal error: Could not bind to socket: " + e.message)
        if not ok:
            if t1 == None:
                t1 = time.time()
            else:
                if (time.time()-t1) > conf.get(SOCKETS_BIND_TIMEOUT):
                    raise SocketBindException(server_addr)
            time.sleep(conf.get(SOCKETS_BIND_RETRY_DELAY))

    # Obtain binded addresses
    address = sock.getsockname()

    # If bounded address equals '0.0.0.0', then lookup the best candidate for a public IP.
    if address[0] == '0.0.0.0':
        address = (_get_ip(), address[1])

    return sock, address

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

def sendallNOcache(sock, data):
    """
    Send all data on socket. Do not reconnect on error.
    """
    try:
        sock.sendall(data)
    except socket.error as e:
        if STDERR_OUTPUT:
            sys.stderr.write("PyCSP socket issue (%d): %s\n" % (e.errno, e.message))
            # TODO make exceptions depending on the error value

        raise SocketSendException()

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
    except socket.error as e:
        if STDERR_OUTPUT:
            sys.stderr.write("PyCSP socket issue (%d): %s\n" % (e.errno, e.message))
        raise SocketClosedException()
        
    return "".join(msg_chunks)


class ConnHandler(object):
    """
    Connection handler. This exists to be able to use the same socket from multiple threads, thus reducing the amount of sockets necessary.
    
    The connection handler is thread safe for sending.
    """
    def __init__(self):
        self.cacheSockets = {}
        self.lock = threading.Lock()

    def send(self, addr, header, payload_bin_data=None):

        sock = None
        self.lock.acquire()
        try:
            # Connect or fetch connected socket
            sock = self._connect(addr)

            # Send header
            sock = self._sendall(sock, header)

            if not payload_bin_data == None:
                # Send payload right after header
                self._sendallNOreconnect(sock, payload_bin_data)
                
        finally:
            self.lock.release()

        return sock

    def updateCache(self, addr, sock):
        
        self.lock.acquire()
        try:
            if ENABLE_CACHE:
                if not addr in self.cacheSockets:
                    self.cacheSockets[addr] = sock
        finally:
            self.lock.release()

    def _connect(self, addr, reconnect=True):
        """
        Retrieve old connection or acquire new connection

        If reconnect = False, connect returns False instead of socket, when unable to connect to host.
        """

        # Lookup connection
        if addr in self.cacheSockets:
            sock = self.cacheSockets[addr]
            return sock

        # Reverse locking
        self.lock.release()
        try:
        
            # Perform the connection without a lock
            sock = _connect(addr, reconnect)
        finally:
            self.lock.acquire()

        # Check whether someone already saved a connection, while we were connecting.
        if ENABLE_CACHE:
            if addr in self.cacheSockets:
                # Ok another thread got a connection before us. Thus, we close ours.
                sock.close()
                sock = self.cacheSockets[addr]
            else:
                # Save connection
                self.cacheSockets[addr] = sock

        return sock

    
    def _sendallNOreconnect(self, sock, data):
        """
        Send all data on socket. Do not reconnect on error.
        """
        try:
            sock.sendall(data)
        except socket.error as e:
            if STDERR_OUTPUT:
                sys.stderr.write("PyCSP socket issue (%d): %s\n" % (e.errno, e.message))
            # TODO make exceptions depending on the error value

            # Expire socket
            addr = None
            for item in self.cacheSockets.items():
                if (item[1] == sock):
                    addr = item[0]
                    self._forceclose(addr)

            if addr == None:
                raise Exception("Fatal error: Could not find cached socket " + str(sock))

            raise SocketSendException()


    def _sendall(self, sock, data):
        """
        Send all data on socket. Reconnect once if socket fails and the socket was cached.

        Warning: Provided socket may be invalidated and replaced, thus use like this:
        sock = ossocket.sendall(sock, shipped_data)

        """
        ok = False
        new = False

        while (not ok):
            try:
                sock.sendall(data)
                ok = True
            except socket.error as e:
                if STDERR_OUTPUT:
                    sys.stderr.write("PyCSP socket issue (%d): %s\n" % (e.errno, e.message))
                # TODO make exceptions depending on the error value

                if new:
                    # The socket was new and still failed, thus no reconnection
                    raise SocketSendException()
                else:
                    # Expire socket
                    addr = None
                    for item in self.cacheSockets.items():
                        if (item[1] == sock):
                            addr = item[0]
                            self._forceclose(addr)

                    if addr == None:
                        raise Exception("Fatal error: Could not find cached socket " + str(sock))

                    # Reconnect
                    sock = self._connect(addr)
                    new = True

        # Return "possibly new" socket
        return sock


    def _forceclose(self, addr):
        """
        Close socket and remove cached socket
        """
        if addr in self.cacheSockets:
            sock = self.cacheSockets[addr]

            del self.cacheSockets[addr]

            sock.close()

    def _closeall(self):
        """
        Close all sockets owned by thread
        """
        for addr in self.cacheSockets:
            sock = self.cacheSockets[addr]
            sock.close()

        self.cacheSockets = {}


