"""
Socket abstraction module

Allows reusing previously opened sockets.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

import time
import errno
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
            

            # Create IPv4 TCP socket (TODO: add support for IPv6)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Disable Nagle's algorithem, to enable faster send
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            # Connect to addr
            print('ossocket connect ' + str(addr))
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
    Dummified, to prevent a security bug, disabling listening on port.
    """
    return None, ("NONE",-1)

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
        
    return b"".join(msg_chunks)


class ConnHandler(object):
    def __init__(self):
        self.cacheSockets = {}

    def updateCache(self, addr, sock):
        if ENABLE_CACHE:
            if not addr in self.cacheSockets:
                self.cacheSockets[addr] = sock

    def connect(self, addr, reconnect=True):
        """
        Retrieve old connection or acquire new connection

        If reconnect = False, connect returns False instead of socket, when unable to connect to host.
        """

        # Lookup connection
        if addr in self.cacheSockets:
            sock = self.cacheSockets[addr]
            return sock

        sock = _connect(addr, reconnect)

        # Save connection
        if ENABLE_CACHE:
            self.cacheSockets[addr] = sock

        return sock

    
    def sendallNOreconnect(self, sock, data):
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
            for item in list(self.cacheSockets.items()):
                if (item[1] == sock):
                    addr = item[0]
                    self.forceclose(addr)

            if addr == None:
                raise Exception("Fatal error: Could not find cached socket " + str(sock))

            raise SocketSendException()




    def sendall(self, sock, data):
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
                    for item in list(self.cacheSockets.items()):
                        if (item[1] == sock):
                            addr = item[0]
                            self.forceclose(addr)

                    if addr == None:
                        raise Exception("Fatal error: Could not find cached socket " + str(sock))

                    # Reconnect
                    sock = self.connect(addr)
                    new = True

        # Return "possibly new" socket
        return sock


    def close(self, addr):
        """
        Do not close socket. As they kept for later reuse
        """
        pass

    
    def forceclose(self, addr):
        """
        Close socket and remove cached socket
        """
        if addr in self.cacheSockets:
            sock = self.cacheSockets[addr]

            del self.cacheSockets[addr]

            sock.close()

    def closeall(self):
        """
        Close all sockets owned by thread
        """
        for addr in self.cacheSockets:
            sock = self.cacheSockets[addr]
            sock.close()

        self.cacheSockets = {}


